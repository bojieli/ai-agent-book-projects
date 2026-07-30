"""实验 6-5：全自动 TTS 质量评估流水线 —— 配置与测试语料。

本模块集中管理：
  - 用到的 OpenAI 模型名与计费单价（仅供参考成本估算）；
  - 多个 TTS「配置」（model / voice / speed 的组合，作为待对比的对象）；
  - 一组带挑战性的参考文本（数字 / 多音字 / 长句 / 专有名词 + 情感）。
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 模型名（均为 OpenAI，读 OPENAI_API_KEY）。
# ---------------------------------------------------------------------------
WHISPER_MODEL = "whisper-1"        # 语音转写（回译），用于计算 WER/字准确率（须走 OpenAI 直连）
JUDGE_MODEL = "gpt-5.6-luna"       # LLM Rubric 评审模型（当前廉价旗舰；chat 调用可回退 OpenRouter）

# 可选的 Gemini 音频评审（书中方案）。默认用当前廉价旗舰 gemini-3.5-flash（已验证支持
# 音频输入，能直接「听」合成语音）。模型名可能随时间过期，运行时会通过 REST /models
# 探测校正。仅当 --gemini 开启时才会用到。
GEMINI_MODEL_DEFAULT = "gemini-3.5-flash"

# 计费单价（美元），仅用于打印粗略成本，不影响评分。数值随官方调整可能变化。
PRICE = {
    "tts-1": 15.0 / 1_000_000,          # $ / 字符
    "tts-1-hd": 30.0 / 1_000_000,       # $ / 字符
    "gpt-4o-mini-tts": 12.0 / 1_000_000,
    "whisper-1": 0.006 / 60,            # $ / 秒
}


@dataclass
class TTSConfig:
    """一个待评估的 TTS 配置。name 需在整表内唯一。

    provider 指明合成走哪个服务商（openai / elevenlabs / fishaudio / minimax /
    doubao）。model / voice / speed 的语义由各 provider 自行解释：例如 elevenlabs
    的 voice 是 voice_id，fishaudio 的 voice 是 reference_id（可留空用默认音色）。
    """

    name: str
    model: str
    voice: str
    speed: float = 1.0
    provider: str = "openai"

    def supports_speed(self) -> bool:
        # 只有部分 provider/模型支持 speed 参数；不支持时忽略该字段。
        if self.provider == "openai":
            return self.model in ("tts-1", "tts-1-hd")
        return self.provider in ("minimax", "doubao")


# ---------------------------------------------------------------------------
# 多 provider 注册表（对应书中「接入主流服务：OpenAI、ElevenLabs、Fish Audio、
# Minimax、豆包」）。每个 provider 声明所需环境变量与一个代表性配置，便于跨服务商
# 横向对比。除 OpenAI 外均按各家公开 REST 接口实现，缺 key 时该 provider 的行会被
# 记为失败而不影响整表（见 demo.py）。
# ---------------------------------------------------------------------------
# 环境变量别名：同一凭据可能有多个历史/惯用名，任意一个被设置即视为已配置。
ENV_ALIASES = {
    "FISH_API_KEY": ("FISH_API_KEY", "FISHAUDIO_API_KEY"),
}


def env_get(name: str) -> str:
    """读取环境变量，支持 ENV_ALIASES 中登记的别名，返回第一个非空值（已 strip）。"""
    import os
    for n in ENV_ALIASES.get(name, (name,)):
        val = os.environ.get(n, "").strip()
        if val:
            return val
    return ""


@dataclass
class ProviderInfo:
    key: str                # 内部标识（--providers 用）
    label: str              # 展示名
    env: tuple              # 该 provider 合成所需的环境变量名
    note: str               # 一句话说明 voice 字段语义等

    def configured(self) -> bool:
        return all(env_get(e) for e in self.env)


PROVIDERS = {
    "openai": ProviderInfo(
        "openai", "OpenAI", ("OPENAI_API_KEY",),
        "voice=alloy/nova/…，model=tts-1/tts-1-hd/gpt-4o-mini-tts；本仓库唯一端到端验证过的 provider。",
    ),
    "elevenlabs": ProviderInfo(
        "elevenlabs", "ElevenLabs", ("ELEVENLABS_API_KEY",),
        "voice=voice_id，model 默认 eleven_multilingual_v2（多语言/中文）。",
    ),
    "fishaudio": ProviderInfo(
        "fishaudio", "Fish Audio", ("FISH_API_KEY",),
        "voice=reference_id（留空用默认音色），走 /v1/tts；key 亦可用别名 FISHAUDIO_API_KEY。",
    ),
    "minimax": ProviderInfo(
        "minimax", "Minimax", ("MINIMAX_API_KEY",),
        "voice=voice_id，model 默认 speech-2.8-hd（另有 speech-2.8-turbo）；Bearer 鉴权，"
        "MINIMAX_REGION 选 global(api.minimax.io)/cn(api.minimaxi.com)。",
    ),
    "doubao": ProviderInfo(
        "doubao", "豆包（火山引擎）", ("DOUBAO_APP_ID", "DOUBAO_ACCESS_TOKEN"),
        "voice=voice_type，走 openspeech.bytedance.com；鉴权头为 'Bearer;{token}'。",
    ),
}

# 各 provider 的代表性配置（--providers 选中时，每个 provider 取这一条参与对比）。
# 非 OpenAI 的 voice/model 取各家常见默认值，可在此按账号可用音色调整。
PROVIDER_CONFIGS = {
    # Reuse the identical default-grid identity so a cross-provider campaign
    # can audit an existing OpenAI artifact instead of synthesizing it twice.
    "openai": TTSConfig("tts1-alloy-1.0", provider="openai", model="tts-1", voice="alloy"),
    "elevenlabs": TTSConfig("elevenlabs-multi", provider="elevenlabs",
                            model="eleven_multilingual_v2", voice="21m00Tcm4TlvDq8ikWAM"),
    # This immutable reference ID is the same real source voice used to build
    # Chapter 9's checked-in 24-clip Fish S1 library.  Accounts that cannot
    # access it can supply FISH_REFERENCE_ID explicitly; an empty/default
    # voice would make the voice-consistency arm scientifically meaningless.
    "fishaudio": TTSConfig(
        "fishaudio-s1-clone",
        provider="fishaudio",
        model="s1",
        voice=os.getenv("FISH_REFERENCE_ID", "6df3c1e14c9440e9ac978556536bf116"),
    ),
    "minimax": TTSConfig("minimax-hd", provider="minimax",
                        model="speech-2.8-hd", voice="male-qn-qingse"),
    "doubao": TTSConfig("doubao-tts", provider="doubao",
                       model="volcano_tts", voice="zh_female_qingxin"),
}


# 默认对比的配置集合：覆盖 model（tts-1 vs tts-1-hd）、voice、speed 三个维度，
# 便于观察不同配置在准确性/自然度上的差异。默认全部走 OpenAI 以保证零额外配置跑通。
TTS_CONFIGS = [
    TTSConfig("tts1-alloy-1.0", model="tts-1", voice="alloy", speed=1.0),
    TTSConfig("tts1hd-alloy-1.0", model="tts-1-hd", voice="alloy", speed=1.0),
    TTSConfig("tts1-nova-1.0", model="tts-1", voice="nova", speed=1.0),
    TTSConfig("tts1-alloy-1.5", model="tts-1", voice="alloy", speed=1.5),
]

# 可选加入（--extra 开启）：gpt-4o-mini-tts。默认不加入以保证一定跑通。
EXTRA_CONFIGS = [
    TTSConfig("4omini-nova-1.0", model="gpt-4o-mini-tts", voice="nova", speed=1.0),
]


@dataclass
class Sample:
    """一条参考文本 + 期望情感标签（供 Rubric 情感维度参考）。"""

    id: str
    text: str
    challenge: str      # 该样本主要考察的挑战点
    emotion: str = "中性"


# 多样化测试语料：数字/日期、多音字、长句、专有名词+情感。
CORPUS = [
    Sample(
        id="num",
        text="2026年第三季度营收增长了37.5%，同比提升12个百分点。",
        challenge="数字/百分比/日期",
        emotion="中性",
    ),
    Sample(
        id="polyphone",
        text="银行行长正在重新调整这件事的重点，长此以往，还得还清所有欠款。",
        challenge="多音字（行/长/重/还）",
        emotion="中性",
    ),
    Sample(
        id="long",
        text="据报道，随着人工智能技术的快速发展，越来越多的企业开始将大语言模型"
             "应用于客户服务、内容创作和数据分析等场景，从而显著提升了运营效率。",
        challenge="长句/新闻文体",
        emotion="中性",
    ),
    Sample(
        id="emotion",
        text="太棒了！OpenAI 刚刚发布的新模型在 GAIA 基准测试上表现惊人！",
        challenge="专有名词 + 感叹情感",
        emotion="兴奋",
    ),
    Sample(
        id="sad",
        text="很遗憾地通知您，救援队今天仍然没有找到失踪的登山者。",
        challenge="悲伤情感/低语速低语调",
        emotion="悲伤",
    ),
    Sample(
        id="question",
        text="请问您希望把明天下午三点的预约改到星期五上午吗？",
        challenge="对话文体/疑问句升调",
        emotion="礼貌询问",
    ),
]
