"""
实验 5-6 的三个 Agent：

  VideoAnalyzerAgent —— 视频分析子 Agent，用"两步 Vision 定位"找目标场景边界。
  ProposerAgent      —— 把自然语言需求解析成剪辑计划，调用子 Agent 定位并执行剪辑。
  ReviewerAgent      —— 抽取成片关键帧，用 Vision 检查是否剪对，给出结构化反馈。

把视频分析封装为独立子 Agent 的意义：大量截图只进入子 Agent 的一次性上下文，
不会污染主 Agent（Proposer/Reviewer）的对话历史——见 demo.py 打印的 token 统计。
"""
import base64
import json
import os
import re

from openai import OpenAI

from ffmpeg_utils import extract_frame, probe_duration

TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-5.6-luna")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-5.6-luna")  # 必须支持图像输入

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_client = None


def map_model_to_openrouter(model: str) -> str:
    """把直连模型名映射为 OpenRouter 上的 id（非可映射 id 统一兜底到当前廉价旗舰）。"""
    if not model or "/" in model:
        return model or "openai/gpt-5.6-luna"
    m = model.lower()
    if m.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai/" + model
    if m.startswith("claude"):
        if "haiku" in m:
            return "anthropic/claude-haiku-4.5"
        if "sonnet" in m:
            return "anthropic/claude-sonnet-4.6"
        return "anthropic/claude-opus-4.8"
    if m.startswith("gemini"):
        return "google/" + model
    return "openai/gpt-5.6-luna"


def _temp_for(model):
    """推理模型（gpt-5 / o 系列等）不接受 temperature=0。"""
    return (1 if any(k in (model or "").lower()
                     for k in ("gpt-5", "o1", "o3", "o4", "thinking", "reasoner", "kimi-k3"))
            else 0)


def client() -> OpenAI:
    """构造（并缓存）OpenAI 客户端，含通用 OpenRouter 兜底。

    - 有 OPENAI_API_KEY：直连；但默认模型 gpt-5.x（直连需组织实名认证）且设置了
      OPENROUTER_API_KEY 时优先走 OpenRouter。
    - 无 OPENAI_API_KEY 但有 OPENROUTER_API_KEY：改走 OpenRouter（模型名自动映射）。
    """
    global _client, TEXT_MODEL, VISION_MODEL
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        orkey = os.getenv("OPENROUTER_API_KEY")
        prefer_or = bool(orkey) and (
            (TEXT_MODEL or "").lower().startswith("gpt-5") or (VISION_MODEL or "").lower().startswith("gpt-5")
        )
        if prefer_or or (not api_key and orkey):
            api_key, base_url = orkey, OPENROUTER_BASE_URL
            TEXT_MODEL = map_model_to_openrouter(TEXT_MODEL)
            VISION_MODEL = map_model_to_openrouter(VISION_MODEL)
        kw = {}
        if api_key:
            kw["api_key"] = api_key
        if base_url:
            kw["base_url"] = base_url
        _client = OpenAI(**kw)
    return _client


