"""TTS 质量评估流水线的核心步骤。

一条评估链路：
  合成(OpenAI TTS) -> 时长探测(ffprobe) -> 回译(Whisper) -> 计算 CER/字准确率
      -> LLM Rubric 打分(gpt-5.6-luna) [可选: Gemini 音频评审 gemini-3.5-flash]

说明：TTS 合成与 Whisper 回译必须走 OpenAI 直连；文本 Rubric 与直接听音频的
多模态 Rubric 支持 Google Gemini、OpenRouter 与 Mistral Voxtral。每条路径都把
两段真实音频交给音频模型，不会退化成转写文本评审。

所有对外函数都做了健壮性处理：单条失败抛出带上下文的异常，由 demo.py 捕获后
在汇总表里记为失败，而不会中断整表。
"""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

import config

# ---------------------------------------------------------------------------
# 客户端（带自动重试，缓解偶发的网络抖动）。
# ---------------------------------------------------------------------------
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """OpenAI 直连 client：用于 TTS 合成与 Whisper 回译（这两项不能走 OpenRouter）。"""
    global _client
    if _client is None:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "缺少 OPENAI_API_KEY（TTS 合成 / Whisper 回译需 OpenAI 直连）。"
                "请 `export OPENAI_API_KEY=your-openai-api-key` 或写入 .env。"
            )
        _client = OpenAI(api_key=key, max_retries=5, timeout=60.0)
    return _client


# ---------------------------------------------------------------------------
# LLM Rubric 评审客户端：支持 OpenRouter 回退。
# gpt-5.x 直连 OpenAI 需组织实名认证，只要有 OPENROUTER_API_KEY 就优先走 OpenRouter。
# 注意：仅 chat 评审可回退；TTS / Whisper 仍需 OpenAI 直连（见 get_client）。
# ---------------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_judge_client: Optional[OpenAI] = None
_judge_client_kind: str = ""


def _to_openrouter_model(model: str) -> str:
    """把模型名映射成 OpenRouter id：含 '/' 视为原生 id；gpt-* -> openai/*；
    claude-* -> anthropic/claude-opus-4.8；其余回退到 openai/gpt-5.6-luna。"""
    if "/" in model:
        return model
    if model.startswith("gpt-"):
        return "openai/" + model
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"


def get_judge_client_and_model(model: str):
    """构造 LLM 评审用的 client 并返回 (client, 实际模型名)。

    回退：gpt-5.x 且有 OPENROUTER_API_KEY -> 优先 OpenRouter；否则有 OPENAI_API_KEY ->
    直连；否则有 OPENROUTER_API_KEY -> OpenRouter（模型名映射）；皆无 -> 清晰报错。
    """
    global _judge_client, _judge_client_kind
    primary = os.environ.get("OPENAI_API_KEY", "").strip()
    orkey = os.environ.get("OPENROUTER_API_KEY", "").strip()
    prefer_or = bool(orkey) and model.startswith("gpt-5")

    if not prefer_or and primary:
        if _judge_client_kind != "openai":
            _judge_client = OpenAI(api_key=primary, max_retries=5, timeout=60.0)
            _judge_client_kind = "openai"
        return _judge_client, model
    if orkey:
        if _judge_client_kind != "openrouter":
            _judge_client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=orkey,
                                   max_retries=5, timeout=60.0)
            _judge_client_kind = "openrouter"
        return _judge_client, _to_openrouter_model(model)
    if primary:
        if _judge_client_kind != "openai":
            _judge_client = OpenAI(api_key=primary, max_retries=5, timeout=60.0)
            _judge_client_kind = "openai"
        return _judge_client, model
    raise RuntimeError(
        "缺少 OPENAI_API_KEY / OPENROUTER_API_KEY，无法运行 LLM Rubric 评审。"
    )


