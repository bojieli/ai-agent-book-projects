"""
控制标记解析器（Control Markup Parser）
========================================

把带控制标记的文本解析成一串「片段」，每个片段要么是一段需要用某条参考语音
合成的语音（speech），要么是一段静音停顿（silence）。这一步对应书中「执行层
解析标记并映射到对应的参考语音」。

支持两类标记：

1) 状态标记（持续生效，直到被下一个同类标记改变）
   [EMO:neutral|happy|frustrated|thinking]           或  [情感=中性|高兴|沮丧|思考]
   [SPEED:normal|fast|slow] / [SPEED:0.8x]           或  [语速=正常|快|慢]
   [STYLE:formal|casual]                             或  [风格=正式|轻松]

2) 内联标记（一次性事件，插入停顿 / 填充音 / 非语言音，或临时改变状态）
   [THINKING]   思考停顿 + 迟疑语气（=情绪思考/慢速/正式，并插入停顿）
   [SEARCHING]  搜索性停顿（同上，停顿略短）
   [PAUSE] / <pause> / [停顿]     插入停顿
   [BREATH] / <breath>            Fish S1 原生吸气声
   [SIGH]  / <sigh>               Fish S1 原生叹气声
   [LAUGH:small] / [LAUGH] / <laugh>  Fish S1 原生轻笑声
   <emphasis>...</emphasis> / [强调]...[/强调]   对包裹的文本加重强调

非语言片段会保留为 S1 的 `(gasping)` / `(sighing)` / `(chuckling)` 原生标记，
由 Fish Audio 直接合成声音，而不是把拟声文字念出来。
"""

import re

# 中文取值 -> 英文维度值的别名映射
_EMO_ALIAS = {
    "中性": "neutral", "高兴": "happy", "开心": "happy", "兴奋": "happy",
    "沮丧": "frustrated", "无奈": "frustrated", "思考": "thinking",
}
_SPEED_ALIAS = {"正常": "normal", "快": "fast", "快速": "fast", "慢": "slow", "慢速": "slow"}
_STYLE_ALIAS = {"正式": "formal", "轻松": "casual", "随意": "casual"}

# 各内联事件插入的停顿时长（毫秒）
PAUSE_MS = 500
BREATH_MS = 400
THINKING_MS = 1200
SEARCHING_MS = 700
SIGH_TAIL_MS = 300


def _norm(value: str, alias: dict) -> str:
    v = value.strip()
    return alias.get(v, v.lower())


class Segment(dict):
    """一个片段：type='speech'(text, emotion, speed, style, emphasis) 或 type='silence'(ms)。"""


