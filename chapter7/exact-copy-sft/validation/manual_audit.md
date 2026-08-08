# 特殊字符串合成数据人工抽查记录

本轮扩容后按 `tool_json`、`decoy_copy`、`verbatim` 三类任务、10 种语言上下文和 8 种文章体裁分层抽查 train/eval/boundary 的样本（每类每 split 至少 4 条，共 36 条）。逐条检查：

1. `source` 与直接复述任务的 `target` 是否完全一致；
2. `tool_json` 的 JSON 是否可解析，且 `old_string` 是否与 `source` 完全相同；
3. 空格、换行、字面量 `\\n`/`\\t`、Unicode `é`、组合字符、中文和零宽字符是否按原样保存；
4. decoy 是否与 TARGET 等长但内容不同，避免模型靠长度捷径作答。

抽查未发现目标字符串漂移、JSON 结构错误或 decoy 标记歧义。全量确定性断言见 `tests/`，跨 tokenizer 的 encode→decode 结果见 [`tokenizer_audit.json`](tokenizer_audit.json)。
