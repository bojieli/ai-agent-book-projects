用户现在需要翻译第五章的内容，也就是上下文工程的第一部分。我需要逐句准确翻译，注意专业术语和代码部分的处理。首先开头是“# Context Engineering [Part 1/8]”，翻译为“# 上下文工程 [第1部分/共8部分]”。然后逐段处理，比如“Context Engineering”翻译为“上下文工程”，代码部分要保留原样。现在开始逐句翻译：

# 上下文工程 [第1部分/共8部分]
## 上下文工程

第1章将上下文定义为智能体在决策时刻的工作信息集。设计和管理该上下文——我们称之为**上下文工程**——是构建有效智能体的核心。在实践中，上下文包括智能体在给定交互中接收的所有信息：对话历史、系统指令、工具定义、检索文档、运行时状态和其他特定任务信息。从第1章介绍的框架视角看，上下文工程实现了框架的“上下文与工具”层的大部分内容：它决定智能体在每个决策点看到的信息以及这些信息的组织方式。良好的上下文设计为模型提供正确的背景、约束和行动接口，使其通用推理能力能有效应用于任务。

![图2-1：上下文窗口组成概览](images/fig2-1.svg)

## 上下文：智能体能力的上限
大型语言模型在标准化基准测试中取得优异成果，但在真实业务场景中往往表现不佳。原因很简单：模型能力是通用的，而具体任务依赖于本地知识，如产品架构、业务规则、操作约束和内部约定。这些信息通常不存在于模型参数中。

设想一位非常有能力的工程师加入新团队。他可能拥有深厚的理论知识和强大的编程能力，但尚不了解产品架构、业务逻辑、技术债务或团队规范。如果关键架构决策分散在个人记忆中且代码库文档匮乏，即使是杰出的工程师也难以快速创造价值。当今的人工智能智能体面临同样的问题。

以编码智能体为例。面对相同指令“帮我修复这个漏洞”，智能体接收的上下文质量决定了它能否完成任务：
- **代码上下文**：代码库结构、模块职责、核心数据结构和编码标准。缺乏此信息，智能体可能生成语法正确但与项目风格或架构不一致的代码。
- **流程要求**：Git分支策略、提交规范、审查流程和CI/CD要求。缺乏此信息，智能体可能直接将未经测试的代码提交到主分支。
- **环境配置**：开发设置、测试数据库连接字符串、阶段部署程序和API密钥管理实践。缺乏此信息，本地运行正常的修复可能在测试环境中立即失败。

这三类——代码、流程和环境——构成智能体有效工作所需的最小上下文。模型固有的能力只是基础；上下文设定了智能体能力的上限。具有良好组织上下文的中等能力模型往往能胜过在上下文不足情况下运行的更强模型。

因此，上下文工程是用当今模型构建有效智能体的核心。这不仅仅是向提示词中添加更多文本的问题。它需要系统地设计、组织并提供模型完成任务所需的背景知识。上下文工程是技术问题，但从根本上说是组织问题。在许多团队中，关键知识仍未明确：架构决策存在于高级工程师的记忆中，业务规则非正式传递，重要上下文埋藏在私人聊天日志中。如果团队自身是不良的信息环境，即使强大的人工智能智能体也会受限。

在远程环境中有效工作的团队通常也为人工智能智能体提供了有效的环境。像Linux内核这样的开源项目就是有启发性的例子：分布在世界各地的开发者维护该项目已超过三十年。这之所以可行，是因为该项目具有透明的、文档驱动的沟通文化。讨论公开，决策记录在案，新人可通过阅读历史了解代码演进。同样的工作风格自然创造了对人工智能友好的环境：信息公开、可检索且结构化。

每次智能体开始任务时，将其视为新的团队成员。有了足够的背景，它能产出高质量工作；缺乏背景，其大部分智能被浪费。因此，构建人工智能原生团队主要是文档工作，而非仅仅部署新工具。

