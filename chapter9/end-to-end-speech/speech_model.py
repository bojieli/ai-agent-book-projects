"""
可插拔的语音模型接口：端到端（end-to-end）与级联（cascaded）两种范式。

对应《深入理解 AI Agent》实验 9-4「使用 Step-Audio R1 实现端到端语音思考」。

- 端到端（EndToEndSpeechModel）：单一模型直接「听 → 想 → 说」，音频进、音频出，
  中间没有暴露给外部的纯文本推理阶段。Step-Audio R1 是书中的代表模型（音频编码器
  + 音频适配器 + Qwen2.5 32B 解码器，需多卡 GPU，无公开 endpoint）。为了让读者不
  依赖自建 GPU 集群也能真实跑通「端到端语音思考」这一范式，本 demo 默认改用 OpenAI
  的 speech-to-speech 模型 `gpt-audio`：它同样是「音频 → 单模型 → 音频」，一次调用
  就同时返回语音答案与其文字转写，不经过独立的 ASR/LLM/TTS 三段。若你已经自行部署
  了真正的 Step-Audio R1，把服务地址写入 STEP_AUDIO_ENDPOINT 即可切换到它。

- 级联（CascadedSpeechModel）：把 ASR → LLM → TTS 三个独立模型串成流水线，
  一棒接一棒。可用 OpenAI 的 whisper-1 / gpt-5.6-luna / tts-1 真实跑通完整闭环。
  代价：模型间以离散文本接口相连，说话人的情绪、语气、语调等副语言信息在交接时
  几乎损失殆尽（见 chapter9.md 范式二 · 端到端全模态模型）。这一路在 demo 中作为
  与端到端对照的**基线**。
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class StageResult:
    """流水线中单个阶段的结果与延迟。"""

    name: str          # 阶段名（如 "ASR 语音识别"）
    model: str         # 使用的模型
    latency_s: float   # 该阶段耗时（秒）
    text: Optional[str] = None       # 文本产物（ASR 转写 / LLM 回答 / 端到端转写）
    audio_path: Optional[str] = None # 音频产物（TTS 合成 / 端到端语音答案）


@dataclass
class PipelineResult:
    """一次完整「语音输入 → 思考 → 语音输出」的结果。"""

    paradigm: str                 # "cascaded" 或 "end_to_end"
    input_audio: str              # 输入音频路径
    output_audio: Optional[str]   # 输出音频路径
    stages: list[StageResult] = field(default_factory=list)

    @property
    def total_latency_s(self) -> float:
        return sum(s.latency_s for s in self.stages)


# ---------------------------------------------------------------------------
# 端到端范式（可运行：默认 gpt-audio；可切换到自部署的 Step-Audio R1）
# ---------------------------------------------------------------------------
class EndToEndSpeechModel:
    """端到端语音思考模型：音频进 → 单模型「听→想→说」→ 音频出。

    两种后端，二选一：

    1. **gpt-audio（默认，OpenAI）**：真正的 speech-to-speech 模型，通过 Chat
       Completions 调用（modalities=["text","audio"]，audio={voice,format}，
       user 消息里放一个 input_audio 内容块）。一次调用即返回语音答案 + 其转写，
       中间没有独立的 ASR/LLM/TTS 阶段——这正是端到端范式的形态。模型名可用
       环境变量 E2E_MODEL 覆盖（默认 gpt-audio）。

    2. **Step-Audio R1（可选，自部署）**：书中的端到端语音思考模型，由音频编码器 +
       音频适配器 + Qwen2.5 32B 解码器组成，需多卡 GPU，无公开 endpoint。它通过
       MGRD（模态锚定思考蒸馏）真正基于声学特征思考，并通过 MPS 双脑架构实现
       「边想边说」。若配置了 STEP_AUDIO_ENDPOINT，本类改为向该地址上传音频、取回
       音频（请求体因部署方案而异，见 run() 中的骨架，接入时按需改写）。
    """

    def __init__(
        self,
        client: OpenAI,
        model: Optional[str] = None,
        voice: str = "alloy",
        system_prompt: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        self.client = client
        self.model = model or os.getenv("E2E_MODEL", "gpt-audio")
        self.voice = voice
        # 优先用显式传入的 endpoint（CLI --step-audio-endpoint），否则回落到环境变量
        self.endpoint = (endpoint if endpoint is not None
                         else os.getenv("STEP_AUDIO_ENDPOINT", "")).strip()
        self.system_prompt = system_prompt or (
            "你是一个中文语音助手。请先在内部完成必要的推理，再用简洁、口语化、"
            "适合朗读的中文说出结论，控制在三句话以内。"
        )

    @property
    def backend(self) -> str:
        """当前生效的端到端后端标识。"""
        return "step-audio-r1" if self.endpoint else "gpt-audio"

    # -- 后端一：自部署 Step-Audio R1（可选） --------------------------------
    def _run_step_audio(self, input_audio: str, output_audio: str) -> PipelineResult:
        # 不同部署方案（vLLM / 自定义 HTTP 服务）的请求体各异，此处给出最常见的
        # 「上传音频、取回音频」形态，供接入真实 Step-Audio R1 时改写。
        import requests  # 延迟导入：仅在真正配置 endpoint 时才需要该依赖

        t0 = time.perf_counter()
        with open(input_audio, "rb") as f:
            resp = requests.post(self.endpoint, files={"audio": f}, timeout=120)
        resp.raise_for_status()
        with open(output_audio, "wb") as out:
            out.write(resp.content)
        latency = time.perf_counter() - t0

        stage = StageResult(
            name="端到端（听→想→说，单模型融合）",
            model="Step-Audio R1",
            latency_s=latency,
            audio_path=output_audio,
        )
        return PipelineResult(
            paradigm="end_to_end",
            input_audio=input_audio,
            output_audio=output_audio,
            stages=[stage],
        )

    # -- 后端二：gpt-audio speech-to-speech（默认） --------------------------
    def _run_gpt_audio(self, input_audio: str, output_audio: str) -> PipelineResult:
        in_fmt = "mp3" if input_audio.lower().endswith(".mp3") else "wav"
        out_fmt = "wav" if output_audio.lower().endswith(".wav") else "mp3"
        with open(input_audio, "rb") as f:
            in_b64 = base64.b64encode(f.read()).decode()

        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=self.model,
            modalities=["text", "audio"],
            audio={"voice": self.voice, "format": out_fmt},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": in_b64, "format": in_fmt},
                        }
                    ],
                },
            ],
        )
        latency = time.perf_counter() - t0

        audio = resp.choices[0].message.audio
        if audio is None or not audio.data:
            raise RuntimeError(
                f"端到端模型 {self.model} 未返回音频。请确认该 Key 有权访问 gpt-audio，"
                "或用 E2E_MODEL 指定可用的 speech-to-speech 模型。"
            )
        with open(output_audio, "wb") as out:
            out.write(base64.b64decode(audio.data))

        # 端到端只有「一段」：听→想→说融合在单次前向中。transcript 是模型顺带
        # 吐出的语音文字稿，并非一个独立的、可供 TTS 消费的中间文本阶段。
        stage = StageResult(
            name="端到端（听→想→说，单模型一次调用）",
            model=self.model,
            latency_s=latency,
            text=audio.transcript,
            audio_path=output_audio,
        )
        return PipelineResult(
            paradigm="end_to_end",
            input_audio=input_audio,
            output_audio=output_audio,
            stages=[stage],
        )

    def run(self, input_audio: str, output_audio: str) -> PipelineResult:
        if self.endpoint:
            return self._run_step_audio(input_audio, output_audio)
        return self._run_gpt_audio(input_audio, output_audio)


# ---------------------------------------------------------------------------
# 级联范式（对照基线）
# ---------------------------------------------------------------------------
class CascadedSpeechModel:
    """级联语音流水线：ASR → LLM → TTS，三个独立模型串联。

    默认使用 OpenAI：
      - ASR：whisper-1        （语音 → 文本）
      - LLM：gpt-5.6-luna     （文本思考 → 文本回答）
      - TTS：tts-1            （文本 → 语音）

    ASR/TTS 只有 OpenAI 直连才有对应端点（OpenRouter 无音频端点），因此固定用 `client`
    （必须是直连 OpenAI）；中间的纯文本 LLM 思考可用单独的 `llm_client` 走 OpenRouter，
    从而绕开 gpt-5.6* 直连所需的组织实名认证。`llm_client` 缺省时回落到 `client`。
    """

    def __init__(
        self,
        client: OpenAI,
        asr_model: str = "whisper-1",
        llm_model: str = "gpt-5.6-luna",
        tts_model: str = "tts-1",
        tts_voice: str = "alloy",
        system_prompt: Optional[str] = None,
        llm_client: Optional[OpenAI] = None,
    ) -> None:
        self.client = client
        self.llm_client = llm_client or client
        self.asr_model = asr_model
        self.llm_model = llm_model
        self.tts_model = tts_model
        self.tts_voice = tts_voice
        self.system_prompt = system_prompt or (
            "你是一个语音助手。请先进行必要的推理，再给出简洁、口语化、"
            "适合朗读的中文回答。回答控制在三句话以内。"
        )

    # -- 阶段 1：ASR 语音识别 ------------------------------------------------
    def transcribe(self, audio_path: str) -> StageResult:
        t0 = time.perf_counter()
        with open(audio_path, "rb") as f:
            resp = self.client.audio.transcriptions.create(
                model=self.asr_model,
                file=f,
            )
        latency = time.perf_counter() - t0
        return StageResult(
            name="ASR 语音识别",
            model=self.asr_model,
            latency_s=latency,
            text=resp.text.strip(),
        )

    # -- 阶段 2：LLM 思考 ----------------------------------------------------
    def think(self, question_text: str) -> StageResult:
        t0 = time.perf_counter()
        kwargs = dict(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question_text},
            ],
            temperature=0.3,
        )
        try:
            resp = self.llm_client.chat.completions.create(**kwargs)
        except Exception as e:
            # 推理模型（如 gpt-5.x）只接受默认 temperature，会拒绝自定义值；
            # 移除该参数重试一次（同 book-translation / voice-werewolf 的做法）。
            if "temperature" not in str(e).lower():
                raise
            kwargs.pop("temperature", None)
            resp = self.llm_client.chat.completions.create(**kwargs)
        latency = time.perf_counter() - t0
        return StageResult(
            name="LLM 思考",
            model=self.llm_model,
            latency_s=latency,
            # content 可能为 None（如被截断/拒答）；用空串兜底，避免 .strip() 崩溃。
            text=(resp.choices[0].message.content or "").strip(),
        )

    # -- 阶段 3：TTS 语音合成 ------------------------------------------------
    def synthesize(self, text: str, output_audio: str) -> StageResult:
        t0 = time.perf_counter()
        resp = self.client.audio.speech.create(
            model=self.tts_model,
            voice=self.tts_voice,
            input=text,
        )
        resp.stream_to_file(output_audio)
        latency = time.perf_counter() - t0
        return StageResult(
            name="TTS 语音合成",
            model=self.tts_model,
            latency_s=latency,
            audio_path=output_audio,
        )

    # -- 完整流水线 ----------------------------------------------------------
    def run(self, input_audio: str, output_audio: str) -> PipelineResult:
        asr = self.transcribe(input_audio)
        llm = self.think(asr.text)
        tts = self.synthesize(llm.text, output_audio)
        return PipelineResult(
            paradigm="cascaded",
            input_audio=input_audio,
            output_audio=output_audio,
            stages=[asr, llm, tts],
        )


def synthesize_question_audio(
    client: OpenAI,
    question_text: str,
    output_audio: str,
    tts_model: str = "tts-1",
    voice: str = "shimmer",
) -> None:
    """用 TTS 先合成一段「用户提问」的语音，作为两条管道共同的输入。"""
    resp = client.audio.speech.create(model=tts_model, voice=voice, input=question_text)
    resp.stream_to_file(output_audio)
