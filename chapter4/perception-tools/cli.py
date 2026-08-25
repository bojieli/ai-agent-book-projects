#!/usr/bin/env python3
"""
感知工具 MCP 服务器 —— 统一命令行入口（实验 4-2）。

除了以 MCP stdio 协议对外提供服务（见 src/main.py），本文件提供一个不依赖
MCP 客户端的命令行入口，方便直接列出、调用和演示各类感知工具：

    python cli.py list                 # 按五大类列出全部感知工具
    python cli.py info <tool>          # 查看某个工具的参数签名
    python cli.py run <tool> k=v ...   # 直接调用某个工具并打印 JSON 结果
    python cli.py demo [--offline]     # 运行一个端到端的感知场景演示

工具按《深入理解 AI Agent》第四章「感知工具」的五类场景组织：
搜索、多模态理解、文件系统、公开数据源、私有数据源。

设计说明：
- 每个工具都是异步函数，返回统一的 ActionResponse（JSON）。CLI 负责运行事件
  循环、解析 JSON 并友好打印。
- 工具按需惰性导入：只有真正调用某个工具时才导入其所在模块，因此在缺少
  可选依赖（如 yfinance、opencv、whisper）时，list / info / 离线 demo 仍可正常工作。
"""
import argparse
import asyncio
import importlib
import inspect
import json
import logging
import sys
import tempfile
import typing
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_DIR))

# 五大类的中文标题（与书中实验 4-2 的分类一一对应）
CATEGORIES = {
    "search": "搜索",
    "multimodal": "多模态理解",
    "filesystem": "文件系统",
    "public": "公开数据源",
    "private": "私有数据源",
}


class Tool(typing.NamedTuple):
    """一个感知工具的注册项。"""
    name: str          # CLI / MCP 中暴露的工具名
    category: str      # 所属分类（CATEGORIES 的 key）
    module: str        # src/ 下的模块名
    func: str          # 模块中的异步函数名
    desc: str          # 一句话中文描述
    online: bool = False   # 是否需要联网
    note: str = ""     # 额外说明（如需要 API Key / 授权）