OpenAI研究员翁佳怡清晰地表达了这一点：**“对人类和模型而言，最重要的是上下文。”** 回顾自己的工作，他指出：“我在OpenAI的工作并不难。如果其他人拥有我所有的上下文，他们也能做到。” 同样的原则适用于智能体：智能体能力的上限不仅由模型大小决定，还由每个决策点提供的上下文的完整性和精确性决定。翁佳怡还观察到团队合作中的核心问题是上下文不一致，且人工智能短期内无法取代人类的一个原因是人工智能和人类不共享相同的环境。上下文工程正是解决这个问题：如何系统地向模型提供智能体所需的结构化背景信息。

下一个问题是如何在技术层面将这些上下文信息提供给大语言模型。

## 智能体如何调用大语言模型：API级上下文结构
本节以OpenAI的Chat Completions API为例进行具体说明。Anthropic、谷歌等提供商在细节上有所不同，但它们面向智能体的API遵循类似模式：每次模型调用由结构化对话历史和一组可用工具定义构建。理解这种结构是本章后续讨论的上下文工程技术的基础。

### 四种消息角色
在Chat Completions风格的API中，核心输入是**消息列表**，通常命名为`messages`。每条消息有一个`role`字段，告诉模型如何解释消息及其来源：
- **system**：开发者编写的指令，定义智能体的身份、行为、约束和工作流。模型将其视为高优先级指令。在大多数对话中，系统消息在消息列表开头出现一次。
- **user**：最终用户的输入，代表智能体需要处理的请求。
- **assistant**：之前的模型输出，包括自然语言回复和工具调用请求。在多轮交互中，这些消息包含在后续请求中，以便无状态的下一次模型调用能访问之前的轨迹。
- **tool**：智能体框架执行工具后返回的结果。每个工具结果通过`tool_call_id`与相应的工具调用关联，使模型能将每个结果与其生成的请求关联起来。

工具定义不是消息。它们在单独的`tools`字段中提供，声明模型可用的工具并指定每个工具接受的参数。

### 单轮请求：最简单的API调用
![图2-2：单轮API调用的请求与响应结构](images/fig2-2.svg)

从最简单的情况开始：没有工具调用的单轮请求。用户问“你好，你是谁？”。示例使用本地部署的Qwen3-0.6B模型，与本节后面的本地大语言模型部署实验相连。示例中的时间戳仅用于演示，与本书时间线无关。

```javascript
// ═══ 智能体框架构造的请求 ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 开发者编写
      "content": "You are a helpful coding assistant. Follow user instructions."
    },
    {
      "role": "user",                              // ← 用户输入
      "content": "Hello, who are you?"
    }
  ]
}
```

```javascript
// ═══ API返回的响应 ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": "Hi! I'm a coding assistant. I can help you write code, debug issues, and explain technical concepts. How can I help?"
    }
  }]
}
```

此请求仅包含两条消息：一条包含开发者编写规则的系统消息和一条包含用户输入的用户消息。模型返回助手消息作为回复。这是最基本的大语言模型API交互模式：**每次调用无状态，因此请求的消息列表必须包含模型所需的所有信息**。

### 带工具调用的多轮交互：智能体的核心循环
真实的智能体工作流通常比单轮问答复杂。当用户问“温哥华当前的时间和天气是什么？”时，模型需要访问动态外部信息：当前时间和最新天气。以下示例逐步展示智能体框架与模型之间的每次交互。

![图2-3：两次工具调用的完整交互序列](images/fig2-3.svg)

**第一次API调用——智能体框架发送初始请求：**

```javascript
// ═══ 智能体框架构造的请求（第1次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 开发者编写
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← 用户输入
      "content": "What's the current time and weather in Vancouver?"
    }
  ],
  "tools": [                                       // ← 开发者定义的工具
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Get the current date and time in a specific timezone",
        "parameters": {
          "type": "object",
          "properties": {
            "timezone": { "type": "string", "description": "Timezone name, e.g. America/Vancouver" }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a specific city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": { "type": "string", "description": "City name" },
            "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
          }
        }
      }
    }
  ]
}
```

**模型返回工具调用请求（非最终回复）：**

