"""
配置文件 - 实验 1-4 文生图工作流与原生图像生成的对照

三条外部依赖：
- 改写节点 LLM：Kimi（Moonshot，OpenAI 兼容接口）
- 工作流路线生图工具：DashScope 通义万相（异步任务接口）
  注：实验设计首选 SiliconFlow 托管的 FLUX.1 / Stable Diffusion 系列，
  实测该账号 FLUX/SD 模型已下线（Model disabled）且余额为 0，
  故正式运行改用 DashScope 国际站的 wan2.2-t2i-flash（经典扩散式文生图模型，
  接受 SD 风格提示词与负面提示词）。详见 README「模型选型实录」。
- 原生路线：gemini-3-pro-image（书稿所称 Nano Banana 2）及 OpenAI gpt-image-2
"""

import os
from typing import List

from dotenv import load_dotenv

# 从工作目录向上查找最近的 .env，仓库根目录放一份即可服务所有章节
load_dotenv()


class Config:
    """配置类（所有密钥只从环境变量读取，不写入任何文件）"""

    # ---- 改写节点 LLM：Kimi（Moonshot）----
    KIMI_API_KEY: str = os.getenv("KIMI_API_KEY", "") or os.getenv("MOONSHOT_API_KEY", "")
    KIMI_BASE_URL: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    REWRITE_MODEL: str = os.getenv("REWRITE_MODEL", "kimi-k3")

    # ---- 工作流路线生图工具：DashScope 通义万相（国际站）----
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_BASE_URL: str = os.getenv(
        "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1"
    )
    WANX_MODEL: str = os.getenv("WANX_MODEL", "wan2.2-t2i-flash")
    WANX_SIZE: str = os.getenv("WANX_SIZE", "1024*1024")

    # ---- 工作流路线生图工具（首选，实测不可用）：SiliconFlow ----
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    SILICONFLOW_BASE_URL: str = os.getenv(
        "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"
    )
    SILICONFLOW_IMAGE_MODEL: str = os.getenv(
        "SILICONFLOW_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"
    )

    # ---- 原生路线 A：Gemini 3 Pro Image（书稿所称 Nano Banana 2）----
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_IMAGE_MODEL: str = os.getenv(
        "GEMINI_IMAGE_MODEL", "gemini-3-pro-image"
    )

    # ---- 原生路线 B：OpenAI GPT-Image 2 ----
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    GPT_IMAGE_MODEL: str = os.getenv("GPT_IMAGE_MODEL", "gpt-image-2")

    # ---- 运行参数 ----
    TASK_POLL_INTERVAL: float = float(os.getenv("TASK_POLL_INTERVAL", "5"))
    TASK_POLL_TIMEOUT: float = float(os.getenv("TASK_POLL_TIMEOUT", "180"))

    @classmethod
    def required_env(cls) -> List[str]:
        return ["KIMI_API_KEY", "DASHSCOPE_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"]

    @classmethod
    def validate(cls) -> bool:
        missing = [name for name in cls.required_env() if not getattr(cls, name)]
        if missing:
            print(f"错误: 缺少环境变量: {', '.join(missing)}")
            print("请参考 env.example 配置后重试。")
            return False
        return True
