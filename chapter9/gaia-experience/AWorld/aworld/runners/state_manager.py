import abc
import time
import asyncio
from pydantic import BaseModel
from typing import Optional, List
from aworld.core.event.base import Message
from enum import Enum
from abc import ABC, abstractmethod, ABCMeta
from aworld.core.agent.base import is_agent_by_name
from aworld.core.tool.tool_desc import is_tool_by_name
from aworld.core.singleton import InheritanceSingleton, SingletonMeta
from aworld.core.event.base import Constants
from aworld.logs.util import logger
from aworld.events.util import send_message


class RunNodeBusiType(Enum):
    AGENT = 'AGENT'
    TOOL = 'TOOL'
    TASK = 'TASK'
    TOOL_CALLBACK = 'TOOL_CALLBACK'
    HUMAN = 'HUMAN'

    @staticmethod
    def from_message_category(category: str) -> 'RunNodeBusiType':
        if category == Constants.AGENT:
            return RunNodeBusiType.AGENT
        if category == Constants.TOOL:
            return RunNodeBusiType.TOOL
        if category == Constants.TASK:
            return RunNodeBusiType.TASK
        if category == Constants.TOOL_CALLBACK:
            return RunNodeBusiType.TOOL_CALLBACK
        if category == Constants.HUMAN:
            return RunNodeBusiType.HUMAN
        return None


class RunNodeStatus(Enum):
    INIT = 'INIT'
    RUNNING = 'RUNNING'
    BREAKED = 'BREAKED'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    TIMEOUT = 'TIMEOUT'


class HandleResult(BaseModel):
    name: str = None
    status: RunNodeStatus = None
    result_msg: Optional[str] = None
    result: Optional[Message] = None


class RunNode(BaseModel):
    # {busi_id}_{busi_type}
    node_id: Optional[str] = None
    task_id: Optional[str] = None
    busi_type: str = None
    busi_id: Optional[str] = None
    session_id: Optional[str] = None
    msg_id: Optional[str] = None  # input message id
    # busi_id of node that send the input message
    msg_from: Optional[str] = None
    parent_node_id: Optional[str] = None
    status: RunNodeStatus = None
    result_msg: Optional[str] = None
    results: Optional[List[HandleResult]] = None
    create_time: Optional[float] = None
    execute_time: Optional[float] = None
    end_time: Optional[float] = None
    group_id: Optional[str] = None
    # sub_group_root_id required when group_id is not None
    sub_group_root_id: Optional[str] = None
    # metadata is used to store the context of the sub task when group_id is not None
    metadata: Optional[dict] = None

    def has_finished(self):
        return self.status in [RunNodeStatus.SUCCESS, RunNodeStatus.FAILED, RunNodeStatus.TIMEOUT]


class SubGroup(BaseModel):
    '''
    SubGroup represents an execution chain pointing to the root node 
    '''
    root_node_id: Optional[str] = None
    session_id: Optional[str] = None
    group_id: Optional[str] = None
    create_time: Optional[float] = None
    execute_time: Optional[float] = None
    end_time: Optional[float] = None
    status: RunNodeStatus = None
    result_msg: Optional[str] = None
    results: Optional[List[HandleResult]] = None
    metadata: Optional[dict] = None

    def has_finished(self):
        return self.status in [RunNodeStatus.SUCCESS, RunNodeStatus.FAILED, RunNodeStatus.TIMEOUT]


class NodeGroup(BaseModel):
    '''
    Node group, used to manage sub group
    '''
    group_id: str = None
    session_id: str = None
    # subtask root node id list
    root_node_ids: List[str] = None
    finished: Optional[bool] = False
    finish_notified: Optional[bool] = False
    create_time: Optional[float] = None
    execute_time: Optional[float] = None
    end_time: Optional[float] = None
    status: RunNodeStatus = None
    # failed subtask root node id list
    failed_root_node_ids: Optional[List[str]] = None
    parent_group_id: Optional[str] = None
    metadata: Optional[dict] = None

    def has_finished(self):
        return self.status in [RunNodeStatus.SUCCESS, RunNodeStatus.FAILED, RunNodeStatus.TIMEOUT]


class NodeGroupDetail(NodeGroup):
    sub_groups: Optional[List[SubGroup]] = None