# ---------------------------------------------------------------------------
# 1) TTS 合成（多 provider 分发）
# ---------------------------------------------------------------------------
def synthesize(cfg: config.TTSConfig, text: str, out_path: str) -> None:
    """按 cfg.provider 分发到对应服务商合成语音，写入 out_path（mp3）。失败抛异常。

    OpenAI 走官方 SDK；其余服务商按各家公开 REST 接口用内置 urllib 调用，
    不引入额外依赖。缺少对应 key 时抛出带上下文的异常，由上层记为该行失败。
    """
    fn = _SYNTH_DISPATCH.get(cfg.provider)
    if fn is None:
        raise RuntimeError(
            f"未知 provider: {cfg.provider!r}（可选：{', '.join(_SYNTH_DISPATCH)}）"
        )
    audio = fn(cfg, text)
    if not audio:
        raise RuntimeError(f"{cfg.provider} TTS 返回空音频")
    with open(out_path, "wb") as f:
        f.write(audio)


def _require_env(name: str) -> str:
    # 走 config.env_get 以支持环境变量别名（如 Fish 的 FISH_API_KEY / FISHAUDIO_API_KEY）。
    val = config.env_get(name)
    if not val:
        raise RuntimeError(f"缺少环境变量 {name}，无法用该 provider 合成。")
    return val


def _http_post(url: str, body: dict, headers: dict, timeout: float = 90.0) -> bytes:
    """POST JSON，返回原始响应字节。非 2xx 抛出带响应体片段的异常。"""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **headers}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None


def _synth_openai(cfg: config.TTSConfig, text: str) -> bytes:
    kwargs = dict(model=cfg.model, voice=cfg.voice, input=text)
    if cfg.supports_speed() and abs(cfg.speed - 1.0) > 1e-6:
        kwargs["speed"] = cfg.speed
    return get_client().audio.speech.create(**kwargs).content


def _synth_elevenlabs(cfg: config.TTSConfig, text: str) -> bytes:
    key = _require_env("ELEVENLABS_API_KEY")
    voice = cfg.voice or "21m00Tcm4TlvDq8ikWAM"
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
           f"?output_format=mp3_44100_128")
    body = {"text": text, "model_id": cfg.model or "eleven_multilingual_v2"}
    # ElevenLabs 返回原始 mp3 字节。
    return _http_post(url, body, {"xi-api-key": key, "Accept": "audio/mpeg"})


def _synth_fishaudio(cfg: config.TTSConfig, text: str) -> bytes:
    key = _require_env("FISH_API_KEY")
    if not cfg.voice:
        raise RuntimeError(
            "Fish Audio voice consistency requires a real reference_id; "
            "set FISH_REFERENCE_ID."
        )
    # Use Fish's maintained SDK instead of assuming the REST response is raw
    # MP3.  The current S1 endpoint streams MessagePack chunks and the SDK is
    # the provider-supported decoder for that wire format.
    from fish_audio_sdk import Session, TTSRequest

    request = TTSRequest(text=text, reference_id=cfg.voice, format="mp3")
    return b"".join(Session(key).tts(request, backend=cfg.model or "s1"))


# Minimax /v1/t2a_v2 uses Bearer auth and no longer takes a GroupId query
# parameter.  The global and mainland-China deployments live on separate hosts;
# pick one via MINIMAX_REGION (defaults to the global api.minimax.io host).
_MINIMAX_T2A_ENDPOINTS = {
    "global": "https://api.minimax.io/v1/t2a_v2",
    "cn": "https://api.minimaxi.com/v1/t2a_v2",
}
# Success criteria for the non-streaming t2a_v2 call: base_resp.status_code == 0
# (request accepted) and data.status == 2 (synthesis finished).
_MINIMAX_SUCCESS_CODE = 0
_MINIMAX_STATUS_DONE = 2


def _minimax_endpoint() -> str:
    """Return the t2a_v2 endpoint for MINIMAX_REGION: cn -> api.minimaxi.com,
    otherwise the global api.minimax.io host."""
    region = os.environ.get("MINIMAX_REGION", "").strip().lower()
    if region in ("cn", "cn_zh", "china", "minimaxi"):
        return _MINIMAX_T2A_ENDPOINTS["cn"]
    return _MINIMAX_T2A_ENDPOINTS["global"]


