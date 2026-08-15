"""
自我进化 Agent（Alita 式）。

只预定义五个基础工具：
    web_search / read_webpage / code_interpreter / create_tool / search_tools
没有任何领域工具。Agent 必须：
    分析任务 → 识别能力缺口 → web_search 找库/API → read_webpage 读文档
    → code_interpreter 沙箱测试 → create_tool 封装入库 → 用新工具完成任务。
再次遇到同类任务时，应先 search_tools 复用已有工具，而非重新搜索创建。

模型：OpenAI SDK，默认 gpt-5.6-luna，function calling。
可通过 LLM_PROVIDER=openai|moonshot|ark 切换（三者均为 OpenAI 兼容接口）；
若对应 Key 缺失但设置了 OPENROUTER_API_KEY，则自动改走 OpenRouter 兜底。
"""

import json
import os

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import base_tools
from tool_manager import ToolLibrary, normalize_schema

# --------------------------------------------------------------------------- #
# LLM 客户端（OpenAI / Moonshot / ARK 都是 OpenAI 兼容接口）
# --------------------------------------------------------------------------- #
_PROVIDERS = {
    "openai": ("OPENAI_API_KEY", None, "gpt-5.6-luna"),
    "moonshot": ("MOONSHOT_API_KEY", "https://api.moonshot.cn/v1", "kimi-k3"),
    "ark": ("ARK_API_KEY", "https://ark.cn-beijing.volces.com/api/v3", "doubao-seed-1-6-250615"),
}

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _to_openrouter_model(model: str) -> str:
    """把常见模型名映射到 OpenRouter 命名空间。"""
    if not model:
        return "openai/gpt-5.6-luna"
    if "/" in model:
        return model
    if model.startswith("gpt-"):
        return "openai/" + model
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"


def build_client():
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    key_env, base_url, default_model = _PROVIDERS.get(provider, _PROVIDERS["openai"])
    model = os.environ.get("LLM_MODEL", default_model)
    api_key = os.environ.get(key_env)
    # 统一兜底：provider 自己的 Key 缺失，但有 OPENROUTER_API_KEY 时改走 OpenRouter
    if not api_key and os.environ.get("OPENROUTER_API_KEY"):
        client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url=OPENROUTER_BASE_URL)
        return client, _to_openrouter_model(model)
    if not api_key:
        raise RuntimeError(
            f"missing {key_env} in environment (provider={provider})；"
            f"也未设置 OPENROUTER_API_KEY（OpenRouter 可作为统一兜底）。"
        )
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    return client, model


SYSTEM_PROMPT = """你是一个「自我进化」智能体（Alita 式）。你只有五个基础工具：
web_search、read_webpage、code_interpreter、create_tool、search_tools。
你没有任何现成的领域工具（没有查股价、查字幕之类的工具）。你的使命是：为缺失的能力
**构建可复用的工具**，让自己越用越强，而不是每次都手工临时凑一个答案。

必须严格遵守下面的固定流水线：

第 0 步（复用优先）：先调用 **search_tools** 检查工具库里是否已有能完成任务的工具。
    - 如果命中：直接调用那个已封装的工具得到数据并作答。**禁止**再调用 web_search / create_tool
      重新造轮子。这是「工具复用」，务必这样做。
    - 如果没有命中：进入下面第 1-5 步「进化」流程。

进化流程（当工具库没有可用工具时）：
1. 用 web_search 搜索能**编程调用**的**开源 Python 库**。搜索关键词要用「open source python
   library」「python package」这类词，而不是「API」——在线 API 往往要注册 key。很多数据
   （包括金融行情）都有无需 key、pip 安装后直接调用、自动从公开数据源抓取的成熟开源库，
   优先找这类库。
2. 用 read_webpage 阅读候选库的 README / PyPI 页 / 文档，了解安装方式和调用方法。
   read_webpage 只用于「读文档」，不要用它去抓取最终答案数字。
3. 用 code_interpreter 在沙箱里**真实运行代码**验证该库可行（用 pip_install 安装依赖）。
   **强约束**：优先选择「完全无需 API key、pip 安装后即可离线调用」的 Python 库；
   凡是需要注册申请 key（如需要 apikey/token 参数）的在线 API，一律跳过，换免费无 key 的库。
   「验证成功」的唯一标准是：你的测试代码用 print 打印出了**真实的价格数字**（不是占位符、
   不是报错、不是空输出）。只有 print 出真实数据，才算验证通过；绝不编造数据，也不要轻易放弃。
4. 验证成功后，用 create_tool 把它封装成一个**通用、可复用**的标准工具。
   工具必须参数化（例如按 ticker 参数查询任意股票，而不是把某只股票写死），命名要通用
   （如 get_stock_price，而不是 get_nvidia_price），description 用通用描述，方便日后复用命中。
   code 中定义 def run(**kwargs) 并 return 结构化结果。工具内部**必须真正调用**你上一步验证
   通过的那个库来现取数据。
   调用 create_tool 时**务必带上 test_args**（一组示例入参）：系统会用它在注册前真跑一次
   run(**test_args)「存前验证」，只有跑通才准入库——这能挡住跑不通的坏工具污染工具库。
   注意：验证通过后**必须**执行本步 create_tool 再作答，不能跳过封装直接回答。
5. 调用你刚 create_tool 创建的那个工具，拿到**真实数据**来回答用户。

硬性要求（违反即视为失败）：
- 对于「获取实时/结构化数据」类任务，你**不允许**仅凭 read_webpage 抓到的某个网页数字直接作答；
  必须走「找库→测试→封装工具→调用工具」这条路，因为只有这样才能复用且可靠。
- **严禁编造数据**：绝不能在工具代码里写死价格/日期等数字，绝不能用「模拟数据 / 示例数据 /
  mock」。工具必须在运行时通过库真正获取当前数据。如果你还没有用 code_interpreter
  真正 print 出真实数字，就**不许**调用 create_tool。
- 若始终找不到可用的免费库，就如实说明失败原因，也**不要**编造一个数字答案。
- 用中文回答最终结论，并说明数据来源（用了哪个库/工具）。"""