class StateStorage:
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def get(self, node_id: str) -> RunNode:
        pass

    @abstractmethod
    def insert(self, node: RunNode):
        pass

    @abstractmethod
    def update(self, node: RunNode):
        pass

    @abstractmethod
    def query(self, session_id: str) -> List[RunNode]:
        pass

    @abstractmethod
    def query_by_task_id(self, task_id: str) -> List[RunNode]:
        pass


class NodeGroupStorage:
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def get(self, group_id: str) -> NodeGroup:
        pass

    @abstractmethod
    def insert(self, node_group: NodeGroup):
        pass

    @abstractmethod
    def update(self, node_group: NodeGroup):
        pass


class SubGroupStorage:
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def get(self, node_id: str) -> SubGroup:
        pass

    @abstractmethod
    def insert(self, sub_group: SubGroup):
        pass

    @abstractmethod
    def update(self, sub_group: SubGroup):
        pass


class StateStorageMeta(SingletonMeta, ABCMeta):
    pass


class InMemoryStateStorage(StateStorage, InheritanceSingleton, metaclass=StateStorageMeta):
    '''
    In memory state storage
    '''

    def __init__(self, max_session=1000):
        self._max_session = max_session
        self._nodes = {}  # {node_id: RunNode}
        self._ordered_session_ids = []
        self._session_nodes = {}  # {session_id: [RunNode, RunNode]}

    def get(self, node_id: str) -> RunNode:
        return self._nodes.get(node_id)

    def insert(self, node: RunNode):
        if node.session_id not in self._ordered_session_ids:
            self._ordered_session_ids.append(node.session_id)
            self._session_nodes.update({node.session_id: []})
        if node.node_id not in self._nodes:
            self._nodes.update({node.node_id: node})
            self._session_nodes[node.session_id].append(node)

        if len(self._ordered_session_ids) > self._max_session:
            oldest_session_id = self._ordered_session_ids.pop(0)
            session_nodes = self._session_nodes.pop(oldest_session_id)
            for node in session_nodes:
                self._nodes.pop(node.node_id)
        # logger.info(f"storage nodes: {self._nodes}")

    def update(self, node: RunNode):
        self._nodes[node.node_id] = node

    def query(self, session_id: str, msg_id: str = None) -> List[RunNode]:
        session_nodes = self._session_nodes.get(session_id, [])
        if msg_id:
            return [node for node in session_nodes if node.msg_id == msg_id]
        return session_nodes

    def query_by_task_id(self, task_id: str) -> List[RunNode]:
        return [node for node in self._nodes.values() if node.task_id == task_id]


class InMemoryNodeGroupStorage(NodeGroupStorage, InheritanceSingleton, metaclass=StateStorageMeta):
    '''
    In memory node group storage
    '''

    def __init__(self):
        self.node_groups = {}

    def get(self, group_id: str) -> NodeGroup:
        return self.node_groups.get(group_id)

    def insert(self, node_group: NodeGroup):
        self.node_groups[node_group.group_id] = node_group

    def update(self, node_group: NodeGroup):
        self.node_groups[node_group.group_id] = node_group


class InMemorySubGroupStorage(SubGroupStorage, InheritanceSingleton, metaclass=StateStorageMeta):
    '''
    In memory sub task storage
    '''

    def __init__(self):
        self.sub_groups = {}

    def get(self, node_id: str) -> SubGroup:
        return self.sub_groups.get(node_id)

    def insert(self, sub_group: SubGroup):
        self.sub_groups[sub_group.root_node_id] = sub_group

    def update(self, sub_group: SubGroup):
        self.sub_groups[sub_group.root_node_id] = sub_group