```javascript
// ═══ API返回的响应（模型决定调用工具） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": null,                             // 无文本响应
      "tool_calls": [                              // 模型请求两次工具调用
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "get_current_time",
            "arguments": "{\"timezone\": \"America/Vancouver\"}"
          }
        },
        {
          "id": "call_def456",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}"
          }
        }
      ]
    }
  }]
}
```

模型尚未回答用户的问题。相反，它返回两个**工具调用请求**：一个用于当前时间，一个用于天气。由于这些请求是独立的，智能体框架可以并行执行它们。**模型发出调用请求；智能体框架执行实际调用。** 这种责任划分是智能体架构的核心：模型决定调用哪个工具及传递什么参数，而框架调用API、运行代码并返回结果。

**智能体框架执行工具，然后发起第二次API调用：**

在接收模型的工具调用请求后，智能体框架执行两个工具（例如，调用时间API和天气API），然后将**完整的对话历史连同工具执行结果**发送回模型：

```javascript
// ═══ 智能体框架构造的请求（第2次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 与第1次调用相同
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← 与第1次调用相同
      "content": "What's the current time and weather in Vancouver?"
    },
    {
      "role": "assistant",                         // ← 第1次调用的模型输出，逐字包含
      "content": null,
      "tool_calls": [
        { "id": "call_abc123", "function": { "name": "get_current_time", "arguments": "{\"timezone\": \"America/Vancouver\"}" } },
        { "id": "call_def456", "function": { "name": "get_weather", "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}" } }
      ]
    },
    {
      "role": "tool",                              // ← 智能体框架生成（工具执行结果）
      "tool_call_id": "call_abc123",
      "content": "{\"timezone\": \"America/Vancouver\", \"datetime\": \"2025-09-13T05:18:47\", \"day_of_week\": \"Saturday\"}"
    },
    {
      "role": "tool",                              // ← 智能体框架生成（工具执行结果）
      "tool_call_id": "call_def456",
      "content": "{\"city\": \"Vancouver\", \"temperature\": 13.2, \"unit\": \"celsius\", \"conditions\": \"clear\", \"humidity\": 93}"
    }
  ],
  "tools": [ ... ]                                 // ← 与上述相同的工具定义，省略
}
```

这里有三个关键细节：
1. **第二次请求包含第一次请求的完整对话历史** — 系统消息、用户消息、包含工具调用的助手消息和新添加的工具结果。这说明了API的无状态性质：智能体框架必须在每个请求中包含相关历史。
2. **第一次助手消息逐字插入消息列表** — 这使下一次模型调用能访问前一次调用中做出的工具调用决策。
3. **工具消息通过`tool_call_id`与相应的工具调用关联** — 这告诉模型哪个结果属于哪个请求的调用。

**模型根据工具结果生成最终响应：**

```javascript
// ═══ API返回的响应（最终回复） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": "It's currently 5:18 AM on Saturday, September 13, 2025 in Vancouver.\n\nWeather: 13.2°C with clear skies and 93% humidity. It's quite cool this morning - you might want to grab a jacket."
    }
  }]
}
```

这次，模型不返回`tool_calls`；它返回文本响应，因为工具结果提供了足够的信息来回答用户的问题。如果需要更多信息（例如，用户问“东京呢？”），模型可以再次返回`tool_calls`，智能体框架重复相同的循环：执行工具、发送结果、再次调用模型。**这个“请求→工具调用→执行→返回结果→下一次请求”循环是第1章介绍的ReAct循环的API级实现。**

### 用代码实现智能体的核心循环
现在JSON结构清晰，我们可以在Python中连接上述步骤。以下是围绕单个循环构建的最小智能体实现：

