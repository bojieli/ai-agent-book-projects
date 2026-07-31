"""
提议者（Proposer）与审核者（Reviewer）两个 Agent，以及一个带 token 计量的 LLM 客户端。

设计要点（对应书中“提议者-审核者”机制）：
  - Proposer 只处理**文本**：论文正文 + 累积的结构化文字反馈；从不接收渲染图片。
  - Reviewer 每一轮**只看最新一版的渲染截图**，且每轮都是一次全新的、无历史的调用。
  - 单 Agent 自审对照组则相反：同一段对话里不断累积历次渲染的图片，上下文迅速膨胀。

所有对 OpenAI 的调用都经过 TokenMeter 统计 prompt / completion token，
用于最后的“单 Agent vs 双 Agent 上下文消耗”对比。
"""
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI
from PIL import Image

# 文本生成用的模型（Proposer / 单 Agent 的文本部分）
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gpt-5.6-luna")
# 视觉审查用的模型（Reviewer / 单 Agent 的看图部分），必须支持图像
VISION_MODEL = os.environ.get("VISION_MODEL", "gpt-5.6-luna")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PROVIDER = os.environ.get("PPT_PROVIDER", "auto")


def configure_provider(provider: str) -> None:
    global PROVIDER
    PROVIDER = provider


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

# 发送给 Vision 前把截图缩放到该宽度，兼顾“看得清文字溢出”与“控制 token 成本”
VISION_IMAGE_WIDTH = 1280

FIGURE_PAGE_TITLES = {
    "paper_figure_1_transformer.png": "Transformer Architecture (Figure 1)",
    "paper_figure_3_long_distance.png": "Long-Distance Attention (Figure 3)",
    "paper_figure_4_anaphora.png": "Anaphora Attention (Figure 4)",
}


class TokenMeter:
    """累计一个“角色/模式”消耗的 token，并记录每次调用的 prompt token（用于看上下文峰值）。"""

    def __init__(self, name: str):
        self.name = name
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0
        self.peak_prompt_tokens = 0  # 单次调用最大的 prompt token —— 决定是否“撑爆上下文”
        self.per_call_prompt = []
        self.receipts = []

    def add(self, response, request: dict, latency_s: float | None = None):
        usage = response.usage
        self.calls += 1
        pt = usage.prompt_tokens
        self.prompt_tokens += pt
        self.completion_tokens += usage.completion_tokens
        self.peak_prompt_tokens = max(self.peak_prompt_tokens, pt)
        self.per_call_prompt.append(pt)
        choice = response.choices[0]
        receipt = {
            "meter": self.name,
            "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "latency_s": round(latency_s, 3) if latency_s is not None else None,
            "request": _sanitize_for_evidence(request),
            "response": {
                "id": response.id,
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "content": choice.message.content,
            },
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cached_prompt_tokens": getattr(
                    getattr(usage, "prompt_tokens_details", None), "cached_tokens", None
                ),
            },
        }
        self.receipts.append(receipt)
        checkpoint = os.environ.get("PPT_RECEIPT_CHECKPOINT")
        if checkpoint:
            path = Path(checkpoint)
            path.parent.mkdir(parents=True, exist_ok=True)
            existing = []
            if path.is_file():
                existing = json.loads(path.read_text(encoding="utf-8"))
            existing.append(receipt)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(path)

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens


