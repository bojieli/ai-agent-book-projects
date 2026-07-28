# 快速开始

新版实验的默认入口不依赖 AWorld、向量数据库或 API Key：

```bash
cd chapter8/gaia-experience
python demo_documents.py
python -m unittest -v test_experience_documents.py
```

生成的 Markdown 位于 `output/experience_documents/`。终端会打印“无经验、单轨迹摘要、跨轨迹知识文档”三组迁移指标。

若要采集真实 GAIA 轨迹，再安装 `requirements.txt` 与 `AWorld/` 所需依赖，配置 `env.template`，然后查看：

```bash
python run_with_experience.py --help
```

真实运行得到的轨迹必须先经过 GAIA 结果评分，并转换为 `README.md` 所示的 evaluated record，才能进入跨轨迹文档生成阶段。
