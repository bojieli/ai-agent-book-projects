<div align="center">

# AWorld Train

*为使用 AWorld 构建的智能体，提供与外部 RL/训练框架对接的、与框架无关的适配层、可运行示例与通用工具*

[![License: MIT][license-image]][license-url]

</div>

---

AWorld Train 为 AWorld 智能体生态系统和各种外部训练框架（如强化学习库）之间提供了一座桥梁。它被设计为框架无关的，可以选择你喜欢的训练环境使用AWorld 智能体。

下图说明了环境和训练集群之间的整体架构和交互：

![架构示意图](../readme_assets/train_env_agent_architecture.png)


## 环境构建

首先，您需要设置智能体工具将要运行的环境。

选择一台机器（也可以是训练机）。

机器规格建议：
- 为进行容量规划，为每个并发工作进程分配大约 **2C4G**。
- 示例：对于8个并发，计划需要 **约16C32G**。

```bash
# 克隆 AWorld 仓库
git clone git@github.com:inclusionAI/AWorld.git
cd /path/to/AWorld
cp ./env/gaia-mcp-server/mcp_servers/.env_template ./env/gaia-mcp-server/mcp_servers/.env
```
编辑 `./env/gaia-mcp-server/mcp_servers/.env` 以配置任何需要身份验证的工具的令牌。

```.env
JINA_API_KEY=<YOUR_JINA_API_KEY>
TAVILY_API_KEY=<YOUR_TAVILY_API_KEY>
GOOGLE_API_KEY=<YOUR_GOOGLE_API_KEY>
GOOGLE_CSE_ID=<YOUR_GOOGLE_CSE_ID>
DATALAB_API_KEY=<YOUR_DATALAB_API_KEY>
E2B_API_KEY=<YOUR_E2B_API_KEY>

MCP_LLM_BASE_URL=<YOUR_MCP_LLM_BASE_URL>
MCP_LLM_MODEL_NAME=<YOUR_MCP_LLM_MODEL_NAME>
MCP_LLM_API_KEY=<YOUR_MCP_LLM_API_KEY>

BROWSERUSE_LLM_BASE_URL=${MCP_LLM_BASE_URL}
BROWSERUSE_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
BROWSERUSE_LLM_API_KEY=${MCP_LLM_API_KEY}
CODE_LLM_BASE_URL=${MCP_LLM_BASE_URL}
CODE_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
CODE_LLM_API_KEY=${MCP_LLM_API_KEY}
THINK_LLM_BASE_URL=${MCP_LLM_BASE_URL}
THINK_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
THINK_LLM_API_KEY=${MCP_LLM_API_KEY}
GUARD_LLM_BASE_URL=${MCP_LLM_BASE_URL}
GUARD_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
GUARD_LLM_API_KEY=${MCP_LLM_API_KEY}
AUDIO_LLM_BASE_URL=${MCP_LLM_BASE_URL}
AUDIO_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
AUDIO_LLM_API_KEY=${MCP_LLM_API_KEY}
IMAGE_LLM_BASE_URL=${MCP_LLM_BASE_URL}
IMAGE_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
IMAGE_LLM_API_KEY=${MCP_LLM_API_KEY}
VIDEO_LLM_BASE_URL=${MCP_LLM_BASE_URL}
VIDEO_LLM_MODEL_NAME=${MCP_LLM_MODEL_NAME}
VIDEO_LLM_API_KEY=${MCP_LLM_API_KEY}
```

接下来，运行启动脚本以在本地启动 MCP 服务器：

```bash
cd /path/to/Aworld
# --docker_dir 参数指定需要构建的env对应docker目录
# e.g., --docker_dir=gaia-mcp-server
python -m env.train_env --docker_dir=gaia-mcp-server
```

MCP 服务器成功启动后，将输出连接详细信息：
```bash
  {
      "ip": "1xx.1xx.x.xx",
      "port": 8000,
      "token": "eyJhbGciOi...rYmQ"
  }
```
您将需要此输出中的 `ip`、`port` 和 `token`，用于下一步在训练机上配置智能体。

有关在 Kubernetes 上部署环境的说明，请参阅 [`../env/README.md`](../env/README.md)。

## 训练集群设置