def _client() -> OpenAI:
    # 通用 OpenRouter 兜底：无直连 key，或默认 gpt-5.x（直连需组织实名认证）时改走 OpenRouter。
    global TEXT_MODEL, VISION_MODEL
    if PROVIDER == "ark":
        api_key = os.environ.get("ARK_API_KEY")
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
    elif PROVIDER == "moonshot":
        api_key = os.environ.get("MOONSHOT_API_KEY")
        base_url = "https://api.moonshot.cn/v1"
    elif PROVIDER == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        base_url = OPENROUTER_BASE_URL
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL")
    orkey = os.environ.get("OPENROUTER_API_KEY")
    prefer_or = PROVIDER == "auto" and bool(orkey) and (
        (TEXT_MODEL or "").lower().startswith("gpt-5") or (VISION_MODEL or "").lower().startswith("gpt-5")
    )
    if PROVIDER == "openrouter" or prefer_or or (PROVIDER == "auto" and not api_key and orkey):
        api_key, base_url = orkey, OPENROUTER_BASE_URL
        # 走 OpenRouter 时把模型名映射为其 id（幂等：已带前缀的 id 原样返回）。
        TEXT_MODEL = map_model_to_openrouter(TEXT_MODEL)
        VISION_MODEL = map_model_to_openrouter(VISION_MODEL)
    if not api_key:
        raise SystemExit(
            "❌ 未检测到 OPENAI_API_KEY（或 OPENROUTER_API_KEY 兜底）。请先 `cp env.example .env` 并填入有效的 "
            "OpenAI API Key（或 `export OPENAI_API_KEY=your-openai-api-key` / `export OPENROUTER_API_KEY=...`）后再运行。"
        )
    # timeout + max_retries：单次网络抖动/SSL 中断会自动重试，而不是让整条流水线崩溃。
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        # Large single-agent requests carry the extracted paper plus several
        # full slide revisions (and later image history). Ark can legitimately
        # take more than one minute to produce the complete Markdown deck.
        # Keep bounded retries, but give each real request enough time instead
        # of abandoning an otherwise healthy formal campaign mid-arm.
        timeout=300.0,
        max_retries=4,
    )