# ---------------------------------------------------------------------------
# 工具注册表：与 src/main.py 暴露的 MCP 工具保持一致，并补齐 README 中已声明、
# 但此前未在 main.py 注册的三个工具（crypto_price / location_search / poi_search）。
# ---------------------------------------------------------------------------
TOOLS: list[Tool] = [
    # ---- 搜索 ----
    Tool("web_search", "search", "search_tools", "search_web",
         "使用 DuckDuckGo 进行网络搜索（免费，无需 API Key）", online=True),
    Tool("knowledge_base_search", "search", "search_tools", "search_knowledge_base",
         "在本地知识库目录中做全文检索"),
    Tool("download", "search", "search_tools", "download_file",
         "从 URL 下载文件到本地（含大小/覆盖保护）", online=True),
    Tool("google_search_enhanced", "search", "google_search_enhanced", "google_search_api",
         "Google Custom Search，失败时回退 DuckDuckGo", online=True,
         note="Google API 需 GOOGLE_API_KEY，未配置则自动回退"),

    # ---- 多模态理解 ----
    Tool("webpage_reader", "multimodal", "multimodal_tools", "read_webpage",
         "抓取并提取网页正文/链接", online=True),
    Tool("webpage_read_enhanced", "multimodal", "google_search_enhanced", "read_webpage_content",
         "增强版网页正文提取", online=True),
    Tool("document_reader", "multimodal", "multimodal_tools", "read_document",
         "读取 PDF/DOCX/PPTX 文档内容"),
    Tool("pdf_extract", "multimodal", "document_processing_tools", "extract_pdf_text",
         "提取 PDF 文本（支持页码范围）"),
    Tool("docx_extract", "multimodal", "document_processing_tools", "extract_docx_content",
         "提取 Word（DOCX）文档内容"),
    Tool("pptx_extract", "multimodal", "document_processing_tools", "extract_pptx_content",
         "提取 PowerPoint（PPTX）内容"),
    Tool("csv_parse", "multimodal", "document_processing_tools", "extract_csv_content",
         "解析 CSV 表格数据"),
    Tool("image_parser", "multimodal", "multimodal_tools", "parse_image",
         "解析图片（可选 LLM 视觉分析）", note="use_llm 需视觉模型 API"),
    Tool("image_ocr", "multimodal", "media_processing_tools", "extract_text_ocr",
         "对图片做 OCR 文字识别", note="需安装 tesseract"),
    Tool("image_analyze", "multimodal", "media_processing_tools", "analyze_image_ai",
         "用视觉模型分析图片内容", note="需视觉模型 API"),
    Tool("image_metadata", "multimodal", "media_processing_tools", "get_image_metadata",
         "读取图片 EXIF 等元数据"),
    Tool("video_parser", "multimodal", "multimodal_tools", "parse_video",
         "提取视频元数据/采样帧"),
    Tool("video_keyframes", "multimodal", "media_processing_tools", "extract_video_keyframes",
         "从视频抽取关键帧"),
    Tool("video_analyze", "multimodal", "media_processing_tools", "analyze_video_ai",
         "用视觉模型分析视频内容", note="需视觉模型 API"),
    Tool("audio_transcribe", "multimodal", "media_processing_tools", "transcribe_audio_whisper",
         "用 Whisper 将音频转写为文本", note="需安装 whisper"),
    Tool("audio_metadata", "multimodal", "media_processing_tools", "extract_audio_metadata",
         "读取音频文件元数据"),
    Tool("audio_trim", "multimodal", "media_processing_tools", "trim_audio",
         "裁剪音频到指定时间区间"),
    Tool("youtube_transcript", "multimodal", "multimodal_tools", "extract_youtube_transcript",
         "提取 YouTube 视频字幕", online=True),
    Tool("youtube_download", "multimodal", "multimodal_tools", "download_youtube_video",
         "下载 YouTube 视频", online=True),

    # ---- 文件系统 ----
    Tool("file_reader", "filesystem", "filesystem_tools", "read_file",
         "读取文件内容（支持编码与截断）"),
    Tool("grep", "filesystem", "filesystem_tools", "grep_search",
         "在目录中按正则搜索文件内容"),
    Tool("text_summarizer", "filesystem", "filesystem_tools", "summarize_text",
         "对长文本做摘要（抽取式/截断，占位实现）"),

    # ---- 公开数据源 ----
    Tool("weather", "public", "public_data_tools", "get_weather",
         "查询天气（Open-Meteo，免费无 Key）", online=True),
    Tool("stock_price", "public", "public_data_tools", "get_stock_price",
         "查询股票行情", online=True),
    Tool("crypto_price", "public", "public_data_tools", "get_crypto_price",
         "查询加密货币价格（CoinGecko，免费无 Key）", online=True),
    Tool("currency_converter", "public", "public_data_tools", "convert_currency",
         "货币汇率换算（免费无 Key）", online=True),
    Tool("wikipedia_search", "public", "public_data_tools", "search_wikipedia",
         "搜索 Wikipedia 并返回摘要", online=True),
    Tool("arxiv_search", "public", "public_data_tools", "search_arxiv",
         "搜索 ArXiv 学术论文", online=True),
    Tool("wayback_search", "public", "public_data_tools", "search_wayback",
         "在 Wayback Machine 查历史快照", online=True),
    Tool("xquik_search_posts", "public", "xquik_tools", "search_x_posts",
         "通过 Xquik 搜索 X 帖子并返回游标", online=True,
         note="需 XQUIK_API_KEY 与有效订阅；按返回帖子计费"),
    Tool("location_search", "public", "public_data_tools", "search_location",
         "地名/地点地理编码（Nominatim，免费无 Key）", online=True),
    Tool("poi_search", "public", "public_data_tools", "search_poi",
         "查询坐标附近的兴趣点（Overpass，免费无 Key）", online=True),
    Tool("yfinance_quote", "public", "yahoo_finance_tools", "get_stock_quote",
         "Yahoo Finance 实时报价", online=True),
    Tool("yfinance_historical", "public", "yahoo_finance_tools", "get_historical_data",
         "Yahoo Finance 历史行情", online=True),
    Tool("yfinance_company_info", "public", "yahoo_finance_tools", "get_company_info",
         "Yahoo Finance 公司资料", online=True),
    Tool("yfinance_financials", "public", "yahoo_finance_tools", "get_financial_statements",
         "Yahoo Finance 财务报表", online=True),
    Tool("pubchem_search", "public", "pubchem_tools", "search_compounds",
         "在 PubChem 搜索化合物", online=True),
    Tool("pubchem_properties", "public", "pubchem_tools", "get_compound_properties",
         "获取 PubChem 化合物属性", online=True),
    Tool("pubchem_synonyms", "public", "pubchem_tools", "get_compound_synonyms",
         "获取 PubChem 化合物别名", online=True),
    Tool("pubchem_similar", "public", "pubchem_tools", "search_similar_compounds",
         "搜索结构相似的化合物", online=True),
    Tool("wiki_article_full", "public", "wiki_enhanced", "get_article_content",
         "获取 Wikipedia 条目全文", online=True),
    Tool("wiki_article_categories", "public", "wiki_enhanced", "get_article_categories",
         "获取 Wikipedia 条目分类", online=True),
    Tool("wiki_article_links", "public", "wiki_enhanced", "get_article_links",
         "获取 Wikipedia 条目中的链接", online=True),
    Tool("wiki_article_history", "public", "wiki_enhanced", "get_article_history",
         "获取 Wikipedia 条目历史版本", online=True),
    Tool("arxiv_paper_details", "public", "arxiv_enhanced", "get_paper_details",
         "获取 ArXiv 论文详情", online=True),
    Tool("arxiv_download", "public", "arxiv_enhanced", "download_paper",
         "下载 ArXiv 论文 PDF", online=True),
    Tool("arxiv_categories", "public", "arxiv_enhanced", "get_arxiv_categories",
         "列出 ArXiv 学科分类", online=True),
    Tool("wayback_archived_content", "public", "wayback_enhanced", "get_archived_content",
         "获取 Wayback 存档页面内容", online=True),

    # ---- 私有数据源 ----
    Tool("calendar_events", "private", "private_data_tools", "get_calendar_events",
         "读取 Google 日历事件", online=True, note="需 Google OAuth 授权"),
    Tool("notion_search", "private", "private_data_tools", "search_notion",
         "搜索 Notion 工作区", online=True, note="需 NOTION_API_KEY"),
]

TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# ---------------------------------------------------------------------------
# 调用辅助
# ---------------------------------------------------------------------------
def _load_callable(tool: Tool):
    """惰性导入并返回工具对应的异步函数。"""
    module = importlib.import_module(tool.module)
    return getattr(module, tool.func)


def _coerce(value: str, annotation):
    """把命令行传入的字符串按函数注解转换成合适的类型。"""
    # 解开 Optional[X] / X | None
    origin = typing.get_origin(annotation)
    if origin is typing.Union or (origin is not None and str(origin) == "<class 'types.UnionType'>"):
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        annotation = args[0] if args else str
        origin = typing.get_origin(annotation)

    if annotation is bool:
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    if annotation is int:
        return int(value)
    if annotation is float:
        return float(value)
    if annotation in (list, dict) or origin in (list, dict):
        return json.loads(value)
    return value


def _parse_kwargs(func, pairs: list[str]) -> dict:
    """把 key=value 列表解析成传给工具函数的关键字参数。"""
    sig = inspect.signature(func)
    kwargs = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"参数必须是 key=value 形式：{pair!r}")
        key, _, raw = pair.partition("=")
        key = key.strip()
        if key not in sig.parameters:
            valid = ", ".join(sig.parameters)
            raise ValueError(f"未知参数 {key!r}，可用参数：{valid}")
        kwargs[key] = _coerce(raw, sig.parameters[key].annotation)
    return kwargs