def _synth_minimax(cfg: config.TTSConfig, text: str) -> bytes:
    key = _require_env("MINIMAX_API_KEY")
    body = {
        "model": cfg.model or "speech-2.8-hd",
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": cfg.voice, "speed": cfg.speed},
        "audio_setting": {"format": "mp3", "sample_rate": 32000},
    }
    raw = _http_post(_minimax_endpoint(), body, {"Authorization": f"Bearer {key}"})
    data = json.loads(raw)
    # Validate the request-level return code first, then the synthesis status.
    base_resp = data.get("base_resp") or {}
    if base_resp.get("status_code") != _MINIMAX_SUCCESS_CODE:
        raise RuntimeError(f"Minimax t2a_v2 failed: base_resp={base_resp or data}")
    payload = data.get("data") or {}
    status = payload.get("status")
    hexstr = payload.get("audio")
    if status != _MINIMAX_STATUS_DONE or not hexstr:
        raise RuntimeError(
            f"Minimax returned no finished audio: status={status} base_resp={base_resp}"
        )
    # data.audio is a hex-encoded mp3 payload.
    return bytes.fromhex(hexstr)


def _synth_doubao(cfg: config.TTSConfig, text: str) -> bytes:
    import uuid
    appid = _require_env("DOUBAO_APP_ID")
    token = _require_env("DOUBAO_ACCESS_TOKEN")
    body = {
        "app": {"appid": appid, "token": token,
                "cluster": cfg.model or "volcano_tts"},
        "user": {"uid": "tts-quality-eval"},
        "audio": {"voice_type": cfg.voice, "encoding": "mp3",
                  "speed_ratio": cfg.speed},
        "request": {"reqid": str(uuid.uuid4()), "text": text, "operation": "query"},
    }
    # 火山引擎鉴权头是特殊的 'Bearer;{token}' 形式；音频为 base64 编码的 data 字段。
    raw = _http_post("https://openspeech.bytedance.com/api/v1/tts", body,
                     {"Authorization": f"Bearer;{token}"})
    data = json.loads(raw)
    b64 = data.get("data")
    if not b64:
        raise RuntimeError(f"豆包无音频返回：code={data.get('code')} "
                           f"message={data.get('message')}")
    return base64.b64decode(b64)


_SYNTH_DISPATCH = {
    "openai": _synth_openai,
    "elevenlabs": _synth_elevenlabs,
    "fishaudio": _synth_fishaudio,
    "minimax": _synth_minimax,
    "doubao": _synth_doubao,
}


# ---------------------------------------------------------------------------
# 2) 时长探测（ffprobe）
# ---------------------------------------------------------------------------
def probe_duration(path: str) -> float:
    """返回音频时长（秒）。ffprobe 缺失或出错时抛异常。"""
    if shutil.which("ffprobe") is None:
        raise RuntimeError("未找到 ffprobe，请安装 ffmpeg（macOS: brew install ffmpeg）。")
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe 失败: {proc.stderr.strip()}")
    out = proc.stdout.strip()
    try:
        return float(out)
    except ValueError:
        raise RuntimeError(f"ffprobe 输出无法解析为时长: {out!r}")


# ---------------------------------------------------------------------------
# 3) 回译（Whisper 转写）
# ---------------------------------------------------------------------------
# 用简体中文提示语引导 Whisper 输出简体，避免它偶尔返回繁体导致 CER 被字形差异
# 虚高（那是转写脚本选择问题，不是 TTS 发音错误）。
_ZH_PROMPT = "以下是普通话简体中文的句子。"


def transcribe(path: str) -> str:
    with open(path, "rb") as f:
        tr = get_client().audio.transcriptions.create(
            model=config.WHISPER_MODEL, file=f, language="zh", prompt=_ZH_PROMPT,
        )
    return tr.text or ""


# ---------------------------------------------------------------------------
# 4) 文本归一化 + 字错误率（中文用字级 CER，等价于书中所说 WER 的可懂度维度）
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    """去掉标点/空白，只保留 CJK / 字母 / 数字，并小写，便于逐字比较。"""
    text = text.lower()
    return "".join(ch for ch in text if ch.isalnum())


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein 距离（字符级）。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,        # 删除
                cur[j - 1] + 1,     # 插入
                prev[j - 1] + (ca != cb),  # 替换
            ))
        prev = cur
    return prev[-1]


