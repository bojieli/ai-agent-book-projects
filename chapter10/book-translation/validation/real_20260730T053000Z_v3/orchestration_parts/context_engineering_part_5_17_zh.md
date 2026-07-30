`标签内，保持工具调用之间的连续性。当模板检测到新的用户轮次时，会清除该推理上下文并开始新的上下文。如果工具结果错误标记为用户消息，可能会在错误的时间触发这种重置，削弱多步推理的连贯性。注意不同模型家族在处理历史思维链的方式上差异很大，而且策略本身正在迅速演变。DeepSeek R1时代的官方指导是**剥离所有历史推理**：在多轮对话中，只传递`content`，不传递`reasoning_content`——因为R1的训练输入中从未出现过历史CoT，反馈回去属于分布外输入，可能反而干扰输出，还能节省相当数量的词元。但这种策略在代理场景下有缺陷：中间推理携带“为什么调用这个工具以及排除了哪些假设”等关键状态；一旦剥离，模型每一轮都从头推理，容易重复错误并丢失长程计划。因此DeepSeek在V4中**完全反转**了策略，强制逐字传递每个助手消息（包括带有`tool_calls`的消息）的`reasoning_content`，否则API直接返回错误—— kimi K2、GLM-5等也采用了相同协议。与此同时，Claude要求客户端在工具调用循环内将思维块（带签名验证）原封不动传递给API，而服务器在新用户轮次后忽略历史思维。整个行业从“剥离”转向“强制回传”本身就是有力证据：**对于代理场景，思维不是浪费而是状态**。使用前请查阅模型最新的模板文档。

**第二，解释了为什么KV缓存对前缀如此敏感。** 聊天模板将系统消息和工具定义转换为输入开头附近的固定词元序列。这些词元的键值状态可以在请求间缓存和复用。如果该前缀中的任何词元改变，即使系统提示中多了一个空格，该点之后的缓存就无法再复用。

### KV缓存的原理与约束

要理解KV缓存的价值，首先考虑没有它时会发生什么。假设一个代理已经进行到第六轮对话，积累了2000个上下文词元。没有缓存时，每个新词元都要求模型重新计算整个前缀的K和V向量。尽管前5轮没有变化，但第六轮仍然要重新计算，而且前缀越长，这一轮的成本比第一轮高。没有缓存时，预填充阶段（模型在生成响应前处理所有输入词元的阶段）的注意力计算随上下文长度呈二次方增长，随着对话深入，时延和成本迅速上升。这对需要多次工具调用的代理任务尤其成问题。

![图2-10：KV缓存前缀复用机制](images/fig2-10.svg)

**通过简单示例理解KV缓存。** 假设上下文有4个词元[A, B, C, D]，模型即将生成第五个词元E。核心注意力操作将E的查询向量与现有词元的键向量进行比较以计算匹配分数（关于点积的直观解释见实验2-2）。然后使用这些分数计算值向量的加权和，生成E的输出表示。

没有KV缓存时，每次生成新词元，都必须从头重新计算所有前面词元的K和V向量：生成E需要计算5组K和V，生成第六个词元需要计算6组……到第N个词元时，需要计算N组，总计算量与N²成正比。

有KV缓存时，A、B、C、D的K和V向量在首次计算后被缓存。生成E时，只需要计算E自己的K和V，然后使用这些以及4个缓存的组进行注意力计算。注意KV缓存节省了历史词元的K和V投影的重新计算，因此每个解码步骤不需要重新计算整个前缀；然而，每个新词元的注意力计算仍然需要遍历所有缓存的K和V值，计算量随上下文长度呈线性增长——这就是长上下文解码越来越慢的原因，而KV缓存的内存和带宽成为推理瓶颈。

**为什么修改前缀会使缓存失效？** 大语言模型由堆叠的Transformer层组成（现代大模型通常有几十到几百层），每层都会生成自己的KV缓存。这些层按顺序连接：层1的输出成为层2的输入，层2的输出成为层3的输入，依此类推。处理每个词时，层1会考虑该词和所有前面的词，然后输出中间表示；层2接收该表示并进一步处理。如果早期的词元改变（例如系统提示中的一个字符），层1的输出改变，层2的输入改变，差异会传播到后续层。该点之后的缓存状态必须重新计算。成本很高：之前处理的词元可能需要重新计算并再次计费，时延会大幅增加（本章实验测量到数倍增长）。这就是本书反复强调的：一旦设置系统提示，就不要修改它。</think>### 上下文工程 [第5/17部分]

The Chat Template is a **foundational concept throughout this book**. It affects not only KV Cache behavior, but also mechanisms such as multi-turn tool calls, chain-of-thought retention, and status bar injection. It therefore deserves a dedicated explanation. The token sequences in the attention visualization experiment (e.g., special tokens like `<|im_start|>`, `<|im_end|>`) look very different from the JSON-format API messages shown earlier. The reason is that structured API messages must be converted into a linear token stream the model can process. The component responsible for this conversion is the **Chat Template**.

![Figure 2-8: Token Structure of Chat Template](images/fig2-8.svg)

A useful way to understand the Chat Template is as an **envelope format**. The API message is the content of the letter, while the Chat Template specifies how the sender, recipient, and boundaries are written on the envelope. It uses special tokens (e.g., `<|im_start|>system`, `<|im_end|>`) to mark the role and boundary of each message. Different model families (Qwen, Llama, Gemma) use different envelope formats. The API server (vLLM, Ollama, etc.) performs this conversion automatically based on the model's Chat Template, so developers usually do not need to handle it manually.

Using the Qwen model series as an example, the same conversation appears in completely different forms at the API level and inside the model:

![Figure 2-9: Conversion from API Messages to Model Token Stream](images/fig2-9.svg)

On the left is the structured JSON message, and on the right is the linear token stream that the model processes. `<|im_start|>` and `<|im_end|>` are special tokens that tell the model the role and boundaries of each message.

Agent developers **do not need to manually write or modify the Chat Template**; the API server handles it automatically. However, understanding its existence has two practical benefits for Agent development:

**First, it explains why standard API formats must be used.** If a developer bypasses the API and manually concatenates messages (for example, passing tool results as ordinary user messages instead of tool messages), the Chat Template may represent the conversation incorrectly. With Qwen3's Chat Template, for instance, multi-turn tool calls can retain prior internal reasoning content inside `<think>` tags, preserving continuity across tool calls. When the template detects a new user turn, it clears that reasoning context and starts a new one. If a tool result is incorrectly marked as a user message, it can trigger this reset at the wrong time, weakening the coherence of multi-step reasoning. Note that different model families differ greatly in how they handle historical chain-of-thought, and the strategies themselves are evolving rapidly. The official guidance in the DeepSeek R1 era was to **strip all historical reasoning**: in multi-turn conversations, only `content` is passed back, not `reasoning_content`—because historical CoT never appeared in R1's training input, feeding it back is out-of-distribution input that may instead interfere with the output, and it also saves a considerable number of tokens. But this strategy has flaws for Agent scenarios: intermediate reasoning carries critical state such as "why this tool was called and which hypotheses were ruled out"; once stripped, the model reasons from scratch every turn, making it prone to repeating mistakes and losing long-range plans. DeepSeek therefore **completely reversed** the policy in V4, mandating that the `reasoning_content` of every assistant message (including those with `tool_calls`) be passed back verbatim, otherwise the API returns an error outright—Kimi K2, GLM-5, and others have adopted the same protocol. Claude, meanwhile, requires the client to pass the thinking block (with signature verification) back to the API unchanged within the tool call loop, while the server ignores historical thinking after a new user turn. This industry-wide shift from "stripping" to "mandatory pass-back" is itself strong evidence: **for Agent scenarios, thinking is not waste but state**. Consult the model's latest template documentation before use.

**Second, it explains why KV Cache is so sensitive to the prefix.** The Chat Template converts system messages and tool definitions into a fixed token sequence near the beginning of the input. The key-value states for these tokens can be cached and reused across requests. If any token in this prefix changes, even an extra space in the system prompt, the cache after that point can no longer be reused.

### Principles and Constraints of KV Cache

To understand the value of KV Cache, first consider what happens without it. Suppose an Agent has reached the sixth conversation round and accumulated 2,000 context tokens. Without caching, each new token requires the model to recalculate the K and V vectors for the entire prefix. Although the first five rounds are unchanged, the sixth round still recomputes them, and the longer prefix makes this round more expensive than the first. Without caching, the attention computation in the prefill phase (the stage where the model processes all input tokens before generating a response) grows quadratically with context length, causing latency and cost to rise rapidly as the conversation deepens. This is especially problematic for Agent tasks that require many tool calls.

![Figure 2-10: KV Cache Prefix Reuse Mechanism](images/fig2-10.svg)

**Understanding KV Cache with a simple example.** Suppose the context has 4 tokens [A, B, C, D], and the model is about to generate the fifth token, E. The core attention operation compares E's Query vector with the Key vectors of the existing tokens to calculate match scores (for an intuitive explanation of dot products, see Experiment 2-2). It then uses those scores to compute a weighted sum of the Value vectors, producing E's output representation.

Without KV Cache, every time a new token is generated, the K and V vectors of all preceding tokens must be recalculated from scratch: generating E requires computing 5 sets of K and V, generating the sixth token requires computing 6 sets... and by the Nth token, N sets must be computed, with the total computation proportional to N².

With KV Cache, the K and V vectors of A, B, C, and D are cached after being computed once. When generating E, only E's own K and V need to be computed, and then the attention calculation is performed using these along with the 4 cached sets. Note that KV Cache saves the recomputation of the K and V projections for historical tokens, so each decoding step does not need to recompute the entire prefix; however, the attention calculation for each new token still needs to traverse all cached K and V values, with computation growing linearly with context length — this is why long-context decoding becomes increasingly slow, and KV Cache's memory and bandwidth become the inference bottleneck.

**Why does modifying the prefix invalidate the cache?** Large language models are composed of stacked Transformer layers (modern LLMs typically have dozens to hundreds of layers), and each layer produces its own K and V cache. These layers are connected in sequence: the output of layer 1 becomes the input to layer 2, the output of layer 2 becomes the input to layer 3, and so on. When processing each word, layer 1 considers that word and all preceding words, then outputs an intermediate representation; layer 2 takes that representation and processes it further. If an early token changes (for example, one character in the system prompt), the output of layer 1 changes, the input to layer 2 changes, and the difference propagates through the subsequent layers. The cached states after that change must be recomputed. The cost is significant: previously processed tokens may need to be recomputed and billed again, and latency can increase substantially (this chapter's experiments measured severalfold increases). This is why the book repeatedly emphasizes: once the system prompt is set, do not change it.

### 上下文工程 [第5/17部分]

聊天模板是贯穿本书的一个**基础概念**。它不仅影响KV缓存的行为，还影响多轮工具调用、思维链保留和状态栏注入等机制。因此值得专门解释。注意力可视化实验中的词元序列（例如`<|im_start|>`、`<|im_end|>`等特殊词元）看起来与之前显示的JSON格式API消息非常不同。原因是结构化的API消息必须转换为模型可以处理的线性词元流。负责这种转换的组件就是**聊天模板**。

![图2-8：聊天模板的词元结构](images/fig2-8.svg)

理解聊天模板的一个有用方式是将其视为**信封格式**。API消息是信件的内容，而聊天模板指定了如何在信封上书写发送者、接收者和边界。它使用特殊词元（例如`<|im_start|>system`、`<|im_end|>`）来标记每条消息的角色和边界。不同的模型家族（通义千问、 llama、 Gemma）使用不同的信封格式。API服务器（vLLM、Ollama等）会根据模型的聊天模板自动进行这种转换，因此开发者通常不需要手动处理。

以通义千问模型系列为例，同一个对话在API层面和模型内部以完全不同的形式呈现：

![图2-9：从API消息到模型词元流的转换](images/fig2-9.svg)

左侧是结构化的JSON消息，右侧是模型处理的线性词元流。`<|im_start|>`和`<|im_end|>`是特殊词元，告诉模型每条消息的角色和边界。

代理开发者**不需要手动编写或修改聊天模板**；API服务器会自动处理。然而，了解它的存在对代理开发有两个实际好处：

**第一，解释了为什么必须使用标准API格式。** 如果开发者绕过API手动拼接消息（例如将工具结果作为普通用户消息而不是工具消息传递），聊天模板可能会错误表示对话。例如，使用通义千问3的聊天模板时，多轮工具调用可以将之前的内部推理内容保留在`<think>`标签内，保持工具调用之间的连续性。当模板检测到新的用户轮次时，会清除该推理上下文并开始新的上下文。如果工具结果错误标记为用户消息，可能会在错误的时间触发这种重置，削弱多步推理的连贯性。注意不同模型家族在处理历史思维链的方式上差异很大，而且策略本身正在迅速演变。DeepSeek R1时代的官方指导是**剥离所有历史推理**：在多轮对话中，只传递`content`，不传递`reasoning_content`——因为R1的训练输入中从未出现过历史CoT，反馈回去属于分布外输入，可能反而干扰输出，还能节省相当数量的词元。但这种策略在代理场景下有缺陷：中间推理携带“为什么调用这个工具以及排除了哪些假设”等关键状态；一旦剥离，模型每一轮都从头推理，容易重复错误并丢失长程计划。因此DeepSeek在V4中**完全反转**了策略，强制逐字传递每个助手消息（包括带有`tool_calls`的消息）的`reasoning_content`，否则API直接返回错误—— kimi K2、GLM-5等也采用了相同协议。与此同时，Claude要求客户端在工具调用循环内将思维块（带签名验证）原封不动传递给API，而服务器在新用户轮次后忽略历史思维。整个行业从“剥离”转向“强制回传”本身就是有力证据：**对于代理场景，思维不是浪费而是状态**。使用前请查阅模型最新的模板文档。

**第二，解释了为什么KV缓存对前缀如此敏感。** 聊天模板将系统消息和工具定义转换为输入开头附近的固定词元序列。这些词元的键值状态可以在请求间缓存和复用。如果该前缀中的任何词元改变，即使系统提示中多了一个空格，该点之后的缓存就无法再复用。

### KV缓存的原理与约束

要理解KV缓存的价值，首先考虑没有它时会发生什么。假设一个代理已经进行到第六轮对话，积累了2000个上下文词元。没有缓存时，每个新词元都要求模型重新计算整个前缀的K和V向量。尽管前5轮没有变化，但第六轮仍然要重新计算，而且前缀越长，这一轮的成本比第一轮高。没有缓存时，预填充阶段（模型在生成响应前处理所有输入词元的阶段）的注意力计算随上下文长度呈二次方增长，随着对话深入，时延和成本迅速上升。这对需要多次工具调用的代理任务尤其成问题。

![图2-10：KV缓存前缀复用机制](images/fig2-10.svg)

**通过简单示例理解KV缓存。** 假设上下文有4个词元[A, B, C, D]，模型即将生成第五个词元E。核心注意力操作将E的查询向量与现有词元的键向量进行比较以计算匹配分数（关于点积的直观解释见实验2-2）。然后使用这些分数计算值向量的加权和，生成E的输出表示。

没有KV缓存时，每次生成新词元，都必须从头重新计算所有前面词元的K和V向量：生成E需要计算5组K和V，生成第六个词元需要计算6组……到第N个词元时，需要计算N组，总计算量与N²成正比。

有KV缓存时，A、B、C、D的K和V向量在首次计算后被缓存。生成E时，只需要计算E自己的K和V，然后使用这些以及4个缓存的组进行注意力计算。注意KV缓存节省了历史词元的K和V投影的重新计算，因此每个解码步骤不需要重新计算整个前缀；然而，每个新词元的注意力计算仍然需要遍历所有缓存的K和V值，计算量随上下文长度呈线性增长——这就是长上下文解码越来越慢的原因，而KV缓存的内存和带宽成为推理瓶颈。

**为什么修改前缀会使缓存失效？** 大语言模型由堆叠的Transformer层组成（现代大模型通常有几十到几百层），每层都会生成自己的KV缓存。这些层按顺序连接：层1的输出成为层2的输入，层2的输出成为层3的输入，依此类推。处理每个词时，层1会考虑该词和所有前面的词，然后输出中间表示；层2接收该表示并进一步处理。如果早期的词元改变（例如系统提示中的一个字符），层1的输出改变，层2的输入改变，差异会传播到后续层。该点之后的缓存状态必须重新计算。成本很高：之前处理的词元可能需要重新计算并再次计费，时延会大幅增加（本章实验测量到数倍增长）。这就是本书反复强调的：一旦设置系统提示，就不要修改它。