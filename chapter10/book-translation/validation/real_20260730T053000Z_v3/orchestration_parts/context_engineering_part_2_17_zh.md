### Context Engineering [Part 2/17]

```javascript
// ═══ 由代理框架构造的请求（第一次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 由开发者编写
      "content": "你是一个乐于助人的助手。在需要时使用提供的工具获取实时信息。"
    },
    {
      "role": "user",                              // ← 用户输入
      "content": "温哥华当前的时间和天气是什么？"
    }
  ],
  "tools": [                                       // ← 由开发者定义的工具
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "获取特定时区的当前日期和时间",
        "parameters": {
          "type": "object",
          "properties": {
            "timezone": { "type": "string", "description": "时区名称，例如 America/Vancouver" }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "获取特定城市的当前天气",
        "parameters": {
          "type": "object",
          "properties": {
            "city": { "type": "string", "description": "城市名称" },
            "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
          }
        }
      }
    }
  ]
}
```

**Model returns a tool call request (not a final reply):**

```javascript
// ═══ API返回的响应（模型决定调用工具） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 由模型生成
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

The model does not answer the user's question yet. Instead, it returns two **tool call requests**: one for the current time and one for the weather. Because these requests are independent, the Agent framework can execute them in parallel. **The model issues the call requests; the Agent framework performs the actual execution.** This division of responsibility is central to Agent architecture: the model decides which tool to call and what arguments to pass, while the framework calls APIs, runs code, and returns the results.

**The Agent framework executes the tools and then initiates a second API call:**

After receiving the model's tool call requests, the Agent framework executes the two tools (for example, by calling a time API and a weather API), then sends the **complete conversation history along with the tool execution results** back to the model:

```javascript
// ═══ 由代理框架构造的请求（第二次调用） ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← 与第一次调用相同
      "content": "你是一个乐于助人的助手。在需要时使用提供的工具获取实时信息。"
    },
    {
      "role": "user",                              // ← 与第一次调用相同
      "content": "温哥华当前的时间和天气是什么？"
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

There are three key details here:

1. **The second request includes the full conversation history from the first request** — the system message, the user message, the assistant message containing tool calls, and the newly added tool results. This illustrates the stateless nature of the API: the Agent framework must include the relevant history in every request.
2. **The first assistant message is inserted back into the message list verbatim** — this gives the next model call access to the tool-call decisions made in the previous call.
3. **Tool messages are linked to their corresponding tool calls via `tool_call_id`** — this tells the model which result belongs to which requested call.

**The model generates the final response based on the tool results:**

```javascript
// ═══ API返回的响应（最终回复） ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← 由模型生成
      "content": "2025年9月13日星期六，温哥华当前时间是上午5:18。\n\n天气：13.2°C，晴空，湿度93%。今天早上相当凉爽——你可能需要拿件夹克。"
    }
  }]
}
```

This time, the model does not return `tool_calls`; it returns a text response because the tool results provide enough information to answer the user's question. If more information is needed (for example, if the user asks "What about Tokyo?"), the model can再次返回`tool_calls`，代理框架重复相同的循环：执行工具、发送结果并再次调用模型。**这个“请求→工具调用→执行→返回结果→下一个请求”循环是第1章中介绍的ReAct循环的API级实现。**

### Implementing the Agent's Core Loop in Code

Now that the JSON structure is clear, we can connect the steps above in Python. The following is a minimal Agent implementation built around a single loop:

```python
from openai import OpenAI

client = OpenAI()

# ── 工具定义 ──
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取特定时区的当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "时区名称，例如 America/Vancouver"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取特定城市的当前天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
            },
        },
    },
]

# ── 工具执行函数（带有固定结果的存根；实际实现必须解析JSON参数并调用实际API） ──
def execute_tool(name, arguments):
    if name == "get_current_time":
        return '{"datetime": "2025-09-13T05:18:47", "day_of_week": "Saturday"}'
    elif name == "get_weather":
        return '{"temperature": 13.2, "unit": "celsius", "conditions": "clear", "humidity": 93}'

# ── 初始消息列表 ──
messages = [
    {"role": "system", "content": "你是一个乐于助人的助手。在需要时使用工具获取实时信息。"},
    {"role": "user", "content": "温哥华当前的时间和天气是什么？"},
]

# ── 代理核心循环 ──
# 生产代码需要在此处设置max_iterations限制：如本章后面所述，代理可能会永远重复相同的工具调用而陷入困境
while True:
    response = client.chat.completions.create(
        model="Qwen3-0.6B", messages=messages, tools=tools
    )
    assistant_message = response.choices[0].message

    # 将模型的响应追加到消息列表中（无论是文本还是工具调用）
    messages.append(assistant_message)

    # 如果没有请求工具调用，模型已生成最终响应
    if not assistant_message.tool_calls:
        print(assistant_message.content)
        break

    # 执行模型请求的每个工具，将结果追加到消息列表中
    for tool_call in assistant_message.tool_calls:
        result = execute_tool(tool_call.function.name, tool_call.function.arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
    # 返回循环顶部，使用更新后的消息列表再次调用模型
```

The loop has one main branch: **if the model returns `tool_calls`, execute the tools and continue; otherwise, output the result and exit.** During this process, the `messages` list keeps growing as each round appends the model's reply and any tool execution results.

The `messages` list changes across rounds as follows:

**Initial state (before the first call):**
```
messages = [
  { role: "system",  content: "你是一个乐于助人的助手..." },     # 由开发者编写
  { role: "user",    content: "温哥华当前的时间和天气是什么？" },  # 用户输入
]
```