@dataclass
class ErrorRate:
    cer: float          # 字错误率 = 编辑距离 / 参考字数
    accuracy: float     # 字准确率 = 1 - cer（下限 0）
    edits: int
    ref_len: int


def char_error_rate(reference: str, hypothesis: str) -> ErrorRate:
    ref = normalize(reference)
    hyp = normalize(hypothesis)
    if not ref:
        if not hyp:
            return ErrorRate(0.0, 1.0, 0, 0)
        dist = len(hyp)
        return ErrorRate(cer=float(dist), accuracy=0.0, edits=dist, ref_len=0)
    dist = _edit_distance(ref, hyp)
    cer = dist / len(ref)
    return ErrorRate(cer=cer, accuracy=max(0.0, 1.0 - cer), edits=dist, ref_len=len(ref))


# ---------------------------------------------------------------------------
# 5) LLM Rubric 评审（默认，OpenAI 闭环）
# ---------------------------------------------------------------------------
RUBRIC_DIMENSIONS = ["准确性", "自然度", "情感表达", "音色一致性"]

# 维度说明（供 --dump-rubric 离线打印，也是评审 prompt 的依据）。括号内标注与书中
# 四维度（准确性 / 自然度 / 情感表达 / 音色一致性）的对应关系。
RUBRIC_DESCRIPTIONS = {
    "准确性": "逐字核对原文，检查漏读、错读、添读、数字、专名与多音字。",
    "自然度": "直接听语音的流畅度、机器感、停顿、重音和韵律是否符合人类习惯。",
    "情感表达": "语调、语速和强调是否符合中性、兴奋、悲伤或疑问等目标情感。",
    "音色一致性": "把合成语音与同时提供的参考语音比较，判断说话人音色是否一致。",
}
# The text-only judge remains a diagnostic fallback.  It cannot complete the
# manuscript experiment because it cannot hear emotion or compare a speaker.

_JUDGE_SYSTEM = """你是严格的 TTS（文本转语音）质量评审专家。
你将拿到：原始参考文本、该文本的期望情感、由 Whisper 对合成语音回译得到的转写文本，
以及从音频客观测得的时长、语速（字/秒）和字错误率（CER）。
请据此对合成语音质量按 Rubric 逐维度打分（1-5 的整数，5 最好）。你无法听到音频，
所以情感表达和音色一致性必须返回 0 并明确标记无法判定；本路径仅是诊断回退，不能验收实验：

- 准确性：转写与原文是否高度一致（漏字/错字/多字越多分越低；CER 越高分越低）。
- 自然度：语速是否接近自然朗读（中文自然朗读约 4-6 字/秒；过快>7 或过慢<3 都不自然）。
- 情感表达：返回 0，理由说明文本特征不足以判断真实语调。
- 音色一致性：返回 0，理由说明没有听到参考语音和合成语音。

注意：你看不到音频本身，只能基于以上可测特征做保守、可解释的判断。
只输出 JSON，格式：
{"准确性": {"score": int, "reason": str},
 "自然度": {"score": int, "reason": str},
 "情感表达": {"score": int, "reason": str},
 "音色一致性": {"score": int, "reason": str}}
reason 用一句简短中文说明。"""


@dataclass
class RubricResult:
    scores: dict            # 维度 -> int
    reasons: dict           # 维度 -> str
    raw: str = ""
    judge_model: str = ""
    evidence_mode: str = ""
    provider_attempts: list = field(default_factory=list)


class JudgeRouteError(RuntimeError):
    """A sanitized multimodal-judge failure carrying every attempted route."""

    def __init__(self, message: str, provider_attempts: list):
        super().__init__(message)
        self.provider_attempts = provider_attempts