### 1. 创建智能体或智能体集群
现在，在训练集群机器上，您必须使 MCP 服务凭据对您的智能体可用。使用[环境构建](#环境构建)部分中的 `ip`、`port` 和 `token`，并将它们导出为环境变量或添加到 `.env` 文件中：
```bash
# 导出为环境变量
# 将 <ip>、<port> 和 <token> 替换为环境构建中的 ip、port 和 token
export MCP_SERVER_URL=http://<ip>:<port>/mcp
export MCP_SERVER_TOKEN=<token>

# 或将它们添加到 .env 文件中
# echo "MCP_SERVER_URL=http://<ip>:<port>/mcp" >> .env
# echo "MCP_SERVER_TOKEN=<token>" >> .env
```

然后安装 `aworld` 和强化学习框架：

```bash
# 推荐使用 Python>=3.10。

# 安装 AWorld
pip install aworld

# 安装特定框架的依赖（以 VeRL 为例）
pip install verl==0.5.0
```

配置好连接详细信息后，您可以在所选的训练框架内定义您的智能体。对于 VeRL，这是通过实现一个自定义的 `AgentLoop` 来完成的。

例如，`GaiaAgentLoop` 继承自 `AworldAgentLoop` 并实现了 `build_agents` 方法。

```python
from aworld.agents.llm_agent import Agent
from aworld.config import AgentConfig

from train.adapter.verl.aworld_agent_loop import AworldAgentLoop
from train.adapter.verl.common import get_agent_tool_env_and_servers

class GaiaAgentLoop(AworldAgentLoop):
    def build_agents(self):
        # 获取环境配置和服务器详细信息。
        # 注意：MCP 服务器必须正在运行（环境构建），并且
        # MCP_SERVER_URL/MCP_SERVER_TOKEN 环境变量必须已设置。
        gaia_env_config, gaia_env_servers = get_agent_tool_env_and_servers()

        return Agent(
            conf=AgentConfig(
                # 从服务管理器获取动态的 llm 服务地址。
                # llm 服务是在 VeRL 中启动的。
                llm_base_url=self.get_llm_server_address(),
                llm_model_name=self.get_llm_server_model_name(),
            ),
            name="gaia_super_agent",
            system_prompt="你的系统提示",

            # 智能体的 MCP 工具配置
            mcp_config=gaia_env_config,
            mcp_servers=gaia_env_servers,
        )
```

### 2. 运行训练
在运行训练之前，请在 `agent.yaml` 中指定您的自定义 `AgentLoop`：

```yaml
# 在 agent.yaml 中
- name: gaia_agent
  _target_: train.examples.train_gaia_with_aworld_verl.custom_agent_loop.GaiaAgentLoop
```

最后，运行训练脚本。该脚本通常是基于 VeRL 示例的 `run.sh` 文件。
```bash
bash run.sh
```
此脚本处理由 VeRL 编排的AgentLoop、奖励计算函数和训练流程。
有关 `run.sh` 中的参数设置，请参阅 [VeRL 文档](https://verl.readthedocs.io/en/latest/examples/config.html)。

一个完整的、可运行的示例，包括为 `GaiaAgentLoop` 定制的 `run.sh` 脚本，可在 [`./examples/train_gaia_with_aworld_verl/`](./examples/train_gaia_with_aworld_verl/) 中找到。

## 进阶教程

### 如何创建复杂的多智能体集群 (Swarm)
除了单个智能体，您还可以训练一个多智能体集群。只需让您的 `build_agents` 方法（或等效的设置函数）返回一个 `Swarm` 对象而不是单个 `Agent` 对象即可。AWorld 和训练适配器将处理剩下的部分。

```python
# 在自定义的AgentLoop中
def build_agents(self, ...) -> Union[Agent, Swarm]:
    # ... 创建多个agent
    agent_to_be_train = Agent(
      conf=AgentConfig(
          # 对于要训练的agent，llm_base_url 和 llm_model_name 是从 VeRL 启动的服务中获取的
          llm_base_url=self.get_llm_server_address(),
          llm_model_name=self.get_llm_server_model_name(),
      ),
    )

    plan_agent = Agent(
      conf=AgentConfig(
          # 提供一个即用型的 OpenAI 兼容的 llm 服务地址、模型名称和 api_key
          llm_base_url="",
          llm_model_name="",
          llm_api_key=""
      ),
    )
    
    exe_agent = Agent(
      conf=AgentConfig(
          # 提供一个即用型的 OpenAI 兼容的 llm 服务地址、模型名称和 api_key
          llm_base_url="",
          llm_model_name="",
          llm_api_key=""
      ),
    )
    
    sum_agent = Agent(
      conf=AgentConfig(
          # 提供一个即用型的 OpenAI 兼容的 llm 服务地址、模型名称和 api_key
          llm_base_url="",
          llm_model_name="",
          llm_api_key=""
      ),
    )

    # 返回由以上定义的智能体组成的Swarm
    return Swarm(
        agent_to_be_train, plan_agent, exe_agent, sum_agent,
        # ... 其他Swarm配置
    )
```

### 如何集成其他训练框架
AWorld Train 被设计为可扩展的。要为新的训练框架（例如 “Swift”）添加支持，通常需要：

1.  **创建新的适配器**：在 `train/adapter/` 目录内，为您的框架创建一个新文件夹（例如 `swift/`）。
2.  **实现核心逻辑**：创建一个主类（例如 `AworldAgentTrainer`），它继承自目标框架的某个基类。这个类将负责：
    *   从框架的环境中接收任务或观察结果。
    *   运行 AWorld 智能体（`Runners.sync_run(input=input, agent=agent)`）以获取动作。
    *   将智能体的响应返回给框架。
    *   处理奖励和更新。
3.  **创建示例**：在 `train/examples/` 目录中添加一个新示例，以演示如何使用新的适配器。

可以参考现有的 `verl` 适配器（`train/adapter/verl/`）作为参考实现。

---

<div align="center">

**AWorld Train** — 让你的 AWorld 智能体快速接入主流训练框架

[license-image]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://opensource.org/licenses/MIT

</div>


