"""
Kimi Web Search Agent
一个基于 Kimi API 的智能搜索 Agent，能够理解用户问题，通过搜索引擎获取信息，并总结出答案。
"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from openai.types.chat.chat_completion import Choice
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


# ReAct 轨迹的步骤类型与展示标签（思考 → 行动 → 观察 → 最终答案）
STEP_LABELS = {
    "thought": ("💭", "思考"),
    "action": ("🔧", "行动"),
    "observation": ("👀", "观察"),
    "answer": ("✅", "最终答案"),
}


def format_trace_step(step: Dict[str, Any], max_len: int = 500) -> str:
    """把一条 ReAct 轨迹步骤渲染成一行可读文本。

    这正是本章强调的“轨迹（trajectory）”——用户消息、模型思考、工具调用、
    工具结果都被清晰地区分开来，让 ReAct 循环“想→做→看”一目了然。
    """
    icon, label = STEP_LABELS.get(step["type"], ("•", step["type"]))
    prefix = f"{icon} [{step.get('iteration', '-')}] {label}"

    if step["type"] == "action":
        args = json.dumps(step.get("args", {}), ensure_ascii=False)
        return f"{prefix}: 调用工具 {step.get('tool')}  参数={args}"

    content = str(step.get("content", "")).strip()
    if len(content) > max_len:
        content = content[:max_len] + f"…（省略 {len(content) - max_len} 字）"
    return f"{prefix}: {content}"


def search_impl(arguments: Dict[str, Any]) -> Any:
    """
    When using the search tool provided by Moonshot AI, you just need to return the arguments as they are,
    without any additional processing logic.
 
    But if you want to use other models and keep the internet search functionality, you just need to modify 
    the implementation here (for example, calling search and fetching web page content), the function signature 
    remains the same and still works.
 
    This ensures maximum compatibility, allowing you to switch between different models without making 
    destructive changes to the code.
    """
    return arguments


# search_and_answer 不抛异常，而是以字符串形式返回失败兜底文案。
# 下列前缀 / 文案是判断“一次搜索是否失败”的唯一来源，供调用方（如
# examples.batch_search）复用，避免把失败响应误判为 success。
SEARCH_ERROR_PREFIX = "搜索过程中出现错误"
MAX_ITERATIONS_MESSAGE = "抱歉，搜索过程超过了最大迭代次数，请稍后重试。"
NO_INFO_MESSAGE = "抱歉，我无法获取足够的信息来回答您的问题。"


def is_failure_answer(answer: str) -> bool:
    """判断 search_and_answer 的返回是否为失败兜底（未能正常作答）。"""
    return (
        answer.startswith(SEARCH_ERROR_PREFIX)
        or answer == MAX_ITERATIONS_MESSAGE
        or answer == NO_INFO_MESSAGE
    )


class WebSearchAgent:
    """
    Web Search Agent - 使用 Kimi API 的内置搜索工具
    
    根据官方文档: https://platform.moonshot.ai/docs/guide/use-web-search
    Kimi 提供了内置的 $web_search 工具
    """
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.moonshot.cn/v1",
                 model: str = "kimi-k3", verbose: bool = False):
        """
        初始化 Agent

        Args:
            api_key: Kimi API key (如果不提供，从环境变量获取)
            base_url: API 基础 URL
            model: 使用的模型名称（默认 kimi-k3）
            verbose: 是否实时打印 ReAct 轨迹（思考/行动/观察）
        """
        # 优先使用传入的 api_key，否则从环境变量获取
        # Moonshot 为主，OpenRouter 为通用兜底（当 MOONSHOT_API_KEY 缺失时启用）
        from config import resolve_llm_backend, Config
        primary_key = api_key or os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
        resolved_key, resolved_base_url, model, self.using_openrouter = \
            resolve_llm_backend(primary_key, base_url, model)
        if self.using_openrouter:
            logger.info(
                f"MOONSHOT_API_KEY 未设置，改用 OpenRouter 兜底（模型: {model}）。"
                "注意：Moonshot 内置 $web_search 工具在 OpenRouter 上不可用，"
                "此模式下模型将仅凭自身知识作答，不做实时联网搜索。"
            )

        self.client = OpenAI(
            api_key=resolved_key,
            base_url=resolved_base_url,
            # 应用配置的搜索超时，避免后端挂起时请求默认阻塞约 10 分钟
            timeout=Config.SEARCH_TIMEOUT,
        )
        self.model = model
        self.verbose = verbose
        self.conversation_history = []
        # ReAct 轨迹：按顺序记录每一步的思考/行动/观察，便于展示与调试
        self.trace: List[Dict[str, Any]] = []
        self.temperature = 0.6
        # 推理模型（Kimi K3）需要充足的输出预算，避免最终答案被截断
        self.max_tokens = 4096

    def _emit(self, step: Dict[str, Any]):
        """记录一条 ReAct 轨迹步骤，并在 verbose 模式下实时打印。"""
        self.trace.append(step)
        if self.verbose:
            print(format_trace_step(step))
        
    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        定义可用的工具
        根据 Kimi 文档，$web_search 是内置工具（仅 Moonshot 支持）。
        经 OpenRouter 兜底时该内置工具不可用，返回空列表以避免 400 错误，
        此时模型仅凭自身知识作答。
        """
        if getattr(self, "using_openrouter", False):
            return []
        return [
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search",
                }
            }
        ]
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示
        """
        return f"""你是 Kimi，一个智能搜索助手。

