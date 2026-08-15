# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from aworld.core.agent.swarm import Swarm
from aworld.runner import Runners
from examples.multi_agents.workflow.search.common import *

# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"
# search and summary
if __name__ == "__main__":
    # need to set GOOGLE_API_KEY and GOOGLE_ENGINE_ID to use Google search.
    # os.environ['GOOGLE_API_KEY'] = ""
    # os.environ['GOOGLE_ENGINE_ID'] = ""

    # default is workflow swarm
    swarm = Swarm(search, summary, max_steps=1)
    # swarm = WorkflowSwarm(search, summary, max_steps=1)

    prefix = ""
    # can special search google, wiki, duck go, or baidu. such as:
    # prefix = "search wiki: "
    res = Runners.sync_run(
        input=prefix + """What is an agent.""",
        swarm=swarm
    )
    print(res.answer)