```python
from openai import OpenAI

client = OpenAI()

# ── 工具定义 ──
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in a specific timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone name, e.g. America/Vancouver"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a specific city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
            },
        },
    },
]

# ── 工具执行函数（带固定结果的存根；实际实现必须解析JSON `arguments`并调用实际API） ──
def execute_tool(name, arguments):
    if name == "get_current_time":
        return '{"datetime": "2025-09-13T05:18:47", "day_of_week": "Saturday"}'
    elif name == "get_weather":
        return '{"temperature": 13.2, "unit": "celsius", "conditions": "clear", "humidity": 93}'

# ── 初始消息列表 ──
messages = [
    {"role": "system", "content": "You are a helpful assistant. Use tools to get real-time information when needed."},
    {"role": "user", "content": "What's the current time and weather in Vancouver?"},
]

# ── 智能体核心循环 ──
# 生产代码在此处需要max_iterations限制：如本章后面所述，智能体可能永远重复相同的工具调用
while True:
    response = client.chat.completions.create(
        model="Qwen3-0.6B", messages=messages, tools=tools
    )
    assistant_message = response.choices[0].message

    # 将模型的响应追加到消息列表（无论是文本还是工具调用）
    messages.append(assistant_message)

    # 如果没有请求工具调用，模型已生成最终响应
    if not assistant_message.tool_calls:
        print(assistant_message.content)
        break

    # 执行模型请求的每个工具，将结果追加到消息列表
    for tool_call in assistant_message.tool_calls:
        result = execute_tool(tool_call.function.name, tool_call.function.arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
    # 返回循环顶部，使用更新后的消息列表再次调用模型
```

循环有一个主要分支：**如果模型返回`tool_calls`，执行工具并继续；否则，输出结果并退出。** 在此过程中，`messages`列表随着每一轮追加模型回复和任何工具执行结果而不断增长。

`messages`列表在各轮中的变化如下：

**初始状态（第一次调用前）：**
```
messages = [
  { role: "system",  content: "You are a helpful assistant..." },     # 开发者编写
  { role: "user",    content: "What's the current time and weather in Vancouver?" },  # 用户输入
]
```

**第一次调用后（模型返回工具调用）：**
```
messages = [
  { role: "system",    content: "..." },
  { role: "user",      content: "What's the current time..." },
  { role: "assistant", tool_calls: [get_current_time, get_weather] },  # + 模型生成
  { role: "tool",      tool_call_id: "call_abc", content: "{time...}" },  # + 框架执行
  { role: "tool",      tool_call_id: "call_def", content: "{weather...}" },  # + 框架执行
]
```</think># 上下文工程 [第1部分/共8部分]
## 上下文工程

第1章将上下文定义为智能体在决策时刻的工作信息集。设计和管理该上下文——我们称之为**上下文工程**——是构建有效智能体的核心。在实践中，上下文包括智能体在给定交互中接收的所有信息：对话历史、系统指令、工具定义、检索文档、运行时状态和其他特定任务信息。从第1章介绍的框架视角看，上下文工程实现了框架的“上下文与工具”层的大部分内容：它决定智能体在每个决策点看到的信息以及这些信息的组织方式。良好的上下文设计为模型提供正确的背景、约束和行动接口，使其通用推理能力能有效应用于任务。

![图2-1：上下文窗口组成概览](images/fig2-1.svg)

## 上下文：智能体能力的上限
大型语言模型在标准化基准测试中取得优异成果，但在真实业务场景中往往表现不佳。原因很简单：模型能力是通用的，而具体任务依赖于本地知识，如产品架构、业务规则、操作约束和内部约定。这些信息通常不存在于模型参数中。

设想一位非常有能力的工程师加入新团队。他可能拥有深厚的理论知识和强大的编程能力，但尚不了解产品架构、业务逻辑、技术债务或团队规范。如果关键架构决策分散在个人记忆中且代码库文档匮乏，即使是杰出的工程师也难以快速创造价值。当今的人工智能智能体面临同样的问题。

以编码智能体为例。面对相同指令“帮我修复这个漏洞”，智能体接收的上下文质量决定了它能否完成任务：
- **代码上下文**：代码库结构、模块职责、核心数据结构和编码标准。缺乏此信息，智能体可能生成语法正确但与项目风格或架构不一致的代码。
- **流程要求**：Git分支策略、提交规范、审查流程和CI/CD要求。缺乏此信息，智能体可能直接将未经测试的代码提交到主分支。
- **环境配置**：开发设置、测试数据库连接字符串、阶段部署程序和API密钥管理实践。缺乏此信息，本地运行正常的修复可能在测试环境中立即失败。

