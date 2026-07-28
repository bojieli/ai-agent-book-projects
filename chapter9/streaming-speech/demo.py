#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 9-3：模拟流式语音感知（Streaming Speech Perception）

书中原实验用 Qwen2-Audio 做"分块输入模拟流式处理"，把连续音频切成小块，
每块连同此前累积的音频上下文一起送入模型，逐步产出文本，并测量每块的延迟；
用来演示"过早分块导致误识别 / 缺失上下文"与"等完整音频再识别"之间的
延迟 vs 准确率权衡。

Qwen2-Audio 当前没有可直接调用的 key/endpoint，本 demo 用 OpenAI Whisper
（whisper-1）作为**可用的 ASR 替代**来演示同一现象：Whisper 同样是"整段输入
的非流式模型"（它的编码器需要一整段音频才能开始工作），因此把音频按递增长度
切块、每块单独识别，正好复现"过早决策的代价"。

流程（在线模式）：
  1) 用 OpenAI TTS（tts-1）合成一句中文测试音频；也可用 --audio 直接给定音频文件。
  2) 用 ffmpeg 把音频按递增长度（每 --chunk-step 秒增长一次）切出"到目前为止
     收到的全部音频"，模拟流式：t=0.5s、1.0s、1.5s ...
  3) 每个前缀块调用 Whisper 得到"当前部分识别结果"，记录识别文本与单块延迟。
  4) 对比：只在结尾对整段音频识别一次的结果与延迟（整段 / batch 方案）。
  5) 打印逐块识别表 + 整段识别对照，量化"首个可用识别"与整段延迟的权衡。

两项对照：
  - 流式(chunked) vs 整段(whole-utterance)：默认单一分块粒度即可看到。
  - **不同分块粒度**之间的延迟对照：加 --compare-chunks 会在多个分块粒度（如
    0.5/1.0/2.0s）上各跑一遍流式模拟，输出一张跨粒度的延迟对照表。

离线自检（--offline）：不联网、不需 ffmpeg，用**合成识别器**（SYNTHETIC）驱动同一套
分块/计时逻辑——文本按前缀比例揭示（复现"早期截断→随音频累积收敛"），延迟按
"BASE + SLOPE×前缀秒数"合成（建模非增量编码器"前缀越长单块越慢"）。数字为合成，
仅用于验证分块/计时/对照逻辑，**不代表任何真实模型的性能**。