def judge_rubric(reference: str, emotion: str, hypothesis: str,
                 duration: float, cer: float, model: Optional[str] = None) -> RubricResult:
    """用评审模型（默认 gpt-5.6-luna）按 Rubric 打分。返回结构化分数 + 点评。

    评审 chat 调用支持 OpenRouter 回退（见 get_judge_client_and_model）。"""
    chars = len(normalize(reference))
    speed = chars / duration if duration > 0 else 0.0
    user = (
        f"原始参考文本：{reference}\n"
        f"期望情感：{emotion}\n"
        f"Whisper 回译文本：{hypothesis}\n"
        f"音频时长：{duration:.2f} 秒\n"
        f"语速：{speed:.2f} 字/秒（参考文本 {chars} 个有效字符）\n"
        f"字错误率 CER：{cer:.3f}\n"
    )
    judge_client, judge_model = get_judge_client_and_model(model or config.JUDGE_MODEL)
    resp = judge_client.chat.completions.create(
        model=judge_model,
        messages=[{"role": "system", "content": _JUDGE_SYSTEM},
                  {"role": "user", "content": user}],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    scores, reasons = {}, {}
    for dim in RUBRIC_DIMENSIONS:
        item = data.get(dim, {})
        if isinstance(item, dict):
            scores[dim] = int(item.get("score") or 0)   # score 缺失或为 null 时按 0 分
            reasons[dim] = str(item.get("reason", "")).strip()
        else:  # 兼容模型直接返回数字（null 按 0 分）
            scores[dim] = int(item or 0)
            reasons[dim] = ""
    return RubricResult(
        scores=scores,
        reasons=reasons,
        raw=raw,
        judge_model=judge_model,
        evidence_mode="transcript-metrics-only-incomplete",
    )


# ---------------------------------------------------------------------------
# 6) 可选：Gemini 多模态音频评审（书中方案）。用 REST，避免额外 SDK 依赖。
# ---------------------------------------------------------------------------
def _resolve_gemini_model(api_key: str) -> str:
    """探测当前可用的 Gemini 模型，避免默认名过期。"""
    import urllib.request
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read())
        models_list = data.get("models") or [] if isinstance(data, dict) else []
        names = [(m.get("name") or "").split("/")[-1] for m in models_list
                 if isinstance(m, dict) and "generateContent" in (m.get("supportedGenerationMethods") or [])]
        # 优先默认的 gemini-3.5-flash（已验证支持音频输入），再退到 pro / 旧 flash 系列。
        for want in (config.GEMINI_MODEL_DEFAULT, "gemini-3.5-flash",
                     "gemini-2.5-pro", "gemini-2.5-flash", "gemini-flash-latest"):
            if want in names:
                return want
        # 退而求其次：任意非 tts/image 的可用模型
        for n in names:
            if "tts" not in n and "image" not in n and "embedding" not in n:
                return n
    except Exception:
        pass
    return config.GEMINI_MODEL_DEFAULT


def _parse_direct_audio_rubric(text: str, *, judge_model: str, provider_attempts: list) -> RubricResult:
    """Validate a direct-audio judge response against the exact four dimensions."""
    parsed = json.loads(text)
    scores, reasons = {}, {}
    for dim in RUBRIC_DIMENSIONS:
        item = parsed.get(dim, {})
        scores[dim] = int(item.get("score") or 0) if isinstance(item, dict) else int(item or 0)
        reasons[dim] = str(item.get("reason", "")).strip() if isinstance(item, dict) else ""
    return RubricResult(
        scores=scores,
        reasons=reasons,
        raw=text,
        judge_model=judge_model,
        evidence_mode="direct-audio-with-reference",
        provider_attempts=provider_attempts,
    )


def _message_text(data: dict) -> str:
    """Extract text from OpenAI-compatible string or chunk-list content."""
    choices = data.get("choices") or []
    message_content = ((choices[0].get("message") or {}).get("content")) if choices else None
    if isinstance(message_content, list):
        return "".join(
            str(item.get("text", "")) for item in message_content if isinstance(item, dict)
        ).strip()
    return str(message_content or "").strip()