def _unwrap(result):
    """工具返回 TextContent(JSON) 或裸 JSON 字符串，统一解析成 dict。"""
    text = getattr(result, "text", result)
    if isinstance(text, (dict, list)):
        return text
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"success": True, "message": text, "metadata": {}}


async def _invoke(tool: Tool, kwargs: dict) -> dict:
    func = _load_callable(tool)
    result = await func(**kwargs)
    return _unwrap(result)


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------
def cmd_list(args) -> int:
    print("\n感知工具 MCP 服务器 —— 工具清单（共 {} 个）".format(len(TOOLS)))
    print("=" * 72)
    cats = [args.category] if args.category else list(CATEGORIES)
    for cat in cats:
        tools = [t for t in TOOLS if t.category == cat]
        if not tools:
            continue
        print(f"\n【{CATEGORIES[cat]}】({len(tools)} 个)")
        print("-" * 72)
        for t in tools:
            flags = []
            if t.online:
                flags.append("联网")
            if t.note:
                flags.append(t.note)
            tag = f"  [{'；'.join(flags)}]" if flags else ""
            print(f"  {t.name:<26} {t.desc}{tag}")
    print("\n提示：`python cli.py info <tool>` 查看参数；`python cli.py run <tool> k=v` 调用。\n")
    return 0


def cmd_info(args) -> int:
    tool = TOOLS_BY_NAME.get(args.tool)
    if tool is None:
        print(f"未找到工具：{args.tool}。用 `python cli.py list` 查看全部。", file=sys.stderr)
        return 1
    try:
        func = _load_callable(tool)
    except Exception as e:
        print(f"工具 {tool.name} 所在模块导入失败（可能缺少可选依赖）：{e}", file=sys.stderr)
        return 1
    sig = inspect.signature(func)
    print(f"\n工具：{tool.name}   分类：{CATEGORIES[tool.category]}")
    print(f"描述：{tool.desc}")
    print(f"实现：src/{tool.module}.py :: {tool.func}()")
    if tool.online:
        print("需要联网：是")
    if tool.note:
        print(f"说明：{tool.note}")
    print("\n参数：")
    for name, p in sig.parameters.items():
        ann = "" if p.annotation is inspect.Parameter.empty else f": {p.annotation}"
        default = "" if p.default is inspect.Parameter.empty else f" = {p.default!r}"
        print(f"  {name}{ann}{default}")
    print(f"\n示例：python cli.py run {tool.name} " +
          " ".join(f"{n}=..." for n, p in sig.parameters.items()
                   if p.default is inspect.Parameter.empty) + "\n")
    return 0