class RuntimeStateManager(InheritanceSingleton):
    '''
    Runtime state manager
    '''

    def __init__(self,
                 storage: StateStorage = InMemoryStateStorage.instance()):
        self.storage = storage
        self._node_group_manager = None

    @property
    def node_group_manager(self):
        if not self._node_group_manager:
            self._node_group_manager = NodeGroupManager(node_state_manager=self)
        return self._node_group_manager

    def create_node(self,
                    busi_type: RunNodeBusiType,
                    busi_id: str,
                    session_id: str,
                    node_id: str = None,
                    task_id: str = None,
                    parent_node_id: str = None,
                    msg_id: str = None,
                    msg_from: str = None,
                    group_id: str = None,
                    sub_group_root_id: str = None,
                    metadata: Optional[dict] = None) -> RunNode:
        '''
            create node and insert to storage
        '''
        node_id = node_id or msg_id
        node = self._find_node(node_id)
        if node:
            # raise Exception(f"node already exist, node_id: {node_id}")
            return
        if parent_node_id:
            parent_node = self._find_node(parent_node_id)
            if not parent_node:
                logger.warning(
                    f"parent node not exist, parent_node_id: {parent_node_id}")
        node = RunNode(node_id=node_id,
                       busi_type=busi_type.name,
                       busi_id=busi_id,
                       session_id=session_id,
                       task_id=task_id,
                       msg_id=msg_id,
                       msg_from=msg_from,
                       parent_node_id=parent_node_id,
                       status=RunNodeStatus.INIT,
                       create_time=time.time(),
                       group_id=group_id,
                       sub_group_root_id=sub_group_root_id,
                       metadata=metadata)
        self.storage.insert(node)
        # create sub group if node is the root node of sub group
        if group_id and sub_group_root_id and node_id == sub_group_root_id:
            self.node_group_manager.create_sub_group(group_id, session_id, sub_group_root_id, metadata)
        return node

    def run_node(self, node_id: str):
        '''
            set node status to RUNNING and update to storage
        '''
        logger.debug(f"====== set node {node_id} running =======")
        node = self._node_exist(node_id)
        node.status = RunNodeStatus.RUNNING
        node.execute_time = time.time()
        self.storage.update(node)
        # update sub group status if node is the root node
        if node.group_id and node.sub_group_root_id and node.node_id == node.sub_group_root_id:
            self.node_group_manager.run_sub_group(node_id)

    def save_result(self,
                    node_id: str,
                    result: HandleResult):
        '''
            save node execute result and update to storage
        '''
        node = self._node_exist(node_id)
        if not node.results:
            node.results = []
        node.results.append(result)
        self.storage.update(node)

    def break_node(self, node_id):
        '''
            set node status to BREAKED and update to storage
        '''
        node = self._node_exist(node_id)
        node.status = RunNodeStatus.BREAKED
        self.storage.update(node)

    def run_succeed(self,
                    node_id,
                    result_msg=None,
                    results: List[HandleResult] = None):
        '''
            set node status to SUCCESS and update to storage
        '''
        node = self._node_exist(node_id)
        node.status = RunNodeStatus.SUCCESS
        node.result_msg = result_msg
        node.end_time = time.time()
        if results:
            if not node.results:
                node.results = []
            node.results.extend(results)
        logger.debug(f"====== run_succeed set node {node_id} succeed: {node} =======")

        self.storage.update(node)

    def run_failed(self,
                   node_id,
                   result_msg=None,
                   results: List[HandleResult] = None):
        '''
            set node status to FAILED and update to storage
        '''
        node = self._node_exist(node_id)
        node.status = RunNodeStatus.FAILED
        node.result_msg = result_msg
        node.end_time = time.time()
        if results:
            if not node.results:
                node.results = []
            node.results.extend(results)
        self.storage.update(node)

    def run_timeout(self,
                    node_id,
                    result_msg=None):
        '''
            set node status to TIMEOUT and update to storage
        '''
        node = self._node_exist(node_id)
        node.status = RunNodeStatus.TIMEOUT
        node.result_msg = result_msg
        self.storage.update(node)

    def finish_sub_task(self, node_id: str):
        '''
            finish sub task with node_id as the root node
        '''
        node = self._node_exist(node_id)
        node.sub_task_finished = True
        self.storage.update(node)

    def get_node(self, node_id: str) -> RunNode:
        '''
            get node from storage
        '''
        return self._find_node(node_id)

    def get_nodes(self, session_id: str) -> List[RunNode]:
        '''
            get nodes from storage
        '''
        return self.storage.query(session_id)

    def _node_exist(self, node_id: str):
        node = self._find_node(node_id)
        if not node:
            raise Exception(f"node not found, node_id: {node_id}")
        return node

    def _find_node(self, node_id: str):
        return self.storage.get(node_id)

    def _judge_msg_from_busi_type(self, msg_from: str) -> RunNodeBusiType:
        '''
        judge msg_from busi_type
        '''
        if is_agent_by_name(msg_from):
            return RunNodeBusiType.AGENT
        if is_tool_by_name(msg_from):
            return RunNodeBusiType.TOOL
        return RunNodeBusiType.TASK

    async def wait_for_node_completion(self, node_id: str, timeout: float = 600.0, interval: float = 1.0) -> RunNode:
        '''Poll for node status until completion or timeout.

        Args:
            node_id: Node ID
            timeout: Timeout threshold in seconds
            interval: Polling interval in seconds

        Returns:
            RunNode: Node object

        Raises:
            Exception: If node does not exist
            TimeoutError: If waiting times out
        '''
        start_time = time.time()
        log_start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(f"wait for node completion: {node_id}, start_time:{log_start_time}")

        while True:
            node = self._find_node(node_id)
            if not node:
                raise Exception(f"Node not found, node_id: {node_id}")

            # Check if node has completed
            if node.status in [RunNodeStatus.SUCCESS, RunNodeStatus.FAILED, RunNodeStatus.BREAKED,
                               RunNodeStatus.TIMEOUT]:
                return node

            # Check if timed out
            if time.time() - start_time > timeout:
                self.run_timeout(node_id, result_msg=f"Waiting for node completion timed out after {timeout} seconds")
                node = self._find_node(node_id)
                return node

            # Wait for the specified interval before polling again
            await asyncio.sleep(interval)

    async def create_group(self, group_id: str,
                           session_id: str,
                           root_node_ids: List[str] = None,
                           parent_group_id: Optional[str] = None,
                           metadata: Optional[dict] = None) -> NodeGroup:
        '''
        create node group
        '''
        return await self.node_group_manager.create_group(group_id, session_id, root_node_ids, parent_group_id, metadata)

    async def finish_sub_group(self,
                               group_id: str,
                               root_node_id: str,
                               results: List[Message] = None,
                               result_msg: str = None):
        '''
        finish sub group
        '''
        handle_results = []
        for msg in results:
            handle_result = HandleResult(
                status=RunNodeStatus.FAILED if msg.is_error() else RunNodeStatus.SUCCESS,
                result=msg,
                name=msg.sender
            )
            handle_results.append(handle_result)
        await self.node_group_manager.finish_sub_group(group_id, root_node_id, handle_results, result_msg)

    def get_group(self, group_id: str) -> NodeGroup:
        '''
        get group basic info
        '''
        return self.node_group_manager.get_group(group_id)

    def query_group_detail(self, group_id: str) -> NodeGroupDetail:
        '''
        query group detail info with all sub group info
        '''
        return self.node_group_manager.query_group_detail(group_id)

    def query_by_task(self, task_id: str, busi_typ: RunNodeBusiType = None, busi_id: str = None) -> List[RunNode]:
        all_task_nodes = self.storage.query_by_task_id(task_id)
        if (not busi_typ and busi_id) or (busi_typ and not busi_id):
            raise Exception("busi_typ and busi_id must be both None or not None")
        if busi_typ and busi_id:
            result_nodes = [node for node in all_task_nodes if node.busi_type == busi_typ.name and node.busi_id == busi_id]
        else:
            result_nodes = all_task_nodes
        result_nodes.sort(key=lambda x: x.create_time if x.create_time else 0, reverse=True)
        return result_nodes


