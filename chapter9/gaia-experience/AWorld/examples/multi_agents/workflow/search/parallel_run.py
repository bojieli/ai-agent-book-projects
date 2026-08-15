# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from aworld.core.agent.swarm import Swarm
from aworld.runner import Runners
from examples.multi_agents.workflow.search.common import *

if __name__ == "__main__":
    search2 = Agent(
        conf=agent_config,
        name="search_agent",
        system_prompt=search_sys_prompt,
        agent_prompt=search_prompt,
        tool_names=[Tools.SEARCH_API.value]
    )

    # default is workflow swarm
    # search1 and search2 parallel execution and use the same input.
    swarm = Swarm((search, summary), (search2, summary), max_steps=1)
    # you also can set root_agent=[search, search2]

    prefix = ""
    # can special search google, wiki, duck go, or baidu. such as:
    # prefix = "search wiki: "
    res = Runners.sync_run(
        input=prefix + """What is an agent.""",
        swarm=swarm
    )
    print(res.answer)