这三类——代码、流程和环境——构成智能体有效工作所需的最小上下文。模型固有的能力只是基础；上下文设定了智能体能力的上限。具有良好组织上下文的中等能力模型往往能胜过在上下文不足情况下运行的更强模型。

因此，上下文工程是用当今模型构建有效智能体的核心。这不仅仅是向提示词中添加更多文本的问题。它需要系统地设计、组织并提供模型完成任务所需的背景知识。上下文工程是技术问题，但从根本上说是组织问题。在许多团队中，关键知识仍未明确：架构决策存在于高级工程师的记忆中，业务规则非正式传递，重要上下文埋藏在私人聊天日志中。如果团队自身是不良的信息环境，即使强大的人工智能智能体也会受限。

在远程环境中有效工作的团队通常也为人工智能智能体提供了有效的环境。像Linux内核这样的开源项目就是有启发性的例子：分布在世界各地的开发者维护该项目已超过三十年。这之所以可行，是因为该项目具有透明的、文档驱动的沟通文化。讨论公开，决策记录在案，新人可通过阅读历史了解代码演进。同样的工作风格自然创造了对人工智能友好的环境：信息公开、可检索且结构化。

每次智能体开始任务时，将其视为新的团队成员。有了足够的背景，它能产出高质量工作；缺乏背景，其大部分智能被浪费。因此，构建人工智能原生团队主要是文档工作，而非仅仅部署新工具。

OpenAI研究员翁佳怡清晰地表达了这一点：**“对人类和模型而言，最重要的是上下文。”** 回顾自己的工作，他指出：“我在OpenAI的工作并不难。如果其他人拥有我所有的上下文，他们也能做到。” 同样的原则适用于智能体：智能体能力的上限不仅由模型大小决定，还由每个决策点提供的上下文的完整性和精确性决定。翁佳怡还观察到团队合作中的核心问题是上下文不一致，且人工智能短期内无法取代人类的一个原因是人工智能和人类不共享相同的环境。上下文工程正是解决这个问题：如何系统地向模型提供智能体所需的结构化背景信息。

下一个问题是如何在技术层面将这些上下文信息提供给大语言模型。

## 智能体如何调用大语言模型：API级上下文结构
本节以OpenAI的Chat Completions API为例进行具体说明。Anthropic、谷歌等提供商在细节上有所不同，但它们面向智能体的API遵循类似模式：每次模型调用由结构化对话历史和一组可用工具定义构建。理解这种结构是本章后续讨论的上下文工程技术的基础。

### 四种消息角色
在Chat Completions风格的API中，核心输入是**消息列表**，通常命名为`messages`。每条消息有一个`role`字段，告诉模型如何解释消息及其来源：
- **system**：开发者编写的指令，定义智能体的身份、行为、约束和工作流。模型将其视为高优先级指令。在大多数对话中，系统消息在消息列表开头出现一次。
- **user**：最终用户的输入，代表智能体需要处理的请求。
- **assistant**：之前的模型输出，包括自然语言回复和工具调用请求。在多轮交互中，这些消息包含在后续请求中，以便无状态的下一次模型调用能访问之前的轨迹。
- **tool**：智能体框架执行工具后返回的结果。每个工具结果通过`tool_call_id`与相应的工具调用关联，使模型能将每个结果与其生成的请求关联起来。

工具定义不是消息。它们在单独的`tools`字段中提供，声明模型可用的工具并指定每个工具接受的参数。

### 单轮请求：最简单的API调用
![图2-2：单轮API调用的请求与响应结构](images/fig2-2.svg)

从最简单的情况开始：没有工具调用的单轮请求。用户问“你好，你是谁？”。示例使用本地部署的Qwen3-0.6B模型，与本节后面的本地大语言模型部署实验相连。示例中的时间戳仅用于演示，与本书时间线无关。

