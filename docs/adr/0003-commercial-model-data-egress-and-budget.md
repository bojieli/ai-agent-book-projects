# 限制商业模型的数据出站与调用预算

只有完成脱敏的 public/internal 内容可以发送到 OpenAI-compatible 商业模型；confidential/critical、密封会议内容、凭据和真实身份不得出站，必须转人工或明确失败。确定性规则先行，商业 Judge 仅处理灰区和远程评测；单请求限制为输入 8K、输出 2K token，每日最多 100 次、默认月预算 200 元，超限时不得绕过安全边界。

## Consequences

外部模型不可用或预算耗尽时，低风险生成可以降级为只读草稿；需要语义安全判决或涉及高风险写回的流程必须 fail-closed。