class NodeGroupManager(InheritanceSingleton):
    '''
    Node group manager, used to manage node group
    '''

    def __init__(self,
                 sub_group_storage: SubGroupStorage = InMemorySubGroupStorage.instance(),
                 node_group_storage: NodeGroupStorage = InMemoryNodeGroupStorage.instance(),
                 node_state_manager: RuntimeStateManager = None):
        self.sub_group_storage = sub_group_storage
        self.node_group_storage = node_group_storage
        self.node_state_manager = node_state_manager

    async def create_group(self, group_id: str,
                           session_id: str,
                           root_node_ids: List[str] = None,
                           parent_group_id: Optional[str] = None,
                           metadata: Optional[dict] = None) -> NodeGroup:
        '''
        create node group
        '''
        group = self._find_group(group_id)
        if group:
            raise Exception(f"group already exist, group_id: {group_id}")
        node_group = NodeGroup(
            session_id=session_id,
            group_id=group_id,
            root_node_ids=root_node_ids,
            parent_group_id=parent_group_id,
            metadata=metadata,
            create_time=time.time(),
            update_time=time.time(),
            status=RunNodeStatus.INIT,
        )
        self.node_group_storage.insert(node_group)
        await self._check_subgroup_status(group_id, root_node_ids)

    def create_sub_group(self,
                         group_id: str,
                         session_id: str,
                         root_node_id: str,
                         metadata: Optional[dict] = None) -> SubGroup:
        '''
        create sub group
        '''
        subgroup = self._find_subgroup(root_node_id)
        if subgroup:
            raise Exception(f"subgroup already exist, group_id: {group_id}, root_node_id: {root_node_id}")
        run_node = self.node_state_manager.get_node(root_node_id)
        if not run_node:
            raise Exception(f"run node not found, root_node_id: {root_node_id}")

        sub_group = SubGroup(
            session_id=session_id,
            group_id=group_id,
            root_node_id=root_node_id,
            metadata=metadata,
            create_time=time.time(),
            update_time=time.time(),
            status=RunNodeStatus.INIT,
        )
        self.sub_group_storage.insert(sub_group)
        return sub_group

    def run_sub_group(self,
                      root_node_id: str):
        '''
        run sub group
        '''
        subgroup = self._subgroup_exist(root_node_id)
        if not subgroup:
            raise Exception(f"subgroup not found, root_node_id: {root_node_id}")

        subgroup.execute_time = time.time()
        subgroup.status = RunNodeStatus.RUNNING
        self.sub_group_storage.update(subgroup)
        self.run_group(subgroup.group_id)

    def run_group(self, group_id):
        group = self.node_group_storage.get(group_id)
        if group.status == RunNodeStatus.INIT:
            group.status = RunNodeStatus.RUNNING
            group.execute_time = time.time()
            self.node_group_storage.update(group)

    async def finish_sub_group(self,
                               group_id: str,
                               root_node_id: str,
                               results: List[HandleResult] = None,
                               result_msg: str = None):
        '''
        finish sub task with node_id as the root node
        '''
        subgroup = self.sub_group_storage.get(root_node_id)
        if not subgroup:
            raise Exception(f"subgroup not found, group_id: {group_id}, root_node_id: {root_node_id}")
        if subgroup.group_id != group_id:
            raise Exception(f"subgroup group_id not match, group_id: {group_id}, root_node_id: {root_node_id}")

        group = self._group_exist(group_id)
        subgroup.end_time = time.time()
        subgroup.results = results
        subgroup.result_msg = result_msg
        subgroup.status = RunNodeStatus.SUCCESS
        for result in results:
            if result.status == RunNodeStatus.FAILED:
                subgroup.status = RunNodeStatus.FAILED
        self.sub_group_storage.update(subgroup)
        # check all subgroup status and update group status
        await self._check_subgroup_status(group_id, group.root_node_ids)

    async def _check_subgroup_status(self, group_id, root_node_ids: List[str]):
        '''
        check subgroups status and update group status, if group finished, send group finish message
        '''
        all_subgroups_finished = True
        failed_subgroups = []
        for root_node_id in root_node_ids:
            subgroup = self.sub_group_storage.get(root_node_id)
            if not subgroup or not subgroup.has_finished():
                all_subgroups_finished = False
                break
            if subgroup.status == RunNodeStatus.FAILED or subgroup.status == RunNodeStatus.TIMEOUT:
                failed_subgroups.append(subgroup)

        if all_subgroups_finished:
            group = self._group_exist(group_id)
            if failed_subgroups:
                group.status = RunNodeStatus.FAILED
                group.failed_root_node_ids = [subgroup.root_node_id for subgroup in failed_subgroups]
            else:
                group.status = RunNodeStatus.SUCCESS
            group.end_time = time.time()
            self.node_group_storage.update(group)
            await self._send_group_finish_message(group_id)

    async def _send_group_finish_message(self, group_id: str):
        '''
            Currently, for simple implementation, concurrency control needs to be considered in a distributed environment
        '''
        group = self._group_exist(group_id)
        if group.finish_notified:
            logger.warning(f"group finish message already sent, group_id: {group_id}")
            return
        group_results = {}
        metadata = group.metadata
        for root_node_id in group.root_node_ids:
            subgroup = self.sub_group_storage.get(root_node_id)
            group_results[root_node_id] = subgroup.results
            if not metadata:
                metadata = subgroup.metadata

        metadata = metadata or {}
        if group.parent_group_id:
            metadata.update({
                "parent_group_id": group.parent_group_id
            })
        message = Message(
            category="group",
            payload=group_results,
            sender="node_group_manager",
            session_id=group.session_id,
            topic="__group_results",
            headers=metadata
        )
        await send_message(message)
        group.finish_notified = True
        self.node_group_storage.update(group)

    def get_group(self, group_id: str) -> NodeGroup:
        '''
            get group basic info
        '''
        return self._find_group(group_id)

    def query_group_detail(self, group_id: str) -> NodeGroupDetail:
        '''
            query group detail info with all sub group info
        '''
        group = self._find_group(group_id)
        if not group:
            return None
        sub_groups = []
        for root_node_id in group.root_node_ids:
            subgroup = self._find_subgroup(root_node_id)
            if subgroup:
                sub_groups.append(subgroup)
        return NodeGroupDetail(
            group_id=group.group_id,
            root_node_ids=group.root_node_ids,
            parent_group_id=group.parent_group_id,
            metadata=group.metadata,
            create_time=group.create_time,
            execute_time=group.execute_time,
            end_time=group.end_time,
            status=group.status,
            failed_root_node_ids=group.failed_root_node_ids,
            sub_groups=sub_groups
        )

    def _find_subgroup(self, root_node_id: str) -> SubGroup:
        return self.sub_group_storage.get(root_node_id)

    def _subgroup_exist(self, root_node_id: str) -> SubGroup:
        subgroup = self._find_subgroup(root_node_id)
        if not subgroup:
            raise Exception(f"subgroup not found, root_node_id: {root_node_id}")
        return subgroup

    def _find_group(self, group_id: str) -> NodeGroup:
        return self.node_group_storage.get(group_id)

    def _group_exist(self, group_id: str) -> NodeGroup:
        group = self._find_group(group_id)
        if not group:
            raise Exception(f"group not found, group_id: {group_id}")
        return group