# --------------------------------------------------------------------------- #
# 基础工具的 function-calling schema
# --------------------------------------------------------------------------- #
BASE_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "用 DuckDuckGo 搜索网页，返回标题/URL/摘要。用于寻找开源库或公开 API。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "num_results": {"type": "integer", "description": "返回结果数(1-10)", "default": 6},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "抓取网页并抽取正文文本，用于阅读 README 或 API 文档。",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "网页 URL"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "code_interpreter",
            "description": "在子进程沙箱中执行 Python 代码来验证方案；可用 pip_install 先安装第三方库。返回 stdout/stderr。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "pip_install": {
                        "type": "array", "items": {"type": "string"},
                        "description": "执行前需要 pip 安装的包名列表，可选",
                    },
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_tool",
            "description": "把一个已验证可行的功能封装为标准工具并持久化到工具库。code 中必须定义 def run(**kwargs)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "工具名(合法 Python 标识符)"},
                    "description": {"type": "string", "description": "工具用途描述，供日后检索"},
                    "parameters": {
                        "type": "object",
                        "description": "该工具的参数 JSON Schema (type=object, properties, required)",
                    },
                    "code": {"type": "string", "description": "工具实现，必须包含 def run(**kwargs) 并 return 可 JSON 序列化结果"},
                    "test_args": {
                        "type": "object",
                        "description": "一组用于「存前验证」的示例入参：注册前会用它真跑一次 run(**test_args)，"
                                       "只有成功返回才准入库。强烈建议提供，以挡住跑不通的坏工具。",
                    },
                },
                "required": ["name", "description", "parameters", "code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tools",
            "description": "在工具库中按关键词检索已有工具，用于复用。动手上网前必须先调用它。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "检索关键词，如 'stock price'"}},
                "required": ["query"],
            },
        },
    },
]