```javascript
// ═══ 智能体框架构造的请求 ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 开发者编写
      "content": "You are a helpful coding assistant. Follow user instructions."
    },
    {
      "role": "user",                              // ← 用户输入
      "content": "Hello, who are you?"
    }
  ]
}
```

```javascript
// ═══ API返回的响应 ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": "Hi! I'm a coding assistant. I can help you write code, debug issues, and explain technical concepts. How can I help?"
    }
  }]
}
```

此请求仅包含两条消息：一条包含开发者编写规则的系统消息和一条包含用户输入的用户消息。模型返回助手消息作为回复。这是最基本的大语言模型API交互模式：**每次调用无状态，因此请求的消息列表必须包含模型所需的所有信息**。

### 带工具调用的多轮交互：智能体的核心循环
真实的智能体工作流通常比单轮问答复杂。当用户问“温哥华当前的时间和天气是什么？”时，模型需要访问动态外部信息：当前时间和最新天气。以下示例逐步展示智能体框架与模型之间的每次交互。

![图2-3：两次工具调用的完整交互序列](images/fig2-3.svg)

**第一次API调用——智能体框架发送初始请求：**

```javascript
// ═══ 智能体框架构造的请求（第1次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 开发者编写
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← 用户输入
      "content": "What's the current time and weather in Vancouver?"
    }
  ],
  "tools": [                                       // ← 开发者定义的工具
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Get the current date and time in a specific timezone",
        "parameters": {
          "type": "object",
          "properties": {
            "timezone": { "type": "string", "description": "Timezone name, e.g. America/Vancouver" }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a specific city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": { "type": "string", "description": "City name" },
            "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
          }
        }
      }
    }
  ]
}
```

**模型返回工具调用请求（非最终回复）：**

```javascript
// ═══ API返回的响应（模型决定调用工具） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": null,                             // 无文本响应
      "tool_calls": [                              // 模型请求两次工具调用
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "get_current_time",
            "arguments": "{\"timezone\": \"America/Vancouver\"}"
          }
        },
        {
          "id": "call_def456",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}"
          }
        }
      ]
    }
  }]
}
```

模型尚未回答用户的问题。相反，它返回两个**工具调用请求**：一个用于当前时间，一个用于天气。由于这些请求是独立的，智能体框架可以并行执行它们。**模型发出调用请求；智能体框架执行实际调用。** 这种责任划分是智能体架构的核心：模型决定调用哪个工具及传递什么参数，而框架调用API、运行代码并返回结果。

**智能体框架执行工具，然后发起第二次API调用：**

在接收模型的工具调用请求后，智能体框架执行两个工具（例如，调用时间API和天气API），然后将**完整的对话历史连同工具执行结果**发送回模型：

```javascript
// ═══ 智能体框架构造的请求（第2次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 与第1次调用相同
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← 与第1次调用相同
      "content": "What's the current time and weather in Vancouver?"
    },
    {
      "role": "assistant",                         // ← 第1次调用的模型输出，逐字包含
      "content": null,
      "tool_calls": [
        { "id": "call_abc123", "function": { "name": "get_current_time", "arguments": "{\"timezone\": \"America/Vancouver\"}" } },
        { "id": "call_def456", "function": { "name": "get_weather", "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}" } }
      ]
    },
    {
      "role": "tool",                              // ← 智能体框架生成（工具执行结果）
      "tool_call_id": "call_abc123",
      "content": "{\"timezone\": \"America/Vancouver\", \"datetime\": \"2025-09-13T05:18:47\", \"day_of_week\": \"Saturday\"}"
    },
    {
      "role": "tool",                              // ← 智能体框架生成（工具执行结果）
      "tool_call_id": "call_def456",
      "content": "{\"city\": \"Vancouver\", \"temperature\": 13.2, \"unit\": \"celsius\", \"conditions\": \"clear\", \"humidity\": 93}"
    }
  ],
  "tools": [ ... ]                                 // ← 与上述相同的工具定义，省略
}
```

