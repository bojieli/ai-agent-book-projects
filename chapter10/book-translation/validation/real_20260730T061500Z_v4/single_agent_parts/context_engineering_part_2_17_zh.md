### 上下文工程[第2/17部分]
```javascript
// ═══ 代理框架构造的请求（第一次调用） ═══
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

**模型返回工具调用请求（不是最终回复）：**

```javascript
// ═══ API返回的响应（模型决定调用工具） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 模型生成
      "content": null,                             // 无文本响应
      "tool_calls": [                              // 模型请求两个工具调用
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

模型还没有回答用户的问题。相反，它返回两个**工具调用请求**：一个用于当前时间，一个用于天气。因为这些请求是独立的，代理框架可以并行执行它们。**模型发出调用请求；代理框架执行实际的调用。** 这种职责分工是代理架构的核心：模型决定调用哪个工具以及传递什么参数，而框架调用API、运行代码并返回结果。

**代理框架执行工具，然后发起第二次API调用：**

在收到模型的工具调用请求后，代理框架执行这两个工具（例如，调用时间API和天气API），然后将**完整的对话历史以及工具执行结果**发送回模型：

```javascript
// ═══ 代理框架构造的请求（第二次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 与第一次调用相同
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← 与第一次调用相同
      "content": "What's the current time and weather in Vancouver?"
    },
    {
      "role": "assistant",                         // ← 第一次调用的模型输出，逐字包含
      "content": null,
      "tool_calls": [
        { "id": "call_abc123", "function": { "name": "get_current_time", "arguments": "{\"timezone\": \"America/Vancouver\"}" } },
        { "id": "call_def456", "function": { "name": "get_weather", "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}" } }
      ]
    },
    {
      "role": "tool",                              // ← 由代理框架生成（工具执行结果）
      "tool_call_id": "call_abc123",
      "content": "{\"timezone\": \"America/Vancouver\", \"datetime\": \"2025-09-13T05:18:47\", \"day_of_week\": \"Saturday\"}"
    },
    {
      "role": "tool",                              // ← 由代理框架生成（工具执行结果）
      "tool_call_id": "call_def456",
      "content": "{\"city\": \"Vancouver\", \"temperature\": 13.2, \"unit\": \"celsius\", \"conditions\": \"clear\", \"humidity\": 93}"
    }
  ],
  "tools": [ ... ]                                 // ← 与上述相同的工具定义，省略
}
```

这里有三个关键细节：

1. **第二次请求包含第一次请求的完整对话历史** — 系统消息、用户消息、包含工具调用的助手消息以及新添加的工具结果。这说明了API的无状态性质：代理框架必须在每个请求中包含相关历史。
2. **第一次助手消息逐字插入消息列表** — 这让下一次模型调用能够访问前一次调用中做出的工具调用决策。
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

这次，模型没有返回`tool_calls`；它返回文本响应，因为工具结果提供了足够的信息来回答用户的问题。如果需要更多信息（例如，用户问“东京呢？”），模型可以再次返回`tool_calls`，代理框架重复相同的循环：执行工具、发送结果并再次调用模型。**这个“请求→工具调用→执行→返回结果→下一次请求”的循环是第1章介绍的ReAct循环的API级实现。**

### 在代码中实现代理的核心循环
现在JSON结构清晰了，我们可以在Python中连接上述步骤。以下是围绕单个循环构建的最小代理实现：

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

# ── 工具执行函数（带有固定结果的存根；实际实现必须解析JSON `arguments`并调用实际API） ──
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

# ── 代理核心循环 ──
# 生产代码需要在此处设置max_iterations限制：如本章后面所述，代理可能永远重复相同的工具调用而陷入困境
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

循环有一个主要分支：**如果模型返回`tool_calls`，执行工具并继续；否则，输出结果并退出。** 在此过程中，`messages`列表随着每一轮追加模型的回复和任何工具执行结果而不断增长。

`messages`列表在各轮之间的变化如下：

**初始状态（第一次调用前）：**
```
messages = [
  { role: "system",  content: "You are a helpful assistant..." },     # 开发者编写
  { role: "user",    content: "What's the current time and weather in Vancouver?" },  # 用户输入
]
```