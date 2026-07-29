# 第 9 章 · 多模态与实时交互

> 从文本扩展到语音、GUI、物理世界：语音三范式、Computer Use、机器人

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter9.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | 实时语音聊天，集成 VAD + ASR（Whisper/SenseVoice）+ LLM（GPT-4o/Gemini/Doubao）+ TTS（Fish Audio），WebSocket 低延迟 |
| 9-2 | [phone-agent](phone-agent/) | ✅ | 标准 ReAct Agent 自行想清号码与目标，调用 `make_phone_call`（电话语音 API 抽象）完成通话并按需追问再拨 |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | 音频按递增长度分块喂 ASR，每段立刻出文本降首包延迟，对比「整句到齐再识别」的高准确/高延迟 |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | 对应 Step-Audio R1 的端到端语音思考（「听→想→说」），与 ASR→LLM→TTS 级联对比延迟与副语言损失 |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | LLM 输出带控制标记（情感/语速/停顿/笑声），执行层解析映射到参考语音库风格档案再合成 |
| 9-6 | `claude-quickstarts/` | 📖 | Claude API 快速入门示例与最佳实践，涵盖各种使用场景 |
| 9-7 | `browser-use/` | 📖 | LLM 驱动的浏览器自动化框架，表单填写/网页导航/数据提取，支持多种 LLM 与云/沙箱部署 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
