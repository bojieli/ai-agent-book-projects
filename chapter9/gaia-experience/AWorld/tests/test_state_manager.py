import unittest
import uuid
import asyncio
import random
import time
from typing import List

import pytest

from aworld.core.event.base import Constants, Message
from aworld.runners.state_manager import (
    EventRuntimeStateManager,
    RunNode,
    RunNodeBusiType,
    RunNodeStatus,
    RuntimeStateManager,
)


class StateManagerTest(unittest.TestCase):
    def test_runtime_state_manager(self):
        state_manager = RuntimeStateManager()
        session_id = "1"

        node = state_manager.create_node(busi_type=RunNodeBusiType.TASK,
                                         busi_id="1", session_id=session_id, msg_id="1")

        state_manager.run_node(node.node_id)
        node = state_manager.get_node(node.node_id)
        assert node.status == RunNodeStatus.RUNNING

        state_manager.break_node(node.node_id)
        node = state_manager.get_node(node.node_id)
        assert node.status == RunNodeStatus.BREAKED

        state_manager.run_succeed(node.node_id)
        node = state_manager.get_node(node.node_id)
        assert node.status == RunNodeStatus.SUCCESS

        node = state_manager.create_node(busi_type=RunNodeBusiType.TASK,
                                         busi_id="2", session_id=session_id, msg_id="2", msg_from="1")

        state_manager.run_node(node.node_id)
        state_manager.run_failed(node.node_id)
        node = state_manager.get_node(node.node_id)
        assert node.status == RunNodeStatus.FAILED

        node = state_manager.create_node(busi_type=RunNodeBusiType.TASK,
                                         busi_id="3", session_id=session_id, msg_id="3", msg_from="1")
        state_manager.run_node(node.node_id)
        state_manager.run_timeout(node.node_id)
        node = state_manager.get_node(node.node_id)
        assert node.status == RunNodeStatus.TIMEOUT

        node = state_manager.create_node(busi_type=RunNodeBusiType.TASK,
                                         busi_id="4", session_id=session_id, msg_id="4", msg_from="3")
        state_manager.run_succeed(node.node_id)

        nodes = state_manager.get_nodes(session_id=session_id)
        self.build_run_flow(nodes)

    def build_run_flow(self, nodes: List[RunNode]):
        graph = {}
        start_nodes = []

        for node in nodes:
            if hasattr(node, 'parent_node_id') and node.parent_node_id:
                if node.parent_node_id not in graph:
                    graph[node.parent_node_id] = []
                graph[node.parent_node_id].append(node.node_id)
            else:
                start_nodes.append(node.node_id)

        for start in start_nodes:
            print("-----------------------------------")
            self._print_tree(graph, start, "", True)
            print("-----------------------------------")

    def _print_tree(self, graph, node_id, prefix, is_last):
        print(prefix + ("└── " if is_last else "├── ") + node_id)
        if node_id in graph:
            children = graph[node_id]
            for i, child in enumerate(children):
                self._print_tree(graph, child, prefix +
                                 ("    " if is_last else "│   "), i == len(children) - 1)

    @pytest.mark.asyncio
    async def test_node_group_create(self):
        state_manager: EventRuntimeStateManager = EventRuntimeStateManager.instance()
        await state_manager.create_group(
            group_id="test_group0",
            session_id="session1",
            root_node_ids=["root_message_id1", "root_message_id2", "root_message_id3"],
            parent_group_id="test_parant_group"
        )
        group = state_manager.get_group("test_group0")
        assert group is not None
        assert group.status == RunNodeStatus.INIT

    @pytest.mark.asyncio
    async def test_all_proccess(self):
        state_manager: EventRuntimeStateManager = EventRuntimeStateManager.instance()

        root_message_id1 = uuid.uuid4().hex
        root_message_id2 = uuid.uuid4().hex
        root_message_id3 = uuid.uuid4().hex

        headers = {
            "session_id": "session1",
            "group_id": "test_group"
        }

        def get_headers(root_message_id):
            return {
                "root_message_id": root_message_id,
                **headers
            }

        sub_node_message1 = Message(
            id=root_message_id1,
            category=Constants.AGENT,
            session_id="session1",
            topic="test_topic",
            headers=get_headers(root_message_id1)
        )
        sub_node_message2 = Message(
            id=root_message_id2,
            category=Constants.AGENT,
            session_id="session1",
            topic="test_topic",
            headers=get_headers(root_message_id2)
        )
        sub_node_message3 = Message(
            id=root_message_id3,
            category=Constants.AGENT,
            session_id="session1",
            topic="test_topic",
            headers=get_headers(root_message_id3)
        )

        sub_tasks = []

        async def sub_group_task(message: Message):
            await asyncio.sleep(random.randint(1, 3))
            state_manager.start_message_node(message)
            await asyncio.sleep(random.randint(1, 3))
            result_message = Message(
                session_id="session1",
                topic="test_topic",
                headers=message.headers
            )
            state_manager.save_message_handle_result("sub_node_message1", message, result_message)
            state_manager.end_message_node(message)
            await state_manager.finish_sub_group(message.headers["group_id"], message.headers["root_message_id"],
                                                 [result_message])

        sub_tasks.append(asyncio.create_task(sub_group_task(sub_node_message1)))
        sub_tasks.append(asyncio.create_task(sub_group_task(sub_node_message2)))
        sub_tasks.append(asyncio.create_task(sub_group_task(sub_node_message3)))

        await state_manager.create_group(
            group_id=headers["group_id"],
            session_id=headers["session_id"],
            root_node_ids=[root_message_id1, root_message_id2, root_message_id3],
            parent_group_id="test_parant_group"
        )
        print(f"create group complete, group_id: {headers['group_id']}")
        group = state_manager.get_group(headers["group_id"])
        assert group is not None

        await asyncio.gather(*sub_tasks)

        print(f"sub group complete, group_id: {headers['group_id']}")
        group = state_manager.get_group(headers["group_id"])
        assert group is not None
        assert group.status == RunNodeStatus.SUCCESS

        group_detail = state_manager.query_group_detail(headers["group_id"])
        assert group_detail is not None
        for subgroup in group_detail.sub_groups:
            assert subgroup.status == RunNodeStatus.SUCCESS

    def test_query_by_task(self):
        state_manager = RuntimeStateManager()
        session_id = str(uuid.uuid4())
        task_id1 = str(uuid.uuid4())
        task_id2 = str(uuid.uuid4())
        agent_id1 = str(uuid.uuid4())
        agent_id2 = str(uuid.uuid4())

        node1 = state_manager.create_node(
            busi_type=RunNodeBusiType.TASK,
            busi_id=task_id1,
            session_id=session_id,
            task_id=task_id1,
            msg_id=str(uuid.uuid4())
        )
        time.sleep(0.01)
        node2 = state_manager.create_node(
            busi_type=RunNodeBusiType.AGENT,
            busi_id=agent_id1,
            session_id=session_id,
            task_id=task_id1,
            msg_id=str(uuid.uuid4())
        )
        time.sleep(0.01)
        node3 = state_manager.create_node(
            busi_type=RunNodeBusiType.TASK,
            busi_id=task_id2,
            session_id=session_id,
            task_id=task_id2,
            msg_id=str(uuid.uuid4())
        )
        time.sleep(0.01)
        node4 = state_manager.create_node(
            busi_type=RunNodeBusiType.AGENT,
            busi_id=agent_id2,
            session_id=session_id,
            task_id=task_id1,
            msg_id=str(uuid.uuid4())
        )

        result1 = state_manager.query_by_task(task_id=task_id1)
        self.assertEqual(len(result1), 3)
        self.assertGreater(result1[0].create_time, result1[1].create_time)

        result2 = state_manager.query_by_task(task_id=task_id1, busi_typ=RunNodeBusiType.AGENT, busi_id=agent_id1)
        self.assertEqual(len(result2), 1)
        self.assertEqual(result2[0].node_id, node2.node_id)

        result3 = state_manager.query_by_task(task_id=str(uuid.uuid4()))
        self.assertEqual(len(result3), 0)

        with self.assertRaises(Exception):
            state_manager.query_by_task(task_id=task_id1, busi_typ=RunNodeBusiType.AGENT)

        with self.assertRaises(Exception):
            state_manager.query_by_task(task_id=task_id1, busi_id=agent_id1)