def _judge_mistral_audio(
    prompt: str,
    audio_b64: str,
    reference_audio_b64: str,
    *,
    provider_attempts: list,
) -> RubricResult:
    """Send both MP3s to Mistral Voxtral using its native data-URL chunks."""
    import urllib.error
    import urllib.request

    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not key:
        raise RuntimeError("缺少 MISTRAL_API_KEY，无法回退 Voxtral 音频评审。")
    model = os.environ.get("TTS_MISTRAL_AUDIO_JUDGE_MODEL", "voxtral-small-latest").strip()
    body = {
        "model": model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "text", "text": "待评估合成语音（candidate）:"},
            {
                "type": "input_audio",
                "input_audio": "data:audio/mpeg;base64," + audio_b64,
            },
            {"type": "text", "text": "参考说话人语音（reference）:"},
            {
                "type": "input_audio",
                "input_audio": "data:audio/mpeg;base64," + reference_audio_b64,
            },
        ]}],
    }
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.loads(response.read())
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:2000]
            error = f"Mistral Voxtral HTTP {exc.code}: {detail}"
            if exc.code >= 500 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            provider_attempts.append({
                "provider": "Mistral Voxtral API",
                "model": model,
                "status": "unavailable",
                "error": error,
                "attempts": attempt + 1,
            })
            raise JudgeRouteError(error, provider_attempts) from None
    text = _message_text(data)
    if not text:
        error = f"Mistral Voxtral 未返回评审文本：{data}"
        provider_attempts.append({
            "provider": "Mistral Voxtral API",
            "model": model,
            "status": "unavailable",
            "error": error,
        })
        raise JudgeRouteError(error, provider_attempts)
    provider_attempts.append({
        "provider": "Mistral Voxtral API",
        "model": model,
        "status": "ok",
        "attempts": attempt + 1,
    })
    return _parse_direct_audio_rubric(
        text,
        judge_model=f"mistral/{model}",
        provider_attempts=provider_attempts,
    )


def _judge_openrouter_audio(
    prompt: str,
    audio_b64: str,
    reference_audio_b64: str,
    *,
    provider_attempts: list,
) -> RubricResult:
    """Send both audio clips to an audio-capable Gemini route on OpenRouter."""
    import urllib.error
    import urllib.request

    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("缺少 OPENROUTER_API_KEY，无法回退多模态音频评审。")
    model = os.environ.get("TTS_AUDIO_JUDGE_MODEL", "google/gemini-3.5-flash").strip()
    content = [
        {"type": "text", "text": prompt},
        {
            "type": "input_audio",
            "input_audio": {"data": audio_b64, "format": "mp3"},
        },
        {
            "type": "input_audio",
            "input_audio": {"data": reference_audio_b64, "format": "mp3"},
        },
    ]
    body = {
        "model": model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": content}],
    }
    req = urllib.request.Request(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:2000]
        error = f"OpenRouter audio HTTP {exc.code}: {detail}"
        provider_attempts.append({
            "provider": "OpenRouter audio route",
            "model": model,
            "status": "unavailable",
            "error": error,
        })
        if os.environ.get("MISTRAL_API_KEY", "").strip():
            return _judge_mistral_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        raise JudgeRouteError(error, provider_attempts) from None
    text = _message_text(data)
    if not text:
        error = f"OpenRouter audio 未返回评审文本：{data}"
        provider_attempts.append({
            "provider": "OpenRouter audio route",
            "model": model,
            "status": "unavailable",
            "error": error,
        })
        if os.environ.get("MISTRAL_API_KEY", "").strip():
            return _judge_mistral_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        raise JudgeRouteError(error, provider_attempts)
    provider_attempts.append({
        "provider": "OpenRouter audio route",
        "model": model,
        "status": "ok",
    })
    return _parse_direct_audio_rubric(
        text,
        judge_model=f"openrouter/{model}",
        provider_attempts=provider_attempts,
    )


