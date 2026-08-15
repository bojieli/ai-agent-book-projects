"""实验 6-5：全自动 TTS 质量评估流水线 —— 一条命令跑通。

    python demo.py                      # 默认 4 个 OpenAI 配置 x 4 条语料
    python demo.py --providers openai,minimax   # 跨服务商横向对比
    python demo.py --text '一段话'       # 自定义文本
    python demo.py --gemini             # 评审改用多模态模型直接听两段音频
    python demo.py --quick              # 只用前 2 条语料，快速冒烟
    python demo.py --list-providers     # 离线：查看 provider 及配置状态
    python demo.py --dump-rubric        # 离线：查看 Rubric 维度定义

流程：多 provider TTS 合成 -> ffprobe 时长 -> Whisper 回译 -> CER/字准确率
      -> LLM/多模态音频 Rubric 打分 -> 打印逐条明细 + 配置对比汇总表。
幂等：音频写入 output/ 并复用（除非 --fresh）。完整参数见 `python demo.py --help`。
"""

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import config
import pipeline

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
DEFAULT_REFERENCE_AUDIO = str(
    Path(__file__).resolve().parents[2]
    / "chapter9"
    / "controllable-tts"
    / "reference_audio"
    / "neutral_normal_formal.mp3"
)


def load_env():
    """极简 .env 加载（不引第三方依赖）。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def audio_path(cfg_name: str, sample_id: str) -> str:
    return os.path.join(OUT_DIR, f"{cfg_name}__{sample_id}.mp3")


def evaluate_one(
    cfg,
    sample,
    use_gemini: bool,
    fresh: bool,
    judge_model: str = None,
    reference_audio: str = "",
    with_asr: bool = False,
) -> dict:
    """对单个 (配置, 语料) 跑完整链路。任一步失败返回 error 记录，不抛出。"""
    rec = {"config": cfg.name, "sample": sample.id, "challenge": sample.challenge,
           "provider": getattr(cfg, "provider", "openai"), "ok": False, "error": None}
    path = audio_path(cfg.name, sample.id)
    stage = "synthesis"
    try:
        # 1) 合成（幂等：已存在且非 fresh 则复用）
        if fresh or not os.path.exists(path) or os.path.getsize(path) == 0:
            pipeline.synthesize(cfg, sample.text, path)
        # Preserve successful synthesis evidence even if a later ASR/judge
        # stage fails.  This keeps provider progress auditable without
        # incorrectly marking the end-to-end cell complete.
        rec.update({
            "audio_path": os.path.relpath(path, OUT_DIR),
            "audio_sha256": pipeline.sha256_file(path),
            "audio_bytes": os.path.getsize(path),
        })
        # 2) 时长
        stage = "duration_probe"
        dur = pipeline.probe_duration(path)
        # 3) Optional objective ASR. Direct-audio Gemini judging does not
        # require OpenAI/Whisper and therefore keeps Fish-only runs possible.
        stage = "optional_asr"
        hyp = pipeline.transcribe(path) if (with_asr or not use_gemini) else None
        er = pipeline.char_error_rate(sample.text, hyp) if hyp is not None else None
        # 4) Rubric: manuscript acceptance requires direct audio plus a real
        # reference clip, not a transcript-only inference.
        stage = "multimodal_judge" if use_gemini else "text_judge"
        if use_gemini:
            rub = pipeline.judge_gemini_audio(
                sample.text, sample.emotion, path, reference_audio
            )
        else:
            rub = pipeline.judge_rubric(
                sample.text, sample.emotion, hyp or "", dur, er.cer if er else 0.0,
                model=judge_model,
            )
        rec.update({
            "ok": True,
            "duration": dur,
            "hypothesis": hyp,
            "cer": er.cer if er else None,
            "asr_accuracy": er.accuracy if er else None,
            "speed": (len(pipeline.normalize(sample.text)) / dur) if dur else 0.0,
            "scores": rub.scores, "reasons": rub.reasons,
            "judge_model": rub.judge_model,
            "evidence_mode": rub.evidence_mode,
            "judge_provider_attempts": rub.provider_attempts,
        })
    except Exception as e:  # 单条失败不影响整表
        rec["failed_stage"] = stage
        rec["error"] = f"{type(e).__name__}: {e}"
        attempts = getattr(e, "provider_attempts", None)
        if attempts:
            rec["judge_provider_attempts"] = attempts
    return rec


def fmt(x, nd=2):
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) else str(x)


def print_detail(rec, sample_text):
    head = f"[{rec['config']} | {rec['sample']}] {rec['challenge']}"
    if not rec["ok"]:
        print(f"  {head}\n    !! 失败: {rec['error']}")
        return
    print(f"  {head}")
    print(f"    原文  : {sample_text}")
    if rec.get("hypothesis") is not None:
        print(f"    回译  : {rec['hypothesis']}")
    objective = ""
    if rec.get("cer") is not None:
        objective = (
            f"   CER: {fmt(rec['cer'],3)}"
            f"   ASR字准确率: {fmt(rec['asr_accuracy']*100,1)}%"
        )
    print(f"    时长  : {fmt(rec['duration'])}s   语速: {fmt(rec['speed'])} 字/秒{objective}")
    s, r = rec["scores"], rec["reasons"]
    for dim in pipeline.RUBRIC_DIMENSIONS:
        print(f"    {dim:<4}: {s.get(dim,'-')}/5  {r.get(dim,'')}")


def summarize(records):
    """按配置聚合：平均 CER、平均字准确率、各 Rubric 维度均分、成功数。"""
    by_cfg = {}
    for rec in records:
        by_cfg.setdefault(rec["config"], []).append(rec)
    rows = []
    for cfg_name, recs in by_cfg.items():
        ok = [r for r in recs if r["ok"]]
        row = {"config": cfg_name, "n_ok": len(ok), "n": len(recs)}
        if ok:
            objective = [r for r in ok if r.get("cer") is not None]
            row["cer"] = mean(r["cer"] for r in objective) if objective else None
            row["asr_accuracy"] = (
                mean(r["asr_accuracy"] for r in objective) if objective else None
            )
            for dim in pipeline.RUBRIC_DIMENSIONS:
                row[dim] = mean(r["scores"].get(dim, 0) for r in ok)
        rows.append(row)
    # 按整体分降序、CER 升序排序
    rows.sort(
        key=lambda x: (
            -mean(x.get(dim, 0) for dim in pipeline.RUBRIC_DIMENSIONS),
            x.get("cer") if x.get("cer") is not None else 1,
        )
    )
    return rows


def print_table(rows):
    cols = list(pipeline.RUBRIC_DIMENSIONS)
    header = (f"{'配置':<22}{'成功':>6}{'ASR准确率':>11}{'CER':>8}"
              + "".join(f"{c:>9}" for c in cols))
    print(header)
    print("-" * 74)
    for r in rows:
        ok_str = f"{r['n_ok']}/{r['n']}"
        if not r.get("n_ok"):
            print(f"{r['config']:<22}{ok_str:>6}   (全部失败)")
            continue
        acc = f"{r['asr_accuracy']*100:.1f}%" if r.get("asr_accuracy") is not None else "n/a"
        cer = f"{r['cer']:.3f}" if r.get("cer") is not None else "n/a"
        line = f"{r['config']:<22}{ok_str:>6}{acc:>11}{cer:>8}"
        line += "".join(f"{r.get(c,0):>9.2f}" for c in cols)
        print(line)


def print_providers():
    """离线打印所有可用 TTS provider 及其配置状态（无需任何 API key）。"""
    print("可用 TTS provider（书中：OpenAI / ElevenLabs / Fish Audio / Minimax / 豆包）：\n")
    for key, p in config.PROVIDERS.items():
        state = "已配置" if p.configured() else "未配置"
        env = " + ".join(p.env)
        print(f"  [{key}]  {p.label}   ({state}；需 {env})")
        print(f"      {p.note}")
    print("\n用 --providers openai,minimax 选择跨服务商横向对比（默认仅 OpenAI）。")
    print("非 OpenAI provider 需各自的 key（见 env.example）；缺 key 时该行记为失败，不中断整表。")


def print_rubric():
    """离线打印 Rubric 维度定义（无需任何 API key）。"""
    print("TTS 质量评估 Rubric（1-5 分，5 最好）：\n")
    for dim in pipeline.RUBRIC_DIMENSIONS:
        print(f"  {dim}：{pipeline.RUBRIC_DESCRIPTIONS.get(dim, '')}")
    print("\n默认（Whisper 回译 + LLM）评审基于「转写文本 + 时长 + 语速 + CER」保守打分；")
    print("--gemini 同时提供合成音频与参考语音，覆盖正文全部四个维度。")


def main():
    global OUT_DIR
    ap = argparse.ArgumentParser(
        description="全自动 TTS 质量评估流水线（实验 6-5）：多 provider 合成 + 多模态 LLM Rubric 评审",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python demo.py                          默认 4 个 OpenAI 配置 × 4 条语料\n"
               "  python demo.py --providers openai,minimax   跨服务商横向对比\n"
               "  python demo.py --text '今天天气不错' --gemini   自定义文本 + Gemini 多模态评审\n"
               "  python demo.py --list-providers         离线查看 provider 及配置状态\n"
               "  python demo.py --dump-rubric            离线查看 Rubric 维度定义",
    )
    ap.add_argument("--text", metavar="文本",
                    help="用一段自定义文本替换测试语料库（只评这一句）")
    ap.add_argument("--providers", metavar="列表",
                    help="逗号分隔的 provider（openai,elevenlabs,fishaudio,minimax,doubao），"
                         "每个取代表性配置做横向对比；默认仅 OpenAI 的多配置")
    ap.add_argument("--judge-model", metavar="模型", dest="judge_model",
                    help=f"覆盖 LLM 评审模型（默认 {config.JUDGE_MODEL}）；--gemini 时不生效")
    ap.add_argument("--output", metavar="目录",
                    help=f"输出目录（音频 + results.json），默认 {OUT_DIR}")
    ap.add_argument("--extra", action="store_true", help="额外加入 gpt-4o-mini-tts 配置")
    ap.add_argument(
        "--gemini",
        action="store_true",
        help="用 Gemini/OpenRouter/Voxtral 多模态路线直接听两段音频评审",
    )
    ap.add_argument(
        "--reference-audio",
        default=DEFAULT_REFERENCE_AUDIO,
        help="Gemini 音色一致性对照的真实参考语音（默认复用第 9 章固定证据）",
    )
    ap.add_argument(
        "--with-asr",
        action="store_true",
        help="Gemini 直听之外再运行 Whisper/CER；需要可用 OPENAI_API_KEY",
    )
    ap.add_argument("--quick", action="store_true", help="只用前 2 条语料快速冒烟")
    ap.add_argument("--limit", type=int, default=0, help="只用前 N 条语料（0 = 全部）")
    ap.add_argument("--fresh", action="store_true", help="忽略已有音频，全部重新合成")
    ap.add_argument("--list-providers", action="store_true", dest="list_providers",
                    help="离线打印所有 TTS provider 及配置状态后退出（无需 key）")
    ap.add_argument("--dump-rubric", action="store_true", dest="dump_rubric",
                    help="离线打印 Rubric 维度定义后退出（无需 key）")
    args = ap.parse_args()

    load_env()

    # 离线路径：不联网、不需要任何 key，打印后直接退出。
    if args.list_providers:
        print_providers()
        return
    if args.dump_rubric:
        print_rubric()
        return

    if args.output:
        OUT_DIR = os.path.abspath(args.output)
    os.makedirs(OUT_DIR, exist_ok=True)

    if not args.gemini and not os.environ.get("OPENAI_API_KEY", "").strip():
        print("错误：缺少 OPENAI_API_KEY（回译/默认评审需要）。请 export 或写入 .env 后重试。",
              file=sys.stderr)
        sys.exit(1)
    if (args.gemini
            and not os.environ.get("GEMINI_API_KEY", "").strip()
            and not os.environ.get("OPENROUTER_API_KEY", "").strip()
            and not os.environ.get("MISTRAL_API_KEY", "").strip()):
        print(
            "错误：--gemini 需要 GEMINI_API_KEY、OPENROUTER_API_KEY 或 MISTRAL_API_KEY。",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.gemini and not os.path.isfile(args.reference_audio):
        print(f"错误：参考语音不存在：{args.reference_audio}", file=sys.stderr)
        sys.exit(1)

    # 选择待对比的配置：--providers 优先（跨服务商），否则默认 OpenAI 多配置。
    if args.providers:
        configs = []
        for key in [p.strip() for p in args.providers.split(",") if p.strip()]:
            if key not in config.PROVIDER_CONFIGS:
                print(f"错误：未知 provider {key!r}。可用：{', '.join(config.PROVIDER_CONFIGS)}",
                      file=sys.stderr)
                sys.exit(1)
            configs.append(config.PROVIDER_CONFIGS[key])
    else:
        configs = list(config.TTS_CONFIGS)
        if args.extra:
            configs += config.EXTRA_CONFIGS

    if args.text:
        corpus = [config.Sample(id="custom", text=args.text,
                                challenge="自定义文本", emotion="中性")]
    else:
        corpus = config.CORPUS[:2] if args.quick else config.CORPUS
        if args.limit:
            if args.limit < 0:
                print("错误：--limit 不能为负数。", file=sys.stderr)
                sys.exit(1)
            corpus = corpus[:args.limit]

    judge_model = args.judge_model or config.JUDGE_MODEL
    mode = ("多模态直接音频评审" if args.gemini
            else f"Whisper 回译 + LLM Rubric（{judge_model}）")
    providers_used = sorted({getattr(c, "provider", "openai") for c in configs})
    print("=" * 72)
    print(f"实验 6-5：全自动 TTS 质量评估流水线")
    print(f"评审模式：{mode}")
    print(f"参与 provider：{', '.join(providers_used)}")
    print(f"配置数：{len(configs)}   语料数：{len(corpus)}   "
          f"共 {len(configs)*len(corpus)} 条待评估")
    print("=" * 72)

    records = []
    t0 = time.time()
    for cfg in configs:
        print(f"\n### 配置 {cfg.name}  (provider={getattr(cfg,'provider','openai')}, "
              f"model={cfg.model}, voice={cfg.voice}, speed={cfg.speed})")
        for sample in corpus:
            rec = evaluate_one(
                cfg,
                sample,
                args.gemini,
                args.fresh,
                judge_model=None if args.gemini else args.judge_model,
                reference_audio=args.reference_audio,
                with_asr=args.with_asr,
            )
            print_detail(rec, sample.text)
            records.append(rec)

    rows = summarize(records)
    print("\n" + "=" * 72)
    print("配置对比汇总（按四维宏平均分降序）")
    print("=" * 72)
    print_table(rows)

    ok = sum(1 for r in records if r["ok"])
    print(f"\n完成：{ok}/{len(records)} 条成功，耗时 {time.time()-t0:.1f}s。")

    # 落盘结构化结果，便于二次分析
    out_json = os.path.join(OUT_DIR, "results.json")
    expected = len(configs) * len(corpus)
    exact_dims = set(pipeline.RUBRIC_DIMENSIONS)
    complete_records = [
        r for r in records
        if r.get("ok")
        and r.get("evidence_mode") == "direct-audio-with-reference"
        and set(r.get("scores", {})) == exact_dims
        and all(1 <= int(v) <= 5 for v in r.get("scores", {}).values())
    ]
    reference_sha = (
        pipeline.sha256_file(args.reference_audio)
        if args.gemini and os.path.isfile(args.reference_audio)
        else None
    )
    payload = {
        "schema_version": "2.0",
        "experiment": "6-5",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command_scope": {
            "providers": providers_used,
            "configurations": [
                {
                    "name": c.name,
                    "provider": c.provider,
                    "model": c.model,
                    "voice": c.voice,
                    "speed": c.speed,
                }
                for c in configs
            ],
            "corpus_ids": [s.id for s in corpus],
            "expected_records": expected,
            "direct_audio_judge": args.gemini,
            "optional_asr_enabled": args.with_asr,
        },
        "reference_audio": {
            "path": os.path.relpath(args.reference_audio, OUT_DIR) if args.gemini else None,
            "sha256": reference_sha,
        },
        "rubric_dimensions": pipeline.RUBRIC_DIMENSIONS,
        "completion": {
            "successful_records": ok,
            "direct_audio_four_dimension_records": len(complete_records),
            "expected_records": expected,
            "all_cells_complete": len(complete_records) == expected,
            "multi_provider": len(providers_used) >= 2,
            "manuscript_core_complete": (
                len(complete_records) == expected
                and len(providers_used) >= 2
                and bool(reference_sha)
            ),
        },
        "records": records,
        "summary": rows,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"明细结果已写入 {out_json}")


if __name__ == "__main__":
    main()
