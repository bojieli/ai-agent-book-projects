import asyncio
import logging
import os
import sys
import traceback
from typing import Union

from browser_use import Agent, BrowserSession
from browser_use.llm import ChatOpenAI
from dotenv import load_dotenv
from fastmcp.server.server import FastMCP
from mcp.types import TextContent
from pydantic import Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

mcp = FastMCP("browseruse-server")

extended_browser_system_prompt = """

# 效率指南
0. 如果用户问句里面有明确的URL地址，可以直接访问
1. 使用包含任务关键术语的特定搜索查询
2. 避免被无关信息分散注意力
3. 如果被付费墙阻挡，尝试使用 archive.org 或类似替代方案
4. 清晰简洁地记录每个重要发现
5. 用最少的浏览步骤精确提取必要信息。

## 输出规则
1、如果任务要求查找相关资料内容，可以返回相关资料内容的总结
2、如果任务要求查询相关下载，那尽量的找出可以下载的链接，返回可以下载的链接(比如github上可以下载的链接一般是：https://raw.githubusercontent.com/，如果是huggingface相关的，要找到对应文件页面里面raw标签里面的地址)，下载的链接需要根据任务选择最匹配的地址，示例：
Example 1:
```json
{
  "url": "https://"
}
```
"""


@mcp.tool(
    description="""Use browser to visit a web page, extract content,
    and optionally download files/images, ...

    Returns a dict with execution trace, answer (extracted content),
    and downloaded file/image paths."""
)
async def complete_browser_task(
    task: str = Field(
        ...,
        description=(
            "任务相关描述"
        ),
    )
)-> Union[str, TextContent]:
    browser_session = BrowserSession(
        # headless=True,  # 关键参数：设置为 True 启用无头模式
        headless=False,  # 关键参数：设置为 True 启用无头模式
    )
    try:
        load_dotenv()
        model = os.environ['LLM_MODEL_NAME']
        base_url = os.environ['LLM_BASE_URL']
        api_key = os.environ['LLM_API_KEY']
        if not model or not base_url or not api_key:
            logging.warning(f"Query failed: LLM_MODEL_NAME, LLM_BASE_URL, LLM_API_KEY parameters incomplete")
            return None
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=float(0.1),
        )
        agent = Agent(
            task=task,
            llm=llm,
            extend_system_message=extended_browser_system_prompt,
            browser_session=browser_session
        )
        final_result = ""
        result = await agent.run()
        logging.info(f"complete_browser_task result: {result}")
        if result and result.history[-1] and result.history[-1].result and result.history[-1].result[0]:
            final_result = result.history[-1].result[0].extracted_content

        return final_result
    except BaseException as e:
        logging.warning(f"complete_browser_task error: {e}")
        return None
    except Exception:
        logging.warning(f"complete_browser_task error: {traceback.format_exc()}")
        return None


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting browseruse-server MCP server!")
    mcp.run(transport="stdio")