def _img_part(path: str) -> dict:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {"type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "low"}}


def _extract_json(text: str) -> dict:
    """从 LLM 回复里稳健地抠出第一个 JSON 对象。"""
    start = text.find("{")
    if start < 0:
        raise ValueError(f"未能从回复中解析 JSON：{text[:200]}")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError as e:
        raise ValueError(f"未能从回复中解析 JSON：{text[:200]}") from e
    if not isinstance(obj, dict):
        raise ValueError(f"未能从回复中解析 JSON：{text[:200]}")
    return obj


def _num(value, default: float) -> float:
    """把 LLM 返回的数值字段转成 float；字段缺失、为 null 或非法时回退 default。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class TokenMeter:
    """累计 token，用于对比'子 Agent 隔离截图'带来的主上下文节省。"""

    def __init__(self):
        self.prompt = 0
        self.completion = 0

    def add(self, resp):
        u = getattr(resp, "usage", None)
        if u:
            self.prompt += u.prompt_tokens
            self.completion += u.completion_tokens

    def total(self):
        return self.prompt + self.completion


# --------------------------------------------------------------------------- #
# 视频分析子 Agent：两步 Vision 定位
# --------------------------------------------------------------------------- #
class VideoAnalyzerAgent:
    def __init__(self, meter: TokenMeter = None):
        self.meter = meter or TokenMeter()

    def _vision_locate(self, video, timestamps, question, frame_dir):
        """抽取给定时间点的帧，连同问题交给 Vision LLM，返回 {start,end}。"""
        content = [{
            "type": "text",
            "text": (
                f"下面是同一段视频在不同时间点的截图（每张图前标注了该帧的时间，单位秒）。\n"
                f"目标问题：{question}\n"
                f"请判断'目标场景'在视频中出现的时间区间。只依据画面内容判断。\n"
                f"严格输出 JSON：{{\"start\": <起点秒>, \"end\": <终点秒>, "
                f"\"reason\": \"<简要依据>\"}}。若所有截图都看不到目标场景，"
                f"令 start=end=-1。"
            ),
        }]
        for t in timestamps:
            png = os.path.join(frame_dir, f"f_{t:.1f}.png")
            extract_frame(video, t, png)
            content.append({"type": "text", "text": f"[时间 t={t:.1f}s]"})
            content.append(_img_part(png))

        resp = client().chat.completions.create(
            model=VISION_MODEL,
            messages=[{"role": "user", "content": content}],
            temperature=_temp_for(VISION_MODEL),
            max_tokens=300,
        )
        self.meter.add(resp)
        data = _extract_json(resp.choices[0].message.content)
        # 模型可能省略 start/end 或返回 null——按约定的 -1 哨兵处理，走兜底逻辑。
        return _num(data.get("start"), -1.0), _num(data.get("end"), -1.0), data.get("reason", "")

    def locate(self, video, question, coarse_interval=10.0, fine_interval=1.0,
               frame_dir="output/frames"):
        """
        两步定位：
          第一步（粗）：每 coarse_interval 秒一帧，Vision 给出大致场景区间。
          第二步（细）：在粗区间上下各扩一个粗间隔，每 fine_interval 秒一帧，
                        Vision 精确定位边界。
        返回 (start, end, trace)。
        """
        os.makedirs(frame_dir, exist_ok=True)
        duration = probe_duration(video)
        trace = {}

        # ---- 第一步：粗粒度 ----
        coarse_ts = [t for t in _frange(0, duration, coarse_interval)]
        cs, ce, creason = self._vision_locate(video, coarse_ts, question, frame_dir)
        trace["coarse"] = {"timestamps": coarse_ts, "start": cs, "end": ce,
                           "reason": creason}

        if cs < 0 or ce < 0:
            # 兜底：粗定位失败——退化为全视频精扫（步长放大以控制成本）。
            trace["coarse_fallback"] = True
            step = max(fine_interval, duration / 20.0)
            scan_ts = list(_frange(0, duration, step))
            cs, ce, creason = self._vision_locate(video, scan_ts, question, frame_dir)
            trace["coarse"]["fallback_scan"] = {"start": cs, "end": ce}
            if cs < 0:
                raise RuntimeError(
                    "Vision 定位失败：在整段视频里都没找到匹配'{}'的场景。\n"
                    "请检查需求描述是否与视频内容相符，或更换视频。".format(question)
                )

        # ---- 第二步：细粒度（在粗区间外扩一个粗间隔）----
        lo = max(0.0, cs - coarse_interval)
        hi = min(duration, ce + coarse_interval)
        fine_ts = list(_frange(lo, hi, fine_interval))
        fs, fe, freason = self._vision_locate(video, fine_ts, question, frame_dir)
        trace["fine"] = {"window": [lo, hi], "timestamps_count": len(fine_ts),
                         "start": fs, "end": fe, "reason": freason}

        if fs < 0 or fe < 0 or fe <= fs:
            # 兜底：细定位失败——采用粗定位结果，保证流程可继续。
            trace["fine_fallback"] = True
            fs, fe = cs, ce

        # 收敛到视频范围内。
        fs = max(0.0, fs)
        fe = min(duration, fe)
        return fs, fe, trace


def _frange(start, stop, step):
    """浮点 range（含首、含接近末尾的采样点）。"""
    out = []
    t = start
    while t < stop - 1e-6:
        out.append(round(t, 3))
        t += step
    # 补一个接近末尾的采样点，确保末段场景被覆盖。
    last = round(max(start, stop - 0.5), 3)
    if not out or abs(out[-1] - last) > step / 2:
        out.append(last)
    return out


# --------------------------------------------------------------------------- #
# Proposer Agent
# --------------------------------------------------------------------------- #
class ProposerAgent:
    def __init__(self, meter: TokenMeter = None):
        self.meter = meter or TokenMeter()

    def parse_request(self, nl_request: str) -> dict:
        """把自然语言需求解析成结构化意图：目标场景描述 + 特效列表。"""
        resp = client().chat.completions.create(
            model=TEXT_MODEL,
            temperature=_temp_for(TEXT_MODEL),
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": (
                    "你是视频剪辑规划器。把用户的中文剪辑需求解析成 JSON。\n"
                    "字段：\n"
                    "  target_query: 用于视觉定位的一句话描述（英文更利于匹配画面文字），"
                    "说明要剪出哪个场景；\n"
                    "  effects: 特效数组，元素形如 "
                    "{\"type\":\"subtitle\",\"text\":\"...\"} 或 "
                    "{\"type\":\"slowmo\",\"factor\":2.0}，无特效则为 []。\n"
                    f"用户需求：{nl_request}\n"
                    "只输出 JSON。"
                ),
            }],
        )
        self.meter.add(resp)
        return _extract_json(resp.choices[0].message.content)

    def revise_bounds(self, start, end, feedback, duration):
        """根据 Reviewer 反馈微调边界（保守外扩/内收）。"""
        resp = client().chat.completions.create(
            model=TEXT_MODEL,
            temperature=_temp_for(TEXT_MODEL),
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    f"当前剪辑区间 start={start:.1f}s end={end:.1f}s，视频总长 {duration:.1f}s。\n"
                    f"审核反馈：{feedback}\n"
                    "请给出修正后的区间，输出 JSON {\"start\":..,\"end\":..}。"
                    "若反馈指出包含了无关片段则内收，若指出遗漏内容则外扩，幅度 1~5 秒。"
                ),
            }],
        )
        self.meter.add(resp)
        d = _extract_json(resp.choices[0].message.content)
        # 模型可能省略 start/end 或返回 null——缺失时维持当前区间不变。
        return max(0.0, _num(d.get("start"), start)), min(duration, _num(d.get("end"), end))


# --------------------------------------------------------------------------- #
# Reviewer Agent
# --------------------------------------------------------------------------- #
class ReviewerAgent:
    def __init__(self, meter: TokenMeter = None):
        self.meter = meter or TokenMeter()

    def review(self, clip_path, target_query, frame_dir="output/review_frames"):
        """
        抽取成片的首/中/尾关键帧，用 Vision 检查：
          - 是否完整包含目标场景（无遗漏）；
          - 是否夹带了无关场景（无多余）。
        返回结构化结果 {pass, score, feedback, frames_checked}。
        """
        os.makedirs(frame_dir, exist_ok=True)
        dur = probe_duration(clip_path)
        # 取首/中/尾，并在首尾稍微内缩避开黑帧。
        keyts = [min(0.5, dur * 0.1), dur / 2.0, max(0.0, dur - 0.5)]

        content = [{
            "type": "text",
            "text": (
                f"这是剪辑成片的几个关键帧（首/中/尾）。剪辑目标是：{target_query}。\n"
                "请检查：(1) 成片是否完整呈现了目标场景；(2) 是否夹带了不该出现的其他场景。\n"
                "严格输出 JSON：{\"pass\": true/false, \"score\": 0-10, "
                "\"feedback\": \"<发现的问题或确认无误>\"}。"
            ),
        }]
        for t in keyts:
            png = os.path.join(frame_dir, f"r_{t:.1f}.png")
            extract_frame(clip_path, t, png)
            content.append({"type": "text", "text": f"[成片内 t={t:.1f}s]"})
            content.append(_img_part(png))

        resp = client().chat.completions.create(
            model=VISION_MODEL,
            temperature=_temp_for(VISION_MODEL),
            max_tokens=300,
            messages=[{"role": "user", "content": content}],
        )
        self.meter.add(resp)
        data = _extract_json(resp.choices[0].message.content)
        data["frames_checked"] = keyts
        return data
