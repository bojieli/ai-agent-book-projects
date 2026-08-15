# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from aworld.core.agent.swarm import Swarm
from aworld.runner import Runners
from examples.multi_agents.workflow.search.common import *

if __name__ == "__main__":
    s1 = Swarm(search)
    s2 = Swarm(summary)
    # default is workflow swarm
    # swarm1 and swarm2 are embedded into the swarm, which is a hierarchical swarm
    swarm = Swarm(s1, s2, max_steps=1)

    prefix = ""
    # can special search google, wiki, duck go, or baidu. such as:
    # prefix = "search wiki: "
    res = Runners.sync_run(
        input=prefix + """What is an agent.""",
        swarm=swarm
    )
    print(res.answer)