class EventRuntimeStateManager(RuntimeStateManager):

    def __init__(self, storage: StateStorage = InMemoryStateStorage.instance()):
        super().__init__(storage)

    def start_message_node(self, message: Message):
        '''
        create and start node while message handle started.
        '''
        metadata = message.headers
        run_node_busi_type = RunNodeBusiType.from_message_category(
            message.category)
        logger.debug(
            f"start message node: {message.receiver}, busi_type={run_node_busi_type}, node_id={message.id}")
        if run_node_busi_type:
            self.create_node(
                node_id=message.id,
                busi_type=run_node_busi_type,
                busi_id=message.receiver or "",
                session_id=message.session_id,
                task_id=message.task_id,
                msg_id=message.id,
                msg_from=message.sender,
                group_id=metadata.get("group_id") if metadata else None,
                sub_group_root_id=metadata.get("root_message_id") if metadata else None,
                metadata=metadata)
            self.run_node(message.id)

    def save_message_handle_result(self, name: str, message: Message, result: Message = None):
        '''
        save message handle result
        '''
        run_node_busi_type = RunNodeBusiType.from_message_category(
            message.category)
        if run_node_busi_type:
            if result and result.is_error():
                handle_result = HandleResult(
                    name=name,
                    status=RunNodeStatus.FAILED,
                    result=result)
            else:
                handle_result = HandleResult(
                    name=name,
                    status=self.get_node(message.id).status if self.get_node(message.id) else RunNodeStatus.FAILED,
                    result=result)
            self.save_result(node_id=message.id, result=handle_result)

    def end_message_node(self, message: Message):
        '''
        end node while message handle finished.
        '''
        run_node_busi_type = RunNodeBusiType.from_message_category(
            message.category)
        if run_node_busi_type:
            node = self._node_exist(node_id=message.id)
            status = RunNodeStatus.SUCCESS
            if node.results:
                for result in node.results:
                    if result.status == RunNodeStatus.FAILED:
                        status = RunNodeStatus.FAILED
                        break
            if status == RunNodeStatus.FAILED:
                self.run_failed(node_id=message.id)
            else:
                self.run_succeed(node_id=message.id)

    def get_message_node_status(self, message: Message) -> RunNodeStatus:
        node = self.get_node(node_id=message.id)
        if not node:
            return RunNodeStatus.INIT
        return node.status