def _sanitize_for_evidence(value):
    """Retain raw public text while replacing large data URLs with hashes."""
    if isinstance(value, dict):
        return {key: _sanitize_for_evidence(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_evidence(item) for item in value]
    if isinstance(value, str) and value.startswith("data:"):
        return {
            "data_url_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
            "characters": len(value),
            "media_type": value.split(";", 1)[0][5:],
        }
    return value


def encode_image(path: str) -> str:
    """读取 PNG，缩放到统一宽度，编码为 data URL（base64）。"""
    img = Image.open(path).convert("RGB")
    if img.width > VISION_IMAGE_WIDTH:
        h = int(img.height * VISION_IMAGE_WIDTH / img.width)
        img = img.resize((VISION_IMAGE_WIDTH, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _extract_json(text: str):
    """从模型回复里稳健地抽取 JSON（容忍 ```json 代码块或前后多余文字）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # 找到第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _extract_slides_md(text: str) -> str:
    """从模型回复里抽取 slides.md 内容（容忍 ```markdown 包裹）。"""
    m = re.search(r"```(?:markdown|md)?\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def _slide_count(slides: str) -> int:
    """Count Slidev pages when the required frontmatter is present."""
    # The closing frontmatter fence plus every inter-page fence yields exactly
    # one ``\n---\n`` occurrence per rendered page.
    return slides.replace("\r\n", "\n").count("\n---\n")


def _slide_contract_issues(slides: str) -> list[str]:
    """Return deterministic density/page-count failures before rendering.

    Vision remains the authority for pixel-level quality.  This inexpensive
    source gate prevents repeatedly paying to render drafts that already
    violate the Proposer's explicit 18--20 page / four-bullet instructions.
    """
    normalized = slides.replace("\r\n", "\n")
    pages = normalized.split("\n---\n")[1:]
    issues = []
    if not 18 <= len(pages) <= 20:
        issues.append(f"page count is {len(pages)}; required 18-20")
    for page_number, page in enumerate(pages, 1):
        bullet_count = len(re.findall(r"(?m)^\s*(?:[-*+]|[■▪•])\s+", page))
        if bullet_count > 4:
            issues.append(
                f"page {page_number} has {bullet_count} bullets; maximum is 4 total"
            )
        figure_match = re.search(r"/((?:paper_figure_)[^\s\"')>]+)", page)
        if figure_match:
            required_title = FIGURE_PAGE_TITLES.get(figure_match.group(1))
            if required_title and not re.search(
                rf"(?m)^#{{1,3}}\s+{re.escape(required_title)}\s*$", page
            ):
                issues.append(
                    f"page {page_number} source figure must use one-line title: "
                    f"{required_title}"
                )
            style_match = re.search(r"style=[\"']([^\"']*)[\"']", page)
            style = style_match.group(1) if style_match else ""
            if not all(re.search(pattern, style) for pattern in (
                r"(?:^|;)\s*max-height:\s*460px\s*(?:;|$)",
                r"(?:^|;)\s*width:\s*100%\s*(?:;|$)",
                r"(?:^|;)\s*object-fit:\s*contain\s*(?:;|$)",
            )):
                issues.append(
                    f"page {page_number} source figure must use inline style "
                    "max-height: 460px; width: 100%; object-fit: contain;"
                )
            prose_lines = [
                line.strip()
                for line in page.splitlines()
                if line.strip()
                and not line.lstrip().startswith("#")
                and "<img" not in line
            ]
            if bullet_count or len(prose_lines) > 1:
                issues.append(
                    f"page {page_number} source figure must have only a title "
                    "and at most one caption"
                )
    return issues


# --------------------------------------------------------------------------- #
# Reviewer 的审查评分标准（Proposer / 单 Agent / 独立评委共用同一套 rubric）
# --------------------------------------------------------------------------- #
REVIEW_RUBRIC = """你是一名严格的演示文稿质量审核员（Reviewer）。你会看到一份由 Slidev 渲染出的 PPT，
每张图对应一页幻灯片（按顺序编号，从第 1 页开始）。请逐页检查以下问题：

- text_overflow（文字溢出/被裁切超出页面边界）
- overcrowded（内容过多/过于拥挤/留白不足）
- image_size（图片过大顶出布局，或过小看不清）
- readability（字号过小、对比度差、代码块难读）
- layout（对齐混乱、标题与正文比例失衡、空页）

请以**目标用户是听众**的严格标准审查——一页幻灯片若要点超过约 5 条、或正文文字块偏长、
或图片挤压了文字空间，都应视为 overcrowded/image_size 问题。五个或更少的精炼要点本身
是可接受的，不得仅因页面恰好有五个要点而报错。报告真实存在的问题，
但不要放过"塞得太满"。对每个问题给出：page（页码，整数）、
issue_type（上面之一）、severity（high/medium/low）、suggestion（具体、可执行的修改建议，中文）。

同时给出：
- overall_score：0-100 的整体质量分（越高越好）
- pass：布尔值，仅当整份 PPT **既无 high 也无 medium 级问题**、排版干净可读时才为 true

严格输出如下 JSON（不要输出任何多余文字）：
{
  "overall_score": <int>,
  "pass": <bool>,
  "issues": [
    {"page": <int>, "issue_type": "<type>", "severity": "<high|medium|low>", "suggestion": "<中文建议>"}
  ]
}"""


class Reviewer:
    """审核者 Agent：看最新一版渲染截图，输出结构化 JSON 建议。每轮独立调用、无历史。"""

    def __init__(self, meter: TokenMeter):
        self.client = _client()
        self.meter = meter

    def review(self, png_paths: list[str]) -> dict:
        content = [{"type": "text",
                    "text": f"这份 PPT 共 {len(png_paths)} 页，下面按页码顺序给出每一页的渲染截图。请审查。"}]
        for i, p in enumerate(png_paths, 1):
            content.append({"type": "text", "text": f"第 {i} 页："})
            content.append({"type": "image_url",
                            "image_url": {"url": encode_image(p), "detail": "high"}})
        request = {
            "model": VISION_MODEL,
            "messages": [
                {"role": "system", "content": REVIEW_RUBRIC},
                {"role": "user", "content": content},
            ],
            "temperature": 0.2,
        }
        started = time.monotonic()
        resp = self.client.chat.completions.create(**request)
        self.meter.add(resp, request, time.monotonic() - started)
        return _extract_json(resp.choices[0].message.content)


PROPOSER_SYSTEM = """你是一名擅长把学术论文转化为演示文稿的 Proposer Agent。
你用 Slidev 框架（Markdown + HTML）编写 PPT 源码 slides.md。

Slidev 语法要点：
- 文件开头是 YAML frontmatter（--- 包裹），设置 theme: default。
- 用单独一行的 `---`（前后空行）分隔每一页幻灯片。
- 首页通常放标题、作者、会议。
- 引用图片用 markdown：![说明](/图片文件名.png)，可用 HTML 控制尺寸，
  例如 <img src="/speedup_bar.png" class="h-60 mx-auto" />。
- 可用 Windi/Uno CSS 工具类控制排版（如 text-sm、grid grid-cols-2 gap-4）。

要求：
- 最终生成 18-20 页，覆盖论文的标题、背景/动机、方法、实验结果、局限与结论。
- 至少在 3 页中使用提供的图表/表格，且图文匹配。
- 每页最多 4 个要点，不得粘贴长段原文，宁可精简也不要溢出。
- 三张原论文图必须各占一张专用页面；为避免 UnoCSS 动态类漏编译，图片必须使用行内属性
  `style="max-height: 460px; width: 100%; object-fit: contain;"`，并且页面除标题和一行
  短图注外不得放正文，以保证整张图和图注都在页面边界内且标签可读。
- 三张原图页面必须分别使用不会换行的精确标题：`Transformer Architecture (Figure 1)`、
  `Long-Distance Attention (Figure 3)`、`Anaphora Attention (Figure 4)`。
- 要点统一用 Markdown `- `，不要用 `■` 等字符伪装项目符号；多个小节合计仍不得超过 4 条。
- 只输出 slides.md 的完整内容，用 ```markdown 代码块包裹，不要额外解释。"""


class Proposer:
    """提议者 Agent：只吃文本（论文 + 累积文字反馈），产出 slides.md。"""

    def __init__(self, meter: TokenMeter, paper_md: str, figures: dict):
        self.client = _client()
        self.meter = meter
        fig_desc = "\n".join(f"- {name}：{desc}" for name, desc in figures.items())
        first_user = (
            f"以下是论文全文（Markdown）：\n\n{paper_md}\n\n"
            f"可直接引用的图表文件（放在 Slidev public 目录，用 /文件名 引用）：\n{fig_desc}\n\n"
            f"请生成一版 18-20 页的完整初稿。内容必须忠于论文，至少引用上面列出的三张原论文图，"
            f"并覆盖问题、Transformer 架构、注意力机制、训练、主要实验、局限和结论。"
            f"不要复制长段原文；每页保持听众可读的信息密度。生成完整的 slides.md。"
        )
        # Proposer 的对话历史——只累积文本，永不加入图片
        self.messages = [
            {"role": "system", "content": PROPOSER_SYSTEM},
            {"role": "user", "content": first_user},
        ]

    def _generate(self) -> str:
        for attempt in range(3):
            request = {"model": TEXT_MODEL, "messages": self.messages, "temperature": 0.3}
            started = time.monotonic()
            resp = self.client.chat.completions.create(**request)
            self.meter.add(resp, request, time.monotonic() - started)
            reply = resp.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            slides = _extract_slides_md(reply)
            issues = _slide_contract_issues(slides)
            if not issues:
                return slides
            if attempt < 2:
                self.messages.append({
                    "role": "user",
                    "content": (
                        "硬性源码验收失败：" + "; ".join(issues) + "。"
                        "请在不删除三张原论文图、不丢失主要贡献的前提下精简、合并或拆分内容，"
                        "重新输出完整 slides.md；必须保持 18–20 页且每页最多 4 个 Markdown 要点。"
                    ),
                })
        raise RuntimeError(
            "Proposer failed the source density contract after 3 attempts: "
            + "; ".join(issues)
        )

    def propose(self) -> str:
        """首轮生成。"""
        return self._generate()

    def revise(self, review: dict) -> str:
        """根据 Reviewer 的结构化文字反馈修订（只把 JSON 文本加入上下文）。"""
        feedback = json.dumps(review, ensure_ascii=False, indent=2)
        self.messages.append({
            "role": "user",
            "content": (
                "审核者（Reviewer）渲染了你上一版 slides.md 的每一页截图，"
                "给出如下结构化改进建议（JSON）：\n\n"
                f"{feedback}\n\n"
                "请理解这些问题并修订 slides.md（可拆页、精简文字、调整图片尺寸等），"
                "重新输出完整的 slides.md。修订后仍必须保持 18–20 页；解决拥挤时优先精简与合并，"
                "不得用无限拆页规避版面问题。"
            ),
        })
        return self._generate()


# --------------------------------------------------------------------------- #
# 单 Agent 自审对照组：同一段对话里既生成、又看自己的渲染图、又修订。
# 关键区别：历次渲染的图片会**留在**同一上下文里，导致上下文随迭代快速膨胀。
# --------------------------------------------------------------------------- #
SELF_REVIEW_SYSTEM = PROPOSER_SYSTEM + """

此外，你还要**自我审查**：当收到自己 PPT 的渲染截图时，先在心里按下列标准找出问题
（文字溢出、内容拥挤、图片尺寸、可读性、布局），再据此输出修订后的完整 slides.md。"""


class SelfReviewAgent:
    """单 Agent 自审：一条不断增长的对话，图片累积在上下文中。"""

    def __init__(self, meter: TokenMeter, paper_md: str, figures: dict):
        self.client = _client()
        self.meter = meter
        fig_desc = "\n".join(f"- {name}：{desc}" for name, desc in figures.items())
        first_user = (
            f"以下是论文全文（Markdown）：\n\n{paper_md}\n\n"
            f"可直接引用的图表文件：\n{fig_desc}\n\n"
            f"请生成一版 18-20 页的完整初稿。内容必须忠于论文，至少引用上面列出的三张原论文图，"
            f"并覆盖问题、Transformer 架构、注意力机制、训练、主要实验、局限和结论。"
            f"不要复制长段原文；每页保持听众可读的信息密度。生成完整的 slides.md。"
        )
        self.messages = [
            {"role": "system", "content": SELF_REVIEW_SYSTEM},
            {"role": "user", "content": first_user},
        ]

    def propose(self) -> str:
        return self._generate_with_page_gate()

    def _generate_with_page_gate(self) -> str:
        for attempt in range(3):
            request = {"model": VISION_MODEL, "messages": self.messages, "temperature": 0.3}
            started = time.monotonic()
            resp = self.client.chat.completions.create(**request)
            self.meter.add(resp, request, time.monotonic() - started)
            reply = resp.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            slides = _extract_slides_md(reply)
            issues = _slide_contract_issues(slides)
            if not issues:
                return slides
            if attempt < 2:
                self.messages.append({
                    "role": "user",
                    "content": (
                        "硬性源码验收失败：" + "; ".join(issues) + "。"
                        "请保留三张原论文图和全部核心章节，压缩或重组后重新输出完整 slides.md；"
                        "必须保持 18–20 页且每页最多 4 个 Markdown 要点。"
                    ),
                })
        raise RuntimeError(
            "Single Agent failed the source density contract after 3 attempts: "
            + "; ".join(issues)
        )

    def self_review_and_revise(self, png_paths: list[str]) -> str:
        """把最新渲染截图加入**同一**上下文，让模型自审并修订。图片会一直留在历史里。"""
        content = [{"type": "text",
                    "text": (f"这是你上一版 slides.md 渲染出的 {len(png_paths)} 页截图。"
                             "请自我审查（文字溢出/拥挤/图片尺寸/可读性/布局），"
                             "然后输出修订后的完整 slides.md。修订后硬性保持 18–20 页，"
                             "并保留三张原论文图。")}]
        for i, p in enumerate(png_paths, 1):
            content.append({"type": "text", "text": f"第 {i} 页："})
            content.append({"type": "image_url",
                            "image_url": {"url": encode_image(p), "detail": "high"}})
        self.messages.append({"role": "user", "content": content})
        return self._generate_with_page_gate()


def independent_judge(png_paths: list[str], meter: TokenMeter) -> dict:
    """用同一套 rubric、独立地给某一版最终 PPT 打分，用于公平比较两种方案的质量。"""
    reviewer = Reviewer(meter)
    return reviewer.review(png_paths)
