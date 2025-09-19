# 《AI Agent 实战营》配套代码

本目录包含《AI Agent 实战营》的所有配套示例代码。每个项目都是可独立运行的完整示例。

## 📚 项目结构

所有项目按周次组织，涵盖了从基础概念到高级技术的完整学习路径。

## 🚀 Week 1 - Agent 基础

### 1. learning-from-experience - 强化学习 vs LLM 对比
`week1/learning-from-experience/`

对比传统强化学习（Q-learning）与基于 LLM 的上下文学习，复现 Shunyu Yao 的 "The Second Half" 博文中的关键洞察。通过寻宝游戏展示 LLM 如何以 250-400 倍的样本效率超越传统 RL。

**核心概念**：强化学习、上下文学习、样本效率、先验知识

### 2. web-search-agent - Kimi K2 模型即 Agent
`week1/web-search-agent/`

实现具备基础深度搜索能力的 Agent，能够进行多轮搜索和信息整合。

**核心概念**：网络搜索、模型原生 Agent

### 3. search-codegen - GPT-5 原生工具集成
`week1/search-codegen/`

构建能够基础深度搜索能力和代码沙盒能力的 Agent，综合利用网络搜索、代码执行等工具实现复杂分析。

**核心概念**：网络搜索、代码生成、模型原生 Agent

### 4. context - 上下文消融研究 
`week1/context/`

通过系统性的消融实验展示 Agent 上下文各个组件的重要性。支持多种 LLM 提供商（SiliconFlow Qwen、字节 Doubao、月之暗面 Kimi），配置不同的上下文模式观察 Agent 行为变化。

**核心概念**：上下文管理、工具调用、ReAct 循环、消融研究

## 🎯 Week 2 - 上下文工程与优化

### 1. local_llm_serving - 本地 LLM 部署与工具调用
`week2/local_llm_serving/`

跨平台的本地 LLM 部署方案，自动选择最佳后端（vLLM 或 Ollama）。展示即使 0.6B 的小模型也能通过良好的系统设计实现出色的工具调用能力。支持流式响应，实时显示思考过程。

**核心概念**：模型部署、Chat Template、流式处理、工具调用

### 2. attention_visualization - 注意力机制可视化
`week2/attention_visualization/`

可视化 LLM 的完整输入输出 token 序列和注意力权重分布，深入理解模型如何处理上下文、进行推理和调用工具。

**核心概念**：注意力机制、token 分析、推理过程可视化

### 3. kv-cache - KV Cache 友好的上下文设计
`week2/kv-cache/`

探索不同上下文管理模式对 KV Cache 的影响，演示常见的错误模式如何破坏缓存效率。通过实验展示正确的上下文设计如何显著降低延迟和成本。

**核心概念**：KV Cache、上下文优化、性能调优

### 4. context-compression - 上下文压缩策略
`week2/context-compression/`

实现并对比多种上下文压缩策略，包括摘要、关键信息提取、语义压缩等。在保持 Agent 能力的同时减少 token 使用量。

**核心概念**：上下文压缩、token 优化、信息密度

### 5. prompt-engineering - 提示工程消融研究
`week2/prompt-engineering/`

扩展 Tau-Bench 框架，通过系统性的消融实验量化不同提示工程因素对 Agent 性能的影响。展示语气风格、指令组织、工具描述等因素如何影响任务完成率。

**核心概念**：提示工程、消融研究、性能基准测试

### 6. system-hint - 系统提示优化
`week2/system-hint/`

研究系统提示（System Hint）对 Agent 行为的影响，探索如何通过优化系统提示提升性能。

**核心概念**：系统提示、行为引导、提示优化

### 7. user-memory-evaluation - 用户记忆评估框架
`week2/user-memory-evaluation/`

系统化评估用户记忆系统的准确性、相关性和有效性，包含多种测试场景和评估指标。

**核心概念**：评估框架、测试用例、性能度量

### 8. user-memory - 用户记忆系统
`week2/user-memory/`

构建长期用户记忆系统，让 Agent 能够记住用户偏好和历史交互，提供个性化服务。

**核心概念**：长期记忆、个性化、用户建模

### 9. log-sanitization - 日志脱敏处理
`week2/log-sanitization/`

实现智能的日志脱敏系统，在保留调试信息的同时保护敏感数据。

**核心概念**：隐私保护、日志处理、数据安全

## 📖 学习建议

1. **按顺序学习**：Week 1 建立基础概念，Week 2 深入工程实践
2. **动手实践**：每个项目都设计为可独立运行，建议亲自运行并修改代码
3. **结合书籍**：配合《AI Agent 实战营》配套电子书相应章节阅读，理解理论与实践的结合
4. **实验对比**：多个项目包含消融研究和对比实验，通过对比加深理解

## 🔑 API 密钥

建议大家申请几个平台的 API key，方便学习：
- **Kimi**: https://platform.moonshot.cn/
- **Siliconflow**: https://siliconflow.cn/ 上面有各种开源模型，包括 DeepSeek、Qwen 等
- **火山引擎**: https://www.volcengine.com/product/ark 上面有字节的闭源模型（豆包），国内访问延迟比较低
- **OpenRouter**: https://openrouter.ai/ 可以从国内直接访问海外的各种闭源和开源模型，包括 Gemini 2.5 Pro、Claude 4 Sonnet、OpenAI GPT-5 等（官方 API 需要海外 IP 和支付方式，OpenAI 还需要海外身份实名认证，注册比较麻烦）

模型选型可以参考： https://01.me/2025/07/llm-api-setup/

## 🤝 贡献

欢迎通过 Pull Request 贡献代码改进、bug 修复或新的示例项目。

## 📄 许可证

本项目代码仅供学习参考，具体许可证信息请查看各子项目。
