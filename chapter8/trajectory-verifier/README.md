# 实验 8-1：客服 Agent 的三层轨迹验证器

本实验对应正文的“从运行轨迹中获得学习信号”。它不把用户满意度或一个总分当作学习信号，而是依次核对环境结果、执行过程与语言质量，并在每个失败维度中保留证据轮次。

`verifier.py` 实现三层结构：结果层读取最终订单状态；过程层检查业务规则、隐私、事实依据和承诺—行动一致性；质量层按“表达质量、合规变通”Rubric 评价开放性指标。示例默认使用确定性的 `HeuristicQualityJudge`，所以不需要 API Key；项目也提供遵循同一 `QualityJudge` 接口的真实 LLM 实现，下两层仍坚持使用环境真值和程序规则。

`sample_trajectories.json` 包含正常退款、虚假承诺、违规泄露和过度拒绝四类轨迹，并带有专家标签。`calibration.py` 按维度报告违规识别的精确率、召回率与标签一致率。`demo.py` 还对比了只有一个总分的输出与带证据的多维诊断。

运行方法：

```bash
python demo.py
python -m unittest -v test_verifier.py
```

以上是确定性校准路径。若要真实调用 LLM 评价表达质量与合规变通：

```bash
pip install -r requirements.txt
cp env.example .env
export OPENAI_API_KEY=your_api_key_here
python demo.py --judge llm --model gpt-5.6
```

真实模式使用 OpenAI Responses API，并要求模型按相同 schema 返回逐维结论、证据轮次和置信度；环境结果与过程规则两层仍由代码判断。该命令会产生真实 API 费用，输出可能随模型版本变化，应继续用专家标签检查每个维度，而不能只观察总分。

真实系统应扩大专家校准集，并把低置信度或高风险轨迹交给第二个验证器或人工复核。样例中的 `quality_facts` 是离线实验对 LLM 判读结果的显式表示，并不意味着生产系统可以预先获得这些字段。