def parse(text: str, trace: list | None = None):
    """
    解析带控制标记的文本，返回片段列表。
    若传入 trace（list），会把「标记 -> 动作」的解析过程逐条记入，便于打印。
    """
    def log(msg):
        if trace is not None:
            trace.append(msg)

    # 当前状态（状态标记会持续改变它）
    state = {"emotion": "neutral", "speed": "normal", "style": "formal", "emphasis": False}
    segments: list[Segment] = []
    buf = []  # 累积当前状态下的普通文本

    def flush():
        """把缓冲区的普通文本作为一个 speech 片段输出。"""
        s = "".join(buf).strip()
        buf.clear()
        if s:
            segments.append(Segment(type="speech", text=s, **state))

    def add_silence(ms, why):
        flush()
        segments.append(Segment(type="silence", ms=ms))
        log(f"  {why:22s} -> 插入静音 {ms}ms")

    def add_speech_token(token, emotion, speed, style, why):
        """Insert a Fish S1 native non-verbal marker as a speech segment."""
        flush()
        segments.append(Segment(type="speech", text=token, emotion=emotion,
                                speed=speed, style=style, emphasis=False))
        log(f"  {why:22s} -> Fish S1 原生标记 '{token}' (情绪={emotion},语速={speed})")

    def set_state(**kw):
        flush()  # 状态改变前，先把旧状态的文本收尾
        for k, v in kw.items():
            state[k] = v

    # 用一个总正则切出所有 [..] 与 <..> 标记，其余为普通文本
    parts = re.split(r"(\[[^\]]*\]|<[^>]+>)", text)
    for part in parts:
        if not part:
            continue
        if not re.fullmatch(r"\[[^\]]*\]|<[^>]+>", part):
            buf.append(part)  # 普通文本
            continue

        m = part  # 标记原文
        inner = m[1:-1].strip()

        # --- 状态标记：EMO / SPEED / STYLE（英文冒号式 或 中文等号式） ---
        km = re.match(r"(?i)^(EMO|SPEED|STYLE)\s*:\s*(.+)$", inner)
        cm = re.match(r"^(情感|语速|风格)\s*=\s*(.+)$", inner)
        if km:
            key, val = km.group(1).upper(), km.group(2)
        elif cm:
            key = {"情感": "EMO", "语速": "SPEED", "风格": "STYLE"}[cm.group(1)]
            val = cm.group(2)
        else:
            key = val = None

        if key == "EMO":
            e = _norm(val, _EMO_ALIAS)
            set_state(emotion=e)
            log(f"  {m:22s} -> 情绪 = {e}")
            continue
        if key == "SPEED":
            raw = val.strip()
            v = raw.lower().replace("x", "")  # 兼容 0.8x
            # 先认英文取值(normal/fast/slow)，再认中文别名(正常/快/慢)
            if v in ("normal", "fast", "slow"):
                s = v
            elif raw in _SPEED_ALIAS:
                s = _SPEED_ALIAS[raw]
            else:
                # 数字型（如 0.8）就近映射到 fast/slow/normal，仅用于展示
                try:
                    f = float(v)
                    s = "fast" if f > 1.05 else ("slow" if f < 0.95 else "normal")
                except ValueError:
                    s = "normal"
            set_state(speed=s)
            log(f"  {m:22s} -> 语速 = {s}")
            continue
        if key == "STYLE":
            st = _norm(val, _STYLE_ALIAS)
            set_state(style=st)
            log(f"  {m:22s} -> 风格 = {st}")
            continue

        # --- 强调包裹 ---
        low = inner.lower()
        if low in ("emphasis", "强调"):
            set_state(emphasis=True)
            log(f"  {m:22s} -> 开启强调")
            continue
        if low in ("/emphasis", "/强调"):
            set_state(emphasis=False)
            log(f"  {m:22s} -> 关闭强调")
            continue

        # --- 内联事件标记 ---
        tag = low.split(":")[0]  # laugh:small -> laugh
        if tag == "thinking":
            set_state(emotion="thinking", speed="slow", style="formal")
            log(f"  {m:22s} -> 切换到 思考/慢速/正式 参考语音")
            add_silence(THINKING_MS, "[THINKING] 停顿")
            add_speech_token("(uncertain)嗯……", "thinking", "slow", "formal", "[THINKING] 填充音")
            continue
        if tag == "searching":
            set_state(emotion="thinking", speed="slow", style="formal")
            log(f"  {m:22s} -> 切换到 思考/慢速/正式 参考语音")
            add_silence(SEARCHING_MS, "[SEARCHING] 停顿")
            add_speech_token("(uncertain)那个……", "thinking", "slow", "formal", "[SEARCHING] 填充音")
            continue
        if tag in ("pause", "停顿"):
            add_silence(PAUSE_MS, m)
            continue
        if tag in ("breath", "换气"):
            add_speech_token("(gasping)", state["emotion"], state["speed"], state["style"], m)
            continue
        if tag == "sigh":
            add_speech_token("(sighing)", "frustrated", "slow", "formal", m)
            segments.append(Segment(type="silence", ms=SIGH_TAIL_MS))
            continue
        if tag == "laugh":
            add_speech_token("(chuckling)", "happy", "fast", "casual", m)
            continue

        # 未知标记：忽略但记录
        log(f"  {m:22s} -> [未知标记，已忽略]")

    flush()
    return segments


# ---------------------------------------------------------------------------
# 控制标记 -> 动作 的静态映射表（离线可查，供 demo.py --dump-mapping 打印）
# 这是「书中控制标记 -> 参考语音 / 非语言音」映射关系的单一事实来源。
# ---------------------------------------------------------------------------

# (类别, 标记写法, 中文写法, 映射到的动作)
MARKER_REFERENCE = [
    ("状态", "[EMO:neutral|happy|frustrated|thinking]", "[情感=中性|高兴|沮丧|思考]",
     "切换情绪维度，选择参考语音"),
    ("状态", "[SPEED:normal|fast|slow] / [SPEED:0.8x]", "[语速=正常|快|慢]",
     "切换语速维度（数字型就近映射到 fast/slow/normal）"),
    ("状态", "[STYLE:formal|casual]", "[风格=正式|轻松]", "切换口吻维度"),
    ("内联", "[THINKING]", "—", "切到「思考/慢速/正式」参考语音 + 插入 500ms 停顿"),
    ("内联", "[SEARCHING]", "—", "切到「思考/慢速/正式」参考语音 + 插入 400ms 停顿"),
    ("内联", "[PAUSE] / <pause>", "[停顿]", "插入 500ms 静音"),
    ("内联", "[BREATH] / <breath>", "[换气]", "插入 400ms 换气停顿"),
    ("内联", "[SIGH] / <sigh>", "—", "叹气拟声词「唉——」(沮丧音色) + 300ms 停顿"),
    ("内联", "[LAUGH:small] / [LAUGH] / <laugh>", "—", "轻笑拟声词「哈哈，」(高兴音色)"),
    ("内联", "<emphasis>…</emphasis>", "[强调]…[/强调]", "对包裹文本追加「加重强调」提示词"),
]


def format_marker_reference() -> str:
    """把 MARKER_REFERENCE 渲染成可打印的对齐表格字符串。"""
    lines = [f"{'类别':<4} {'标记写法':<40} {'中文写法':<24} 动作", "-" * 100]
    for cat, mark, zh, action in MARKER_REFERENCE:
        lines.append(f"{cat:<4} {mark:<40} {zh:<24} {action}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("控制标记 -> 动作 映射表：\n")
    print(format_marker_reference())