def cmd_run(args) -> int:
    tool = TOOLS_BY_NAME.get(args.tool)
    if tool is None:
        print(f"未找到工具：{args.tool}。用 `python cli.py list` 查看全部。", file=sys.stderr)
        return 1
    try:
        func = _load_callable(tool)
    except Exception as e:
        print(f"工具 {tool.name} 所在模块导入失败（可能缺少可选依赖）：{e}", file=sys.stderr)
        return 1
    try:
        kwargs = _parse_kwargs(func, args.params)
    except Exception as e:
        print(f"参数错误：{e}", file=sys.stderr)
        return 1

    print(f"调用工具 {tool.name} ...", file=sys.stderr)
    try:
        data = asyncio.run(_invoke(tool, kwargs))
    except Exception as e:
        print(f"调用失败：{type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data.get("success", True) else 2


# ---------------------------------------------------------------------------
# 端到端演示：一个「本地笔记 + 外部资料」研究助手 Agent 的感知流程
# ---------------------------------------------------------------------------
def _header(title: str) -> None:
    print("\n" + "─" * 72)
    print(f"▶ {title}")
    print("─" * 72)


async def _demo(offline: bool) -> None:
    from search_tools import search_web, search_knowledge_base
    from filesystem_tools import grep_search, read_file
    from public_data_tools import convert_currency, search_wikipedia
    from multimodal_tools import read_webpage

    # 各工具内部会用 logging.error 打印完整堆栈；演示时抬高阈值，让每步只显示
    # CLI 自己组织的干净状态行（真实错误仍以友好提示呈现）。
    logging.getLogger().setLevel(logging.CRITICAL)

    print("\n" + "=" * 72)
    print("感知工具端到端演示")
    print("场景：一个研究助手 Agent 需要「先看本地资料、再补充外部信息」")
    print("      本演示串联五类感知工具，展示 Agent 如何『感知世界』" +
          ("（离线模式：跳过联网步骤）" if offline else ""))
    print("=" * 72)

    # 准备一个临时本地知识库，避免污染仓库
    tmp = Path(tempfile.mkdtemp(prefix="perception_demo_"))
    (tmp / "mcp_notes.md").write_text(
        "# MCP 调研笔记\n\n"
        "Model Context Protocol (MCP) 是一套开放协议，用于在 Agent 与工具/数据源之间\n"
        "标准化上下文交换。感知工具（如 web_search、read_file）是 Agent 获取信息的感官。\n"
        "关键设计：粒度权衡、输出信息量控制、上下文感知压缩。\n",
        encoding="utf-8",
    )
    (tmp / "budget.md").write_text(
        "# 预算\n\n本次调研的云资源预算为 200 USD，需要换算成人民币报销。\n",
        encoding="utf-8",
    )

    # 1) 文件系统感知：在本地代码库里定位实现
    _header("[1/5] 文件系统感知：grep 定位 + read_file 精读（离线可用）")
    data = _unwrap(await grep_search("ActionResponse", str(SRC_DIR),
                                     file_pattern="*.py", max_results=5))
    if data.get("success"):
        msg = data["message"]
        print(f"  grep 'ActionResponse' 命中 {msg['total_found']} 处，示例：")
        for hit in msg["results"][:3]:
            print(f"    - {hit['file']}:{hit['line_number']}")
    base_py = _unwrap(await read_file(str(SRC_DIR / "base.py"), max_length=200))
    if base_py.get("success"):
        head = base_py["message"]["content"].strip().splitlines()[0]
        print(f"  read_file base.py 首行：{head}")

    # 2) 搜索感知：知识库检索（离线）+ 网络搜索（联网）
    _header("[2/5] 搜索感知：本地知识库检索（离线）+ 网络搜索（联网）")
    kb = _unwrap(await search_knowledge_base("MCP", str(tmp), top_k=3))
    if kb.get("success"):
        print(f"  知识库检索 'MCP' 命中 {kb['message']['total_found']} 个文件：")
        for r in kb["message"]["results"]:
            print(f"    - {r['file']}（相关度 {r['relevance']}）")
    if offline:
        print("  网络搜索：已跳过（离线模式）")
    else:
        try:
            web = _unwrap(await search_web("Model Context Protocol", num_results=3))
            if web.get("success") and web["message"]["results"]:
                print(f"  web_search 返回 {web['message']['count']} 条结果，首条：")
                top = web["message"]["results"][0]
                print(f"    - {top['title']}\n      {top['url']}")
            else:
                print("  web_search 未返回结果（可能被限流）")
        except Exception as e:
            print(f"  web_search 失败（需要网络）：{e}")

    # 3) 公开数据源感知：汇率换算（把预算 200 USD 换成 CNY）
    _header("[3/5] 公开数据源感知：汇率换算 + Wikipedia 摘要（联网）")
    if offline:
        print("  已跳过（离线模式）")
    else:
        try:
            fx = _unwrap(await convert_currency(200, "USD", "CNY"))
            if fx.get("success"):
                m = fx["message"]
                print(f"  预算换算：200 USD ≈ {m['converted_amount']:.2f} CNY"
                      f"（汇率 {m.get('exchange_rate')}）")
        except Exception as e:
            print(f"  汇率换算失败（需要网络）：{e}")
        try:
            wiki = _unwrap(await search_wikipedia("Model Context Protocol", sentences=2))
            if wiki.get("success"):
                print(f"  Wikipedia：{wiki['message']['title']}")
                print(f"    {wiki['message']['summary'][:120]}...")
            else:
                print("  Wikipedia 未返回结果（可能被限流），Agent 可改用其它来源")
        except Exception as e:
            print(f"  Wikipedia 查询失败（需要网络）：{e}")

    # 4) 多模态理解：读取网页正文
    _header("[4/5] 多模态理解：抓取网页正文（联网）")
    if offline:
        print("  已跳过（离线模式）")
    else:
        try:
            page = _unwrap(await read_webpage("https://example.com", extract_text=True))
            if page.get("success"):
                m = page["message"]
                print(f"  网页标题：{m.get('title')}；正文长度：{m.get('text_length', 0)} 字符")
        except Exception as e:
            print(f"  网页抓取失败（需要网络）：{e}")

    # 5) 私有数据源：需要授权
    _header("[5/5] 私有数据源感知：日历 / Notion（需授权）")
    print("  calendar_events 需 Google OAuth 授权，notion_search 需 NOTION_API_KEY。")
    print("  未配置时工具会返回结构化的失败信息，Agent 可据此提示用户去授权。")

    print("\n" + "=" * 72)
    print("演示完成。要点：感知工具是 Agent 的『感官』——只读、可缓存、可并行；")
    print("      设计关键在于粒度权衡与输出信息量控制（详见第四章）。")
    print("=" * 72 + "\n")

    # 清理临时知识库
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()


def cmd_demo(args) -> int:
    asyncio.run(_demo(offline=args.offline))
    return 0


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="感知工具 MCP 服务器的命令行入口（实验 4-2）。\n"
                    "按五类感知场景组织：搜索 / 多模态理解 / 文件系统 / 公开数据源 / 私有数据源。",
        epilog="示例：\n"
               "  python cli.py list                         列出全部感知工具\n"
               "  python cli.py list --category filesystem   只看文件系统类\n"
               "  python cli.py info weather                  查看 weather 的参数\n"
               "  python cli.py run grep pattern=async directory=src   调用 grep\n"
               "  python cli.py run currency_converter amount=100 from_currency=USD to_currency=CNY\n"
               "  python cli.py demo --offline               运行离线端到端演示\n",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<命令>")

    p_list = sub.add_parser("list", help="列出全部感知工具（按五类分组）")
    p_list.add_argument("--category", choices=list(CATEGORIES),
                        help="只列出某一类：" + " / ".join(f"{k}={v}" for k, v in CATEGORIES.items()))
    p_list.set_defaults(handler=cmd_list)

    p_info = sub.add_parser("info", help="查看某个工具的参数签名与示例")
    p_info.add_argument("tool", help="工具名（见 list）")
    p_info.set_defaults(handler=cmd_info)

    p_run = sub.add_parser("run", help="直接调用某个工具并打印 JSON 结果")
    p_run.add_argument("tool", help="工具名（见 list）")
    p_run.add_argument("params", nargs="*", metavar="key=value",
                       help="以 key=value 形式传入的工具参数")
    p_run.set_defaults(handler=cmd_run)

    p_demo = sub.add_parser("demo", help="运行端到端感知场景演示")
    p_demo.add_argument("--offline", action="store_true",
                        help="离线模式：只跑不联网的步骤（文件系统 / 本地知识库）")
    p_demo.set_defaults(handler=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING,
                        format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