请按照以下步骤处理：
1. 分析用户问题，识别关键信息需求
2. 使用 $web_search 工具搜索相关信息
3. 如果需要更多信息，可以多次调用搜索工具
4. 综合所有信息，生成准确、全面的答案

注意：
- 搜索时使用精准的关键词
- 优先获取最新、最权威的信息
- 答案要结构清晰，有理有据
"""
    
    def _chat(self, messages: List[Dict[str, Any]]) -> Choice:
        """
        调用 Kimi API 进行对话
        
        Args:
            messages: 消息列表
            
        Returns:
            API 响应的 Choice 对象
        """
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=_reasoning_safe_temperature(self.model, self.temperature),
            # Kimi K3 是推理模型，会先产出较长的 reasoning_content，需要给最终回答
            # 留足输出预算（Moonshot 要求 max_tokens>=2048），否则答案可能被截断为空。
            max_tokens=self.max_tokens,
        )
        tools = self._get_tools()
        if tools:  # OpenRouter 兜底时无内置搜索工具，省略 tools 参数
            kwargs["tools"] = tools
        completion = self.client.chat.completions.create(**kwargs)
        return completion.choices[0]

    def search_and_answer(self, user_question: str, max_iterations: int = 5) -> str:
        """
        执行搜索并生成答案
        
        Args:
            user_question: 用户问题
            max_iterations: 最大搜索迭代次数（防止无限循环）
            
        Returns:
            最终答案
        """
        # 构建系统提示
        system_prompt = self._get_system_prompt()
        
        # 重置对话历史并添加新的系统提示
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        # 重置 ReAct 轨迹
        self.trace = []
        logger.info("开始调用 Kimi 搜索工具...")

        try:
            finish_reason = None
            iteration = 0
            
            # 循环处理，直到获得最终答案或达到最大迭代次数
            while (finish_reason is None or finish_reason == "tool_calls") and iteration < max_iterations:
                iteration += 1
                logger.info(f"迭代 {iteration}/{max_iterations}")
                
                # 调用 Kimi API
                choice = self._chat(self.conversation_history)
                finish_reason = choice.finish_reason
                
                # 捕获模型的思考过程（Kimi K3 等推理模型通过 reasoning_content 暴露思考模式）
                reasoning = getattr(choice.message, "reasoning_content", None)
                if reasoning:
                    self._emit({"iteration": iteration, "type": "thought", "content": reasoning})

                if finish_reason == "tool_calls":
                    # 处理工具调用
                    logger.info(f"模型请求调用 {len(choice.message.tool_calls)} 个工具")

                    # 添加助手的消息（包含工具调用）到历史。
                    # 注意：必须把消息重建为纯 dict，而不是直接塞入 SDK 返回的
                    # pydantic message 对象——后者会附带 reasoning_content / refusal
                    # 等额外字段，回传给 Moonshot 时会触发 "tokenization failed" 400 错误。
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": choice.message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in choice.message.tool_calls
                        ],
                    })

                    # 执行每个工具调用
                    for tool_call in choice.message.tool_calls:
                        tool_call_name = tool_call.function.name
                        try:
                            tool_call_arguments = json.loads(
                                tool_call.function.arguments or "{}"
                            )
                        except json.JSONDecodeError:
                            # Models sometimes emit slightly invalid JSON; match
                            # chapter4 async-agent and keep the ReAct loop alive.
                            tool_call_arguments = {}
                            logger.warning(
                                "工具参数不是合法 JSON，已按空对象继续: %r",
                                tool_call.function.arguments,
                            )

                        logger.info(f"执行工具: {tool_call_name}, 参数: {tool_call_arguments}")
                        # 行动：记录一次工具调用
                        self._emit({"iteration": iteration, "type": "action",
                                    "tool": tool_call_name, "args": tool_call_arguments})

                        if tool_call_name == "$web_search":
                            # 调用搜索实现
                            tool_result = search_impl(tool_call_arguments)
                        else:
                            tool_result = f"Error: unable to find tool by name '{tool_call_name}'"

                        tool_content = json.dumps(tool_result, ensure_ascii=False)
                        # 观察：记录工具返回结果
                        self._emit({"iteration": iteration, "type": "observation",
                                    "tool": tool_call_name, "content": tool_content})
                        # 构建工具响应消息并添加到历史
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call_name,
                            "content": tool_content
                        })
                elif finish_reason == "length":
                    # 输出预算（max_tokens）耗尽导致截断：返回已生成内容并明确标注，
                    # 而不是把半截答案当作完整答案，也不误报“无法获取足够信息”
                    # （content 为空时，思考过程已耗尽整个预算）。
                    partial = (choice.message.content or "").strip()
                    logger.warning("回答因达到 max_tokens 上限被截断 (finish_reason=length)")
                    note = "（注意：回答因达到 max_tokens 上限被截断，请增大 max_tokens 后重试。）"
                    final = f"{partial}\n\n{note}" if partial else note
                    self._emit({"iteration": iteration, "type": "answer", "content": final})
                    # 存入历史时保留截断提示（final），否则 get_conversation_history()
                    # 会丢失截断语义，后续复用历史时可能把不完整回答当作普通回答。
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": final
                    })
                    return final
                else:
                    # 获得最终答案
                    if choice.message.content:
                        answer = choice.message.content
                        logger.info("成功生成答案")
                        self._emit({"iteration": iteration, "type": "answer", "content": answer})

                        # 添加最终答案到历史
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": answer
                        })

                        return answer
            
            # 如果达到最大迭代次数仍未完成
            if iteration >= max_iterations:
                logger.warning(f"达到最大迭代次数 {max_iterations}")
                return MAX_ITERATIONS_MESSAGE

            return NO_INFO_MESSAGE
                
        except Exception as e:
            logger.error(f"{SEARCH_ERROR_PREFIX}: {str(e)}")
            return f"{SEARCH_ERROR_PREFIX}: {str(e)}"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清空")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history

    def get_trace(self) -> List[Dict[str, Any]]:
        """获取上一次 search_and_answer 的 ReAct 轨迹（思考/行动/观察/最终答案）"""
        return self.trace
    
    def set_temperature(self, temperature: float):
        """
        设置温度参数
        
        Args:
            temperature: 温度值 (0.0 - 2.0)
        """
        if 0.0 <= temperature <= 2.0:
            self.temperature = temperature
            logger.info(f"温度设置为: {temperature}")
        else:
            logger.warning(f"无效的温度值: {temperature}，应在 0.0 到 2.0 之间")


def run_offline_demo(question: str = "Moonshot AI 的 Context Caching 是什么技术？",
                     verbose: bool = True) -> Dict[str, Any]:
    """离线演示 ReAct 循环——无需 API Key 或联网。

    本函数**不调用真实搜索**，而是回放一段“示例轨迹”，用来直观展示本章讲的
    “想→做→看→想→做→看”循环：模型先思考，再调用 $web_search 行动，观察结果后
    继续思考，最终综合出答案。轨迹内容仅为教学示例，不代表真实搜索返回。

    Returns:
        包含 question / trace / answer 的字典。
    """
    trace: List[Dict[str, Any]] = [
        {"iteration": 1, "type": "thought",
         "content": "用户想了解 Context Caching。这是 Moonshot 的特性，我需要先搜索官方说明，确认它的定义和作用。"},
        {"iteration": 1, "type": "action", "tool": "$web_search",
         "args": {"query": "Moonshot AI Context Caching 是什么"}},
        {"iteration": 1, "type": "observation", "tool": "$web_search",
         "content": "（示例结果）Context Caching 是一种上下文缓存机制：把重复使用的前缀"
                    "（如长系统提示、文档）缓存在服务端，后续请求命中缓存即可复用，"
                    "从而降低重复计算与费用。"},
        {"iteration": 2, "type": "thought",
         "content": "已知大致定义，但还缺少适用场景。再搜一次它的典型用途以便答得更完整。"},
        {"iteration": 2, "type": "action", "tool": "$web_search",
         "args": {"query": "Context Caching 适用场景 计费"}},
        {"iteration": 2, "type": "observation", "tool": "$web_search",
         "content": "（示例结果）常见于多轮对话、长文档反复问答、固定系统提示等场景；"
                    "命中缓存的 token 通常按更低价格计费，并能显著降低首字延迟。"},
        {"iteration": 3, "type": "answer",
         "content": "Context Caching（上下文缓存）是 Moonshot AI 提供的一种机制：将重复使用的"
                    "上下文前缀缓存在服务端，后续请求复用缓存内容，从而降低重复计算、减少费用、"
                    "并加快响应。它特别适合长系统提示、长文档反复问答、多轮对话等场景。"
                    "（本段来自离线示例轨迹，非真实搜索结果。）"},
    ]

    if verbose:
        for step in trace:
            print(format_trace_step(step))

    answer = next(s["content"] for s in trace if s["type"] == "answer")
    return {"question": question, "trace": trace, "answer": answer}


# 独立运行示例
def main():
    """
    独立运行示例，演示基本用法
    """
    # 设置 API key (确保已设置环境变量 MOONSHOT_API_KEY)
    agent = WebSearchAgent()
    
    # 示例问题
    test_question = "请搜索 Moonshot AI Context Caching 技术，告诉我这是什么。"
    
    print(f"问题: {test_question}")
    print("-" * 60)
    print("搜索中...")
    
    # 获取答案
    answer = agent.search_and_answer(test_question)
    
    print("\n答案:")
    print("-" * 60)
    print(answer)


if __name__ == '__main__':
    main()