这里有三个关键细节：
1. **第二次请求包含第一次请求的完整对话历史** — 系统消息、用户消息、包含工具调用的助手消息和新添加的工具结果。这说明了API的无状态性质：智能体框架必须在每个请求中包含相关历史。
2. **第一次助手消息逐字插入消息列表** — 这使下一次模型调用能访问前一次调用中做出的工具调用决策。
3. **工具消息通过`tool_call_id`与相应的工具调用关联** — 这告诉模型哪个结果属于哪个请求的调用。

**模型根据工具结果生成最终响应：**

```javascript
// ═══ API返回的响应（最终回复） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": "It's currently 5:18 AM on Saturday, September 13, 2025 in Vancouver.\n\nWeather: 13.2°C with clear skies and 93% humidity. It's quite cool this morning - you might want to grab a jacket."
    }
  }]
}
```

这次，模型不返回`tool_calls`；它返回文本响应，因为工具结果提供了足够的信息来回答用户的问题。如果需要更多信息（例如，用户问“东京呢？”），模型可以再次返回`tool_calls`，智能体框架重复相同的循环：执行工具、发送结果、再次调用模型。**这个“请求→工具调用→执行→返回结果→下一次请求”循环是第1章介绍的ReAct循环的API级实现。**

### 用代码实现智能体的核心循环
现在JSON结构清晰，我们可以在Python中连接上述步骤。以下是围绕单个循环构建的最小智能体实现：

```python
from openai import OpenAI

client = OpenAI()

# ── 工具定义 ──
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in a specific timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone name, e.g. America/Vancouver"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a specific city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
            },
        },
    },
]

# ── 工具执行函数（带固定结果的存根；实际实现必须解析JSON `arguments`并调用实际API） ──
def execute_tool(name, arguments):
    if name == "get_current_time":
        return '{"datetime": "2025-09-13T05:18:47", "day_of_week": "Saturday"}'
    elif name == "get_weather":
        return '{"temperature": 13.2, "unit": "celsius", "conditions": "clear", "humidity": 93}'

# ── 初始消息列表 ──
messages = [
    {"role": "system", "content": "You are a helpful assistant. Use tools to get real-time information when needed."},
    {"role": "user", "content": "What's the current time and weather in Vancouver?"},
]

# ── 智能体核心循环 ──
# 生产代码在此处需要max_iterations限制：如本章后面所述，智能体可能永远重复相同的工具调用
while True:
    response = client.chat.completions.create(
        model="Qwen3-0.6B", messages=messages, tools=tools
    )
    assistant_message = response.choices[0].message

    # 将模型的响应追加到消息列表（无论是文本还是工具调用）
    messages.append(assistant_message)

    # 如果没有请求工具调用，模型已生成最终响应
    if not assistant_message.tool_calls:
        print(assistant_message.content)
        break

    # 执行模型请求的每个工具，将结果追加到消息列表
    for tool_call in assistant_message.tool_calls:
        result = execute_tool(tool_call.function.name, tool_call.function.arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
    # 返回循环顶部，使用更新后的消息列表再次调用模型
```

循环有一个主要分支：**如果模型返回`tool_calls`，执行工具并继续；否则，输出结果并退出。** 在此过程中，`messages`列表随着每一轮追加模型回复和任何工具执行结果而不断增长。

`messages`列表在各轮中的变化如下：

**初始状态（第一次调用前）：**
```
messages = [
  { role: "system",  content: "You are a helpful assistant..." },     # 开发者编写
  { role: "user",    content: "What's the current time and weather in Vancouver?" },  # 用户输入
]
```

**第一次调用后（模型返回工具调用）：**
```
messages = [
  { role: "system",    content: "..." },
  { role: "user",      content: "What's the current time..." },
  { role: "assistant", tool_calls: [get_current_time, get_weather] },  # + 模型生成
  { role: "tool",      tool_call_id: "call_abc", content: "{time...}" },  # + 框架执行
  { role: "tool",      tool_call_id: "call_def", content: "{weather...}" },  # + 框架执行
]
```