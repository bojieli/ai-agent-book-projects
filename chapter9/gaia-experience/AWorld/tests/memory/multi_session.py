# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio

from dotenv import load_dotenv

from aworld.memory.main import MemoryFactory
from tests.memory.agent.self_evolving_agent import SuperAgent

async def _run_multi_session_examples() -> None:
    """
    Run examples across multiple sessions demonstrating a complete learning workflow.
    This example shows a deep learning process about Agent-RL (Reinforcement Learning Agents):
    1. Deep search and research on Agent-RL concepts and implementations
    2. Content revision and modification for specific aspects
    3. Text-to-speech conversion for learning materials
    4. Next-day review and reinforcement
    """
    # await init_dataset()

    super_agent = SuperAgent(id="super_agent", name="super_agent")
    user_id = "alice"

    # Day 1 - Session 1: Deep Search on Agent-RL
    session_id = "day1_morning_session"
    await super_agent.async_run(
        user_id=user_id,
        session_id=session_id,
        task_id="alice:day1_morning:task#1",
        user_input="我想深入了解基于强化学习的智能体（Agent-RL）。请使用DEEPSEARCH帮我研究这个话题，包括：1. 基础架构（状态空间、动作空间、奖励机制）2. 常用算法（DQN、PPO、SAC等）3. 环境交互设计 4. 实现最佳实践"
    )
    await super_agent.async_run(
        user_id=user_id,
        session_id=session_id,
        task_id="alice:day1_morning:task#2",
        user_input="基于上面的搜索结果，请生成一个结构化的学习文档(markdown)，重点包含：1. 理论框架 2. 代码示例（使用Python实现简单的Agent-RL）3. 常见问题和解决方案"
    )

    # Day 1 - Session 2: Content Revision
    # session_id = "day1_afternoon_session"
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day1_afternoon:task#1",
    #     user_input="我觉得之前生成的文档中'环境交互设计'这部分需要补充。特别是：1. 如何设计合适的奖励函数 2. 环境状态的表示方法 3. 动作空间的设计考虑"
    # )
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day1_afternoon:task#2",
    #     user_input="太好了！现在请帮我把修改后的文档转换成更容易理解的形式，特别是把强化学习的数学概念用通俗的例子解释，准备生成语音内容"
    # )

    # Day 1 - Session 3: TTS Generation
    # session_id = "day1_evening_session"
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day1_evening:task#1",
    #     user_input="请将内容转换成语音文件，要求：1. 语速适中 2. 关键算法和数学概念讲解要清晰 3. 按照'理论基础-算法实现-实践应用'的顺序分章节 4. 生成字幕"
    # )
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day1_evening:task#2",
    #     user_input="请生成一个Agent-RL的知识图谱，包含：1. 核心概念关系 2. 算法分类 3. 应用场景 4. 学习路径建议"
    # )

    # Day 2 - Morning Review
    # session_id = "day2_morning_session"
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day2_morning:task#1",
    #     user_input="早上好！请帮我回顾一下昨天关于Agent-RL的学习内容。特别是：1. 通过知识图谱回顾核心概念 2. 复习各个算法的优缺点 3. 检查是否理解了关键的数学原理"
    # )
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day2_morning:task#2",
    #     user_input="基于已学内容，请推荐下一步的学习方向：1. 进阶算法（如MARL多智能体强化学习）2. 实际项目实践 3. 前沿研究方向"
    # )
    # await super_agent.async_run(
    #     user_id=user_id,
    #     session_id=session_id,
    #     task_id="alice:day2_morning:task#3",
    #     user_input="请设计一个实践项目，让我可以应用学到的Agent-RL知识。要求：1. 项目难度适中 2. 包含完整的代码框架 3. 有清晰的评估指标 4. 提供优化建议"
    # )


# if __name__ == '__main__':
#     load_dotenv()
#
#     MemoryFactory.init()
#
#     # Run the multi-session example with concrete learning tasks
#     asyncio.run(_run_multi_session_examples())