依赖：openai（Python SDK）、本机 ffmpeg/ffprobe（在线模式）；离线模式无外部依赖。
环境变量：OPENAI_API_KEY（在线模式，见 env.example）。
"""

import argparse
import json
import os
import random
import sys
import shutil
import subprocess
import tempfile
import time
from collections import namedtuple
from pathlib import Path

# 从同目录 .env 读取 OPENAI_API_KEY（若安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ----------------------------- 可调参数 -----------------------------

# 测试句子：含时间信息"两点半"，前半句被截断时容易识别不全 / 产生歧义，
# 后半句补充上下文后收敛。TTS 合成语速适中，整句约 5~8 秒，可切出 10+ 个块。
TEST_SENTENCE = "麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，别忘了通知大家。"

CHUNK_STEP = 0.5            # 每次增长的音频长度（秒），模拟流式分块粒度
TTS_MODEL = "tts-1"        # OpenAI 语音合成模型
TTS_VOICE = "alloy"        # 语音音色
ASR_MODEL = "whisper-1"    # OpenAI ASR 模型
ASR_LANGUAGE = "zh"        # 提示 Whisper 目标语言为中文

# --compare-chunks 未显式给粒度时的默认对照集合（秒）
DEFAULT_CHUNK_SIZES = [0.5, 1.0, 2.0]

# 离线合成识别器（SYNTHETIC）参数：延迟 = BASE + SLOPE × 前缀秒数。
# 建模"非增量编码器每块从头重编码，累积音频越长单块推理越慢"，数字纯为演示。
MOCK_LATENCY_BASE = 0.08    # 基础单块推理开销（秒）
MOCK_LATENCY_SLOPE = 0.035  # 每秒累积音频额外的重编码开销（秒/秒）
MOCK_LATENCY_JITTER = 0.01  # 合成抖动幅度（秒），用固定种子保证可复现
MOCK_SECONDS_PER_CHAR = 0.30  # 离线模式下由句子长度估算整段时长（秒/字）

AUDIO_DIR = Path(__file__).parent / "audio"   # 音频输出目录
FULL_AUDIO = AUDIO_DIR / "sentence.wav"        # 合成的整段音频

# 单块识别结果：前缀结束时刻、单块延迟、累计延迟、识别文本
Row = namedtuple("Row", ["end", "latency", "cumulative", "text"])

# ----------------------------- 工具函数 -----------------------------


def die(msg: str) -> None:
    print(f"\n[错误] {msg}", file=sys.stderr)
    sys.exit(1)


def check_prereqs(offline: bool, need_synth: bool):
    """检查前置条件：离线模式无需任何外部依赖。"""
    if offline:
        return
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            die(f"未找到 {tool}，请先安装 ffmpeg（brew install ffmpeg）。")
    if not os.getenv("OPENAI_API_KEY"):
        die("未设置 OPENAI_API_KEY。请复制 env.example 为 .env 并填入，或直接 export。"
            "（若只想验证分块/计时逻辑，可用 --offline 离线自检，不需 key。）")


def get_client():
    from openai import OpenAI
    # 自动读取 OPENAI_API_KEY；timeout + 自动重试，避免单次网络抖动整段崩溃
    return OpenAI(timeout=60.0, max_retries=3)


def synth_audio(client, sentence: str) -> None:
    """用 OpenAI TTS 合成整段测试音频，保存为 wav（便于 ffmpeg 精确切块）。"""
    AUDIO_DIR.mkdir(exist_ok=True)
    print(f"[1/4] 合成测试音频（TTS={TTS_MODEL}, voice={TTS_VOICE}）...")
    print(f"      句子：{sentence}")
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=sentence,
        response_format="wav",
    ) as resp:
        resp.stream_to_file(str(FULL_AUDIO))
    print(f"      已保存：{FULL_AUDIO}")


def audio_duration(path: Path) -> float:
    """用 ffprobe 读取音频时长（秒）。"""
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        text=True,
    )
    return float(out.strip())


def cut_prefix(src: Path, end_sec: float, dst: Path) -> None:
    """用 ffmpeg 切出 [0, end_sec] 的前缀音频，模拟"到目前为止收到的全部音频"。"""
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(src),
            "-t", f"{end_sec:.3f}",
            "-c", "copy" if src.suffix == dst.suffix else "pcm_s16le",
            str(dst),
        ],
        check=True,
    )


def build_endpoints(total: float, chunk_step: float):
    """按分块粒度生成递增前缀的结束时刻，最后一块 = 完整音频。"""
    if chunk_step <= 0:
        die("--chunk-step 必须为正数。")
    endpoints = []
    t = chunk_step
    while t < total:
        endpoints.append(round(t, 3))
        t += chunk_step
    # 浮点累加可能让 t 略小于 total（如 20 × 0.3 = 5.999999999999998），
    # 此时循环末尾已追加过 round(total, 3)，再追加一次会重复计算一次
    # 完整音频的 Whisper 转写。
    if not endpoints or endpoints[-1] != round(total, 3):
        endpoints.append(round(total, 3))
    return endpoints


# ----------------------------- 识别器 -----------------------------


class RealRecognizer:
    """在线识别器：ffmpeg 切前缀 + OpenAI Whisper 识别，测量真实单块延迟。"""

    label = "OpenAI Whisper（真实识别）"

    def __init__(self, client, full_audio: Path, asr_model: str, language: str):
        self.client = client
        self.full_audio = full_audio
        self.asr_model = asr_model
        self.language = language
        self.tmpdir = Path(tempfile.mkdtemp(prefix="stream_chunks_"))

    def _transcribe_file(self, path: Path) -> str:
        with open(path, "rb") as f:
            resp = self.client.audio.transcriptions.create(
                model=self.asr_model,
                file=f,
                language=self.language,
            )
        return resp.text.strip()

    def transcribe_prefix(self, end_sec: float, total: float, idx: int):
        """识别 [0, end_sec] 前缀，返回 (文本, 单块延迟秒)。"""
        chunk_path = self.tmpdir / f"chunk_{idx:03d}.wav"
        cut_prefix(self.full_audio, end_sec, chunk_path)
        t0 = time.perf_counter()
        text = self._transcribe_file(chunk_path)
        return text, time.perf_counter() - t0

    def transcribe_full(self, total: float):
        """整段（batch）识别一次，返回 (文本, 延迟秒)。"""
        t0 = time.perf_counter()
        text = self._transcribe_file(self.full_audio)
        return text, time.perf_counter() - t0

    def close(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class MockRecognizer:
    """离线合成识别器（SYNTHETIC，不联网 / 不需 ffmpeg）。

    - 文本：按前缀比例揭示参考句字符，复现"早期截断不完整→随音频累积收敛"；
      仅建模"截断式不完整"，不臆造某个真实模型的具体错字。
    - 延迟：latency = BASE + SLOPE × 前缀秒数（+ 固定种子的小抖动），建模非增量
      编码器"前缀越长、单块重编码越慢"。数字为合成，**不代表任何真实模型性能**。
    """

    label = "合成识别器（SYNTHETIC / 离线自检）"

    def __init__(self, sentence: str, seed: int = 42):
        self.sentence = sentence
        self._rng = random.Random(seed)

    def _reveal(self, end_sec: float, total: float) -> str:
        frac = 0.0 if total <= 0 else max(0.0, min(1.0, end_sec / total))
        n = round(frac * len(self.sentence))
        n = max(0, min(len(self.sentence), n))
        return self.sentence[:n]

    def _latency(self, end_sec: float) -> float:
        jitter = self._rng.uniform(-MOCK_LATENCY_JITTER, MOCK_LATENCY_JITTER)
        return max(0.0, MOCK_LATENCY_BASE + MOCK_LATENCY_SLOPE * end_sec + jitter)

    def transcribe_prefix(self, end_sec: float, total: float, idx: int):
        return self._reveal(end_sec, total), self._latency(end_sec)

    def transcribe_full(self, total: float):
        return self.sentence, self._latency(total)

    def close(self):
        pass


# ----------------------------- 流式模拟 -----------------------------


def simulate_stream(recognizer, total: float, chunk_step: float, verbose: bool = True):
    """在给定分块粒度上跑一遍"递增前缀流式模拟"，返回 (rows, first_usable)。

    累计延迟 = 逐块单块识别延迟之和（在线模式为真实测量，离线模式为合成值），
    反映"边到边转、每块从头重编码"的累计推理成本。
    """
    endpoints = build_endpoints(total, chunk_step)
    rows = []
    first_usable = None
    cumulative = 0.0
    for i, end in enumerate(endpoints, 1):
        text, latency = recognizer.transcribe_prefix(end, total, i)
        cumulative += latency
        if first_usable is None and text:
            first_usable = cumulative
        rows.append(Row(end, latency, cumulative, text))
        if verbose:
            print(f"  块#{i:02d}  音频前缀 {end:>4.1f}s  单块延迟 {latency:5.2f}s  "
                  f"累计 {cumulative:6.2f}s | 识别：{text or '(空)'}")
    return rows, first_usable


# ----------------------------- 输出 -----------------------------


def run_single(recognizer, total: float, chunk_step: float, sentence: str):
    """默认模式：单一分块粒度的流式模拟 + 整段对照 + 权衡小结。返回结果字典。"""
    print(f"[2/4] 流式模拟：每 {chunk_step}s 增长一次，逐块识别当前累积音频"
          f"（识别器：{recognizer.label}）")
    print("      （编码器非增量，每块都对累积音频从头识别——这正是「模拟流式」的代价）\n")
    rows, first_usable = simulate_stream(recognizer, total, chunk_step)

    print(f"\n[3/4] 对照方案：等完整音频到齐后，只识别整段一次（整段 / batch）")
    full_text, full_latency = recognizer.transcribe_full(total)
    print(f"      整段识别延迟 {full_latency:.2f}s | 识别：{full_text}")

    print(f"\n[4/4] 对照小结（延迟 vs 准确率权衡）")
    print(f"  原始句子           ：{sentence}")
    print(f"  整段识别结果       ：{full_text}")
    print(f"  整段识别需等待     ：{total:.2f}s（录完）+ {full_latency:.2f}s（推理）")
    if first_usable is not None:
        print(f"  流式首个可用识别   ：仅需约 {rows[0].end:.1f}s 音频即产出部分结果，"
              f"比整段提前 {total - rows[0].end:.1f}s 拿到第一版")
    early = rows[0].text if rows else ""
    print(f"\n  过早分块的代价：")
    print(f"    最早分块（{rows[0].end:.1f}s）识别 →  {early or '(空/不完整)'}")
    print(f"    随音频增长收敛 →              {rows[-1].text}")
    print(f"    对比整段一次识别 →            {full_text}")
    print(f"\n  结论：流式分块能极早给出'部分结果'（低首包延迟），但早期块因缺少后半句"
          f"上下文，识别可能不完整/出错（如时间、数字被截断误判）；随着音频累积逐步"
          f"收敛。整段识别最准，但必须等整句说完 + 推理，首字延迟最高。这正是流式"
          f"语音感知的延迟/准确率权衡。")

    return {
        "mode": "single",
        "recognizer": recognizer.label,
        "sentence": sentence,
        "total_seconds": round(total, 3),
        "chunk_step": chunk_step,
        "full_text": full_text,
        "full_latency": round(full_latency, 3),
        "first_usable_latency": None if first_usable is None else round(first_usable, 3),
        "chunks": [
            {"end": r.end, "latency": round(r.latency, 3),
             "cumulative": round(r.cumulative, 3), "text": r.text}
            for r in rows
        ],
    }


def run_compare_chunks(recognizer, total: float, chunk_sizes, sentence: str):
    """对照模式：在多个分块粒度上各跑一遍流式模拟，输出跨粒度延迟对照表。"""
    print(f"[对照] 不同分块粒度的延迟对照（识别器：{recognizer.label}）")
    print(f"       整段时长 {total:.2f}s；对照粒度：{', '.join(f'{c}s' for c in chunk_sizes)}\n")

    full_text, full_latency = recognizer.transcribe_full(total)

    results = []
    for cs in chunk_sizes:
        rows, first_usable = simulate_stream(recognizer, total, cs, verbose=False)
        stream_total = rows[-1].cumulative if rows else 0.0
        last_latency = rows[-1].latency if rows else 0.0
        converged = bool(rows) and rows[-1].text == sentence
        results.append({
            "chunk_step": cs,
            "num_chunks": len(rows),
            "first_usable_latency": None if first_usable is None else round(first_usable, 3),
            "last_chunk_latency": round(last_latency, 3),
            "stream_total_latency": round(stream_total, 3),
            "final_text": rows[-1].text if rows else "",
            "converged_to_full": converged,
        })

    # 表头
    print(f"  {'分块粒度':<8}{'块数':>5}{'首个部分结果':>14}{'末块单块延迟':>14}"
          f"{'流式识别总耗时':>16}{'末块=整段?':>12}")
    print("  " + "-" * 70)
    for r in results:
        fu = "—" if r["first_usable_latency"] is None else f"{r['first_usable_latency']:.2f}s"
        conv = "是" if r["converged_to_full"] else "否"
        print(f"  {str(r['chunk_step']) + 's':<8}{r['num_chunks']:>5}{fu:>14}"
              f"{r['last_chunk_latency']:>13.2f}s{r['stream_total_latency']:>15.2f}s{conv:>12}")
    print("  " + "-" * 70)
    print(f"  {'整段(batch)':<8}{'—':>5}{'—':>14}{full_latency:>13.2f}s"
          f"{'（需先等录完 ' + format(total, '.2f') + 's）':>18}")
    print(f"\n  读表：分块粒度越小，'首个部分结果'来得越早（首包延迟越低），但块数更多、"
          f"\n        '流式识别总耗时'（把每块从头重编码累加）也更高——这就是非增量编码器"
          f"\n        下'低首包'与'高累计算力'的取舍。整段(batch)方案单次推理最省算力，"
          f"\n        但必须先等整段音频录完（{total:.2f}s）才能开始，首字延迟最高。")

    return {
        "mode": "compare-chunks",
        "recognizer": recognizer.label,
        "sentence": sentence,
        "total_seconds": round(total, 3),
        "full_text": full_text,
        "full_latency": round(full_latency, 3),
        "per_chunk_size": results,
    }


# ----------------------------- 主流程 -----------------------------


def parse_chunk_sizes(spec: str):
    """解析 '0.5,1.0,2.0' 形式的分块粒度列表。"""
    if not spec:
        return list(DEFAULT_CHUNK_SIZES)
    try:
        sizes = [float(x) for x in spec.split(",") if x.strip()]
    except ValueError:
        die(f"--compare-chunks 参数无法解析为数字列表：{spec!r}")
    if not sizes or any(s <= 0 for s in sizes):
        die("--compare-chunks 的分块粒度必须都是正数。")
    return sizes


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="demo.py",
        description="实验 9-3：模拟流式语音感知。用 TTS 合成（或 --audio 指定）一句中文，"
                    "按递增前缀长度切块逐块识别，复现「早期分块因缺后文而误识别、随音频"
                    "累积收敛」的延迟 vs 准确率权衡，并与整段(batch)识别对照；可用 "
                    "--compare-chunks 在多个分块粒度间做延迟对照，或用 --offline 离线自检。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python demo.py                          # 默认：TTS 合成 + 0.5s 粒度流式识别\n"
               "  python demo.py --quick                  # 粒度放大到 1.5s，Whisper 调用约 1/3\n"
               "  python demo.py --audio my.wav           # 用现成音频文件，跳过 TTS 合成\n"
               "  python demo.py --compare-chunks         # 跨 0.5/1.0/2.0s 的延迟对照表\n"
               "  python demo.py --compare-chunks 0.3,0.8 # 自定义对照的分块粒度\n"
               "  python demo.py --offline --compare-chunks  # 离线自检（合成数字，不联网）\n"
               "  python demo.py --output result.json     # 结果另存为 JSON",
    )
    inp = p.add_argument_group("输入")
    inp.add_argument("--sentence", default=TEST_SENTENCE,
                     help="测试句子（默认为书中同类的带时间信息的句子）。")
    inp.add_argument("--audio", metavar="PATH",
                     help="使用现成音频文件作为输入（跳过 TTS 合成）；离线模式忽略此项。")

    chunk = p.add_argument_group("分块")
    chunk.add_argument("--chunk-step", type=float, default=CHUNK_STEP,
                       help=f"分块粒度（秒），越小分块越多、越慢（默认 {CHUNK_STEP}）。")
    chunk.add_argument("--quick", action="store_true",
                       help="快速模式：把分块粒度放大到 1.5s，识别调用数减到约 1/3。")
    chunk.add_argument("--compare-chunks", nargs="?", const="", metavar="S1,S2,...",
                       help="跨多个分块粒度做延迟对照并打印对照表；不带值时用默认 "
                            f"{','.join(str(c) for c in DEFAULT_CHUNK_SIZES)}（秒）。")

    model = p.add_argument_group("模型 / 语言")
    model.add_argument("--tts-model", default=TTS_MODEL,
                       help=f"OpenAI TTS 模型（默认 {TTS_MODEL}）。")
    model.add_argument("--voice", default=TTS_VOICE,
                       help=f"TTS 音色（默认 {TTS_VOICE}）。")
    model.add_argument("--asr-model", default=ASR_MODEL,
                       help=f"OpenAI ASR 模型（默认 {ASR_MODEL}）。")
    model.add_argument("--language", default=ASR_LANGUAGE,
                       help=f"ASR 目标语言提示（默认 {ASR_LANGUAGE}）。")

    misc = p.add_argument_group("运行 / 输出")
    misc.add_argument("--offline", action="store_true",
                      help="离线自检：不联网、不需 ffmpeg，用合成识别器驱动分块/计时逻辑，"
                           "数字为 SYNTHETIC，仅用于验证流程。")
    misc.add_argument("--duration", type=float, default=None, metavar="SEC",
                      help="离线模式下的整段时长（秒）；缺省时按句子长度估算。")
    misc.add_argument("--output", metavar="PATH",
                      help="把结果（逐块表 / 对照表）另存为 JSON 文件。")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # argparse 覆盖模块级默认（仅调参，不改变核心流程）
    global TTS_MODEL, TTS_VOICE, ASR_MODEL, ASR_LANGUAGE
    TTS_MODEL, TTS_VOICE = args.tts_model, args.voice
    ASR_MODEL, ASR_LANGUAGE = args.asr_model, args.language
    sentence = args.sentence
    chunk_step = 1.5 if args.quick else args.chunk_step

    check_prereqs(args.offline, need_synth=not args.audio)

    # ---- 准备识别器与整段时长 ----
    if args.offline:
        total = args.duration if args.duration else max(3.0, len(sentence) * MOCK_SECONDS_PER_CHAR)
        print("[离线自检] 使用合成识别器（SYNTHETIC）：以下文本按前缀比例揭示、延迟为合成值，")
        print("           仅用于验证分块 / 计时 / 对照逻辑，不代表任何真实模型的性能。")
        print(f"           句子：{sentence}")
        print(f"           估算整段时长：{total:.2f}s\n")
        recognizer = MockRecognizer(sentence)
    else:
        client = get_client()
        if args.audio:
            src = Path(args.audio)
            if not src.exists():
                die(f"--audio 指定的文件不存在：{src}")
            AUDIO_DIR.mkdir(exist_ok=True)
            print(f"[1/4] 使用现成音频：{src}")
        else:
            synth_audio(client, sentence)
            src = FULL_AUDIO
        total = audio_duration(src)
        print(f"      整段时长：{total:.2f} 秒\n")
        recognizer = RealRecognizer(client, src, ASR_MODEL, ASR_LANGUAGE)

    # ---- 跑对照 / 单粒度 ----
    try:
        if args.compare_chunks is not None:
            chunk_sizes = parse_chunk_sizes(args.compare_chunks)
            result = run_compare_chunks(recognizer, total, chunk_sizes, sentence)
        else:
            result = run_single(recognizer, total, chunk_step, sentence)
    finally:
        recognizer.close()

    # ---- 可选：结果落盘 ----
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[输出] 结果已写入：{args.output}")


if __name__ == "__main__":
    main()