class SelfEvolvingAgent:
    def __init__(self, verbose: bool = True, allow_create: bool = True, model: str | None = None):
        self.client, self.model = build_client()
        if model:  # CLI/调用方可覆盖模型名（优先级高于 LLM_MODEL 环境变量）
            self.model = model
        self.library = ToolLibrary()
        self.verbose = verbose
        # 是否允许「自我进化」中的造工具动作。False 时移除 create_tool 能力，
        # 用于对照演示「没有造工具能力时只能复用/无法完成」的差异。
        self.allow_create = allow_create
        self.trajectory = []  # 记录动作轨迹，便于「证明工具复用」
        self._verified_real_data = False  # 本轮任务是否已用 code_interpreter 打印出真实数据
        self._created_tool = False         # 本轮是否创建了工具
        self._used_library_tool = False    # 本轮是否复用了库中已封装的工具
        # 已「解锁」的工具库工具：只有经 search_tools 检索命中（或刚 create_tool 新建）后，
        # 才把它暴露为可调用函数。这样能强制「先 search_tools 复用」的流程，而非绕过检索直接调用。
        self._unlocked = set()

    # ------------------------------------------------------------------ #
    def _tools(self):
        """暴露给模型的工具 = 五个基础工具 + 本轮已解锁（经 search_tools 命中或刚创建）的工具。"""
        base = BASE_TOOL_SCHEMAS
        if not self.allow_create:  # 关闭造工具能力：不把 create_tool 暴露给模型
            base = [s for s in base if s["function"]["name"] != "create_tool"]
        dynamic = []
        for rec in self.library.list_tools():
            if rec["name"] not in self._unlocked:
                continue
            dynamic.append(
                {
                    "type": "function",
                    "function": {
                        "name": rec["name"],
                        "description": "[已封装工具] " + rec["description"],
                        "parameters": normalize_schema(rec["parameters"]),
                    },
                }
            )
        return base + dynamic

    def _log(self, *a):
        if self.verbose:
            print(*a, flush=True)

    # ------------------------------------------------------------------ #
    def _dispatch(self, name: str, args: dict) -> dict:
        """执行一次工具调用，并记录轨迹。"""
        self.trajectory.append(name)
        if name == "web_search":
            return base_tools.web_search(args.get("query", ""), args.get("num_results", 6))
        if name == "read_webpage":
            return base_tools.read_webpage(args.get("url", ""))
        if name == "code_interpreter":
            res = base_tools.code_interpreter(args.get("code", ""), args.get("pip_install"))
            # 记录：跑通且有真实输出，才认为已完成「真实数据验证」
            if res.get("success") and res.get("stdout", "").strip():
                self._verified_real_data = True
            return res
        if name == "create_tool":
            if not self.allow_create:
                return {"success": False, "error": "本次运行禁用了造工具能力（--no-create）。"}
            code = args.get("code", "")
            # 反幻觉守卫 1：必须先用 code_interpreter 打印出真实数据，才允许封装工具
            if not self._verified_real_data:
                return {
                    "success": False,
                    "error": "尚未验证真实数据：请先用 code_interpreter 真正调用库并 print 出"
                             "真实数字，验证通过后再封装工具。不要用未经验证或编造的数据封装工具。",
                }
            # 反幻觉守卫 2：拒绝含「模拟/示例/写死数据」气味的工具代码
            lowered = code.lower()
            if any(k in lowered for k in ("mock", "模拟", "示例数据", "sample data", "fake", "dummy")):
                return {
                    "success": False,
                    "error": "工具代码疑似包含模拟/示例/写死数据。工具必须在运行时通过库真正获取"
                             "数据，请改用真实的库调用后重新提交。",
                }
            res = self.library.create_tool(
                args.get("name", ""), args.get("description", ""),
                args.get("parameters", {}), code, args.get("test_args"),
            )
            if res.get("success"):
                self._created_tool = True
                self._unlocked.add(res["name"])  # 新建后立即解锁，便于本轮直接调用
            return res
        if name == "search_tools":
            res = self.library.search_tools(args.get("query", ""))
            for t in res.get("tools", []):  # 命中的工具解锁为可调用函数（工具复用）
                self._unlocked.add(t["name"])
            return res
        # 否则：调用一个已封装的工具（工具复用）
        if self.library.get_tool(name) is not None:
            self._used_library_tool = True
            return self.library.execute_tool(name, args)
        return {"success": False, "error": f"unknown tool: {name}"}

    # ------------------------------------------------------------------ #
    def run(self, task: str, max_steps: int = 20) -> str:
        self._verified_real_data = False
        self._created_tool = False
        self._used_library_tool = False
        self._unlocked = set()
        nudges = 0  # 已发出的「请先封装工具」提醒次数（限次，避免死循环）
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
        self._log(f"\n{'='*70}\n[任务] {task}\n{'='*70}")

        for step in range(max_steps):
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages,
                tools=self._tools(), tool_choice="auto", temperature=0,
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                # 进化守卫：若已用库验证出真实数据，却既没封装工具、也没复用工具就想直接作答，
                # 强制它先 create_tool 把能力固化下来（这正是「自我进化」的关键动作）。
                if (
                    self._verified_real_data
                    and not self._created_tool
                    and not self._used_library_tool
                    and nudges < 2
                ):
                    nudges += 1
                    self._log("\n[进化守卫] 已验证真实数据但未封装工具，提醒模型先 create_tool。")
                    messages.append(
                        {
                            "role": "user",
                            "content": "你已经用真实数据验证了方案，但还没有把它封装成可复用工具。"
                            "请**先调用 create_tool**（通用命名、按 ticker 参数化、内部真正调用该库），"
                            "然后调用你新建的工具得到真实数据再作答。",
                        }
                    )
                    continue
                self._log(f"\n[最终回答]\n{msg.content}")
                return msg.content or ""

            for tc in msg.tool_calls:
                fname = tc.function.name
                try:
                    fargs = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    fargs = {}
                self._log(f"\n[step {step+1}] 调用工具 -> {fname}  args={_short(fargs)}")
                result = self._dispatch(fname, fargs)
                self._log(f"           结果: {_short(result)}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False, default=str)[:8000],
                    }
                )

        return "(达到最大步数上限)"


def _short(obj, n: int = 240) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + f"...(+{len(s)-n} chars)"