def judge_gemini_audio(
    reference: str,
    emotion: str,
    audio_path: str,
    reference_audio_path: str,
) -> RubricResult:
    """让 Gemini 同时听合成音频与参考音频，执行正文四维 Rubric。

    默认关闭；--gemini 开启。依次尝试已配置的 Google Gemini、OpenRouter 与
    Mistral Voxtral，失败抛异常由上层记为失败。
    """
    import urllib.error
    import urllib.request
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    mistral_key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not key and not openrouter_key and not mistral_key:
        raise RuntimeError(
            "缺少 GEMINI_API_KEY / OPENROUTER_API_KEY / MISTRAL_API_KEY，"
            "无法使用直接音频评审。"
        )
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    if not reference_audio_path or not os.path.isfile(reference_audio_path):
        raise RuntimeError(
            f"音色一致性评估需要真实参考语音，文件不存在: {reference_audio_path!r}"
        )
    with open(reference_audio_path, "rb") as f:
        reference_audio_b64 = base64.b64encode(f.read()).decode()
    prompt = (
        "你是严格的 TTS 质量评审专家。你会收到两段音频：第一段是待评估的合成语音，"
        "第二段是参考说话人语音。请直接聆听并按正文四维 Rubric 独立打 1-5 整数分："
        "(1)准确性：逐字核对原文，检查漏读、错读、添读、数字、专名和多音字；"
        "(2)自然度：检查机器感、不自然停顿、流畅度、重音和韵律；"
        "(3)情感表达：检查语调、语速和强调是否符合期望情感；"
        "(4)音色一致性：只比较说话人音色，不要把内容或录音质量差异误当作不同说话人。"
        "每个理由必须引用一个可听见的具体观察。只输出 JSON："
        '{"准确性":{"score":int,"reason":str},"自然度":{"score":int,"reason":str},'
        '"情感表达":{"score":int,"reason":str},"音色一致性":{"score":int,"reason":str}}\n'
        f"合成语音原文：{reference}\n期望情感：{emotion}\n"
        "音频顺序：1=待评估合成语音；2=参考说话人语音。"
    )
    provider_attempts = []
    if not key:
        if openrouter_key:
            return _judge_openrouter_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        return _judge_mistral_audio(
            prompt,
            audio_b64,
            reference_audio_b64,
            provider_attempts=provider_attempts,
        )
    model = _resolve_gemini_model(key)
    body = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "audio/mp3", "data": audio_b64}},
            {"inline_data": {"mime_type": "audio/mp3", "data": reference_audio_b64}},
        ]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as exc:
        # Preserve the provider's diagnostic while never serializing the key
        # (it only appears in the request URL, not this response excerpt).
        detail = exc.read().decode("utf-8", "replace")[:2000]
        direct_error = f"Gemini HTTP {exc.code}: {detail}"
        provider_attempts.append({
            "provider": "Google Gemini API",
            "model": model,
            "status": "unavailable",
            "error": direct_error,
        })
        if openrouter_key:
            return _judge_openrouter_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        if mistral_key:
            return _judge_mistral_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        raise JudgeRouteError(direct_error, provider_attempts) from None
    # Gemini 在安全拦截时不返回 candidates（或 candidate 无 content/parts），
    # 防御式取值并给出带 promptFeedback 的清晰错误，交由上层记为该条失败。
    candidates = data.get("candidates") or []
    parts = []
    if candidates:
        parts = (candidates[0].get("content") or {}).get("parts") or []
    if not parts or not parts[0].get("text"):
        error = f"Gemini 未返回评审文本：{data.get('promptFeedback') or data}"
        provider_attempts.append({
            "provider": "Google Gemini API",
            "model": model,
            "status": "unavailable",
            "error": error,
        })
        if openrouter_key:
            return _judge_openrouter_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        if mistral_key:
            return _judge_mistral_audio(
                prompt,
                audio_b64,
                reference_audio_b64,
                provider_attempts=provider_attempts,
            )
        raise JudgeRouteError(error, provider_attempts)
    text = parts[0]["text"]
    provider_attempts.append({
        "provider": "Google Gemini API",
        "model": model,
        "status": "ok",
    })
    return _parse_direct_audio_rubric(
        text,
        judge_model=model,
        provider_attempts=provider_attempts,
    )


def sha256_file(path: str) -> str:
    """Return a content identity for an evidence audio file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
