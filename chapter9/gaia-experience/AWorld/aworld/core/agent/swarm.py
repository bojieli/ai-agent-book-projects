# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from collections import OrderedDict
from enum import Enum
from typing import Dict, List, Any, Callable, Optional, Tuple, Iterator, Union

from aworld.core.agent.agent_desc import agent_handoffs_desc
from aworld.core.agent.base import AgentFactory, BaseAgent
from aworld.core.common import ActionModel, Observation
from aworld.core.context.base import Context
from aworld.core.exceptions import AWorldRuntimeException as AworldException, AWorldRuntimeException
from aworld.logs.util import logger
from aworld.utils.common import new_instance, convert_to_subclass


class GraphBuildType(Enum):
    WORKFLOW = "workflow"
    # Collaborative
    HANDOFF = "handoff"
    # Coordination
    TEAM = "team"


class Swarm(object):
    """Swarm is the multi-agent topology of AWorld, a collection of autonomous agents working together to
    solve complex problems through collaboration or competition.

    Swarm supports the key paradigms of workflow and handoff, and it satisfies the construction of various
    agent graphs, including DAG and DCG, such as star, tree, mesh, ring, and hybrid topology.
    """

    def __init__(self,
                 *args,  # agent
                 topology: List[tuple] = None,
                 root_agent: Union[BaseAgent, List[BaseAgent]] = None,
                 max_steps: int = 0,
                 register_agents: List[BaseAgent] = None,
                 build_type: GraphBuildType = GraphBuildType.WORKFLOW,
                 builder_cls: str = None,
                 keep_build_type: bool = True,
                 event_driven: bool = True):
        """Swarm init.

        Args:
            topology: Agent topology definition.
            root_agent: Communication agent of swarm, and it is the first executing agent.
            max_steps: Maximum number of iterations.
            register_agents: Only used for agents registered to swarm, not for topology structures.
            build_type: The construction type of topology, different construction types execute differently.
            builder_cls: Custom topology class, must comply with the protocol of TopologyBuilder.
            keep_build_type: Whether to maintain the build type set.
                             If value is False, the build type will be automatically recognized for special topologies.
                             For example, a star topology will automatically assume that it should be built by TeamBuilder.
            event_driven: Should event driven be used. Do not modify this parameter.
        """
        self._communicate_agent: Union[BaseAgent, List[BaseAgent]] = None
        if topology:
            self.topology = topology
        else:
            self.topology = list(args)

        logger.debug(f"{type(self)}Swarm Agent List is : {[type(agent) for agent in self.topology]}")

        self.setting_build_type(build_type)
        self.register_agents = register_agents
        self.max_steps = max_steps
        self._cur_step = 0
        self._event_driven = event_driven
        self.build_type = build_type.value
        if builder_cls:
            self.builder = new_instance(builder_cls, self)
        else:
            self.builder = BUILD_CLS.get(self.build_type)(topology=self.topology,
                                                          root_agent=root_agent,
                                                          keep_build_type=keep_build_type)

        self.agent_graph: AgentGraph = None

        # global tools
        self.tools = []
        self.task = ''
        self.initialized: bool = False
        self._finished: bool = False

    def setting_build_type(self, build_type: GraphBuildType):
        all_pair = True
        for agent in self.topology:
            if isinstance(agent, (list, tuple)):
                if len(agent) != 2:
                    all_pair = False
            elif isinstance(agent, (BaseAgent, Swarm)):
                all_pair = False
            else:
                raise AworldException(
                    f"Unknown type {type(agent)}, supported list, tuple, Agent only.")

        # team and workflow support mixing individual agents and agent lists.
        if build_type == GraphBuildType.HANDOFF and not all_pair:
            raise AworldException(
                'The type of `handoff` requires all pairs to appear.')

        for agent in self.topology:
            if isinstance(agent, Swarm):
                continue

            if isinstance(agent, BaseAgent):
                agent = [agent]
            for a in agent:
                if not isinstance(agent, BaseAgent):
                    continue
                if a and a.event_driven:
                    self._event_driven = True
                    break

    def reset(self, content: Any = None, context: Context = None, tools: List[str] = None):
        """Resets the initial internal state, and init supported tools in agent in swarm.

        Args:
            tools: Tool names that all agents in the swarm can use.
        """
        # can use the tools in the agents in the swarm as a global
        if self.initialized:
            logger.warning(f"swarm {self} already init")
            return

        self.tools = tools if tools else []
        # origin task
        self.task = content

        # build graph
        agent_graph: AgentGraph = self.builder.build()

        if not agent_graph.agents:
            logger.warning("No valid agent in swarm.")
            return

        self.build_type = agent_graph.build_type
        _ = agent_graph.topological_sequence()
        # Coordination mode, ordered_agents only requires the master node
        if self.build_type == GraphBuildType.TEAM.value:
            agent_graph.ordered_agents.clear()
            agent_graph.ordered_agents.append(agent_graph.root_agent)

        # Workflow cannot have cycles. For simple loops, you can use `LoopableAgent`.
        # And there can only be one start node without in-degree and one end node without out-degree.
        if self.build_type == GraphBuildType.WORKFLOW.value:
            if agent_graph.has_cycle:
                raise AworldException("Workflow unsupported cycle graph.")
            if agent_graph.node_in_degree(agent_graph.ordered_agents[0]) > 0:
                raise AworldException("The first agent of workflow has input node.")
            if agent_graph.node_out_degree(agent_graph.ordered_agents[-1]) > 0:
                raise AworldException("The last agent of workflow has output node.")

        # Agent that communicate with the outside world, the default is the first if the root agent is None.
        if not self._communicate_agent:
            self._communicate_agent = agent_graph.root_agent
        self.cur_agent = self.communicate_agent
        self.agent_graph = agent_graph

        if context is None:
            context = Context()

        for agent in agent_graph.agents.values():
            agent.event_driven = self.event_driven
            if not agent.task:
                agent.task = self.task
            if hasattr(agent, 'need_reset') and agent.need_reset:
                agent.context = context
                agent.reset()
            # global tools
            agent.tool_names.extend(self.tools)

        Swarm.register_agent(list(self.agent_graph.agents.values()))
        Swarm.register_agent(self.register_agents)
        self.cur_step = 1
        self.initialized = True

    @staticmethod
    def register_agent(agents: List[BaseAgent]) -> None:
        """Agent list register to the AgentFactory."""
        if not agents:
            return

        for agent in agents:
            logger.info(f"register_agent: {type(agent)}: {agent.id()}")
            if agent.id() not in AgentFactory:
                AgentFactory._cls[agent.id()] = agent.__class__
                AgentFactory._desc[agent.id()] = agent.desc()
                AgentFactory._agent_conf[agent.id()] = agent.conf
                AgentFactory._agent_instance[agent.id()] = agent
            else:
                if agent.id() not in AgentFactory._agent_instance:
                    AgentFactory._agent_instance[agent.id()] = agent
                if agent.desc():
                    AgentFactory._desc[agent.id()] = agent.desc()

    def find_agents_by_prefix(self, name, find_all=False):
        """Fild the agent list by the prefix name.

        Args:
            name: The agent prefix name.
            find_all: Find the total agents or the first match agent.
        """
        import re

        res = []
        for k, agent in self.agents.items():
            val = re.split(r"---uuid\w{6}uuid", k)[0]
            if name == val:
                res.append(agent)
                if not find_all:
                    return res
        return res

    def _check(self):
        if not self.initialized:
            self.reset('')

    def handoffs_desc(self, agent_name: str = None, use_all: bool = False):
        """Get agent description by name for handoffs.

        Args:
            agent_name: Agent unique name.
        Returns:
            Description of agent dict.
        """
        self._check()
        agent: BaseAgent = self.agents.get(agent_name, None)
        return agent_handoffs_desc(agent, use_all)

    def action_to_observation(self, policy: List[ActionModel], observation: List[Observation], strategy: str = None):
        """Based on the strategy, transform the agent's policy into an observation, the case of the agent as a tool.

        Args:
            policy: Agent policy based some messages.
            observation: History of the current observable state in the environment.
            strategy: Transform strategy, default is None. enum?
        """
        self._check()

        if not policy:
            logger.warning("no agent policy, will return origin observation.")
            # get the latest one
            if not observation:
                raise RuntimeError(
                    "no observation and policy to transform in swarm, please check your params.")
            return observation[-1]

        if not strategy:
            # default use the first policy
            policy_info = policy[0].policy_info

            if not observation:
                res = Observation(content=policy_info)
            else:
                res = observation[-1]
                if not res.content:
                    res.content = policy_info or ""

            return res
        else:
            logger.warning(f"{strategy} not supported now.")

    def supported_tools(self):
        """Tool names that can be used by all agents in Swarm."""
        self._check()
        return self.tools

    @property
    def has_cycle(self):
        self._check()
        return self.agent_graph.has_cycle

    def loop_agent(self,
                   agent: BaseAgent,
                   max_run_times: int,
                   loop_point: str = None,
                   loop_point_finder: Callable[..., Any] = None,
                   stop_func: Callable[..., Any] = None):
        """Loop execution of the flow.

        Args:
            agent: The agent.
            max_run_times: Maximum number of loops.
            loop_point: Loop point of the desired execution.
            loop_point_finder: Strategy function for obtaining execution loop point.
            stop_func: Termination function.
        """
        from aworld.agents.loop_llm_agent import LoopableAgent

        if agent not in self.ordered_agents:
            raise RuntimeError(
                f"{agent.id()} not in swarm, agent instance {agent}.")

        loop_agent: LoopableAgent = convert_to_subclass(agent, LoopableAgent)
        # loop_agent: LoopableAgent = type(LoopableAgent)(agent)
        loop_agent.max_run_times = max_run_times
        loop_agent.loop_point = loop_point
        loop_agent.loop_point_finder = loop_point_finder
        loop_agent.stop_func = stop_func

        idx = self.ordered_agents.index(agent)
        self.ordered_agents[idx] = loop_agent

    def save(self, filepath: str):
        """Serialize topology structure to storage."""
        self._check()

    def load(self, filepath: str):
        """Load topology structure from the file."""
        self._check()

    @property
    def agents(self):
        self._check()

        agents = self.agent_graph.agents
        if self.register_agents:
            for agent in self.register_agents:
                agents[agent.id()] = agent
        return agents

    @property
    def ordered_agents(self):
        self._check()
        return self.agent_graph.ordered_agents

    @property
    def communicate_agent(self) -> Union[BaseAgent, List[BaseAgent]]:
        return self._communicate_agent

    @communicate_agent.setter
    def communicate_agent(self, agent: Union[BaseAgent, List[BaseAgent]]):
        self._communicate_agent = agent

    @property
    def event_driven(self):
        return self._event_driven

    @event_driven.setter
    def event_driven(self, event_driven):
        self._event_driven = event_driven

    @property
    def cur_step(self) -> int:
        return self._cur_step

    @cur_step.setter
    def cur_step(self, step):
        self._cur_step = step

    @property
    def finished(self) -> bool:
        """Need all agents in a finished state."""
        self._check()
        if not self._finished:
            self._finished = all(
                [agent.finished for _, agent in self.agents.items()])
        return self._finished

    @finished.setter
    def finished(self, finished):
        self._finished = finished


class WorkflowSwarm(Swarm):
    """Workflow Paradigm."""

    def __init__(self,
                 *args,  # agent
                 topology: List[tuple] = None,
                 root_agent: BaseAgent = None,
                 max_steps: int = 0,
                 register_agents: List[BaseAgent] = None,
                 builder_cls: str = None,
                 event_driven: bool = True):
        super().__init__(*args,
                         topology=topology,
                         root_agent=root_agent,
                         max_steps=max_steps,
                         register_agents=register_agents,
                         build_type=GraphBuildType.WORKFLOW,
                         builder_cls=builder_cls,
                         event_driven=event_driven)


class TeamSwarm(Swarm):
    """Coordination paradigm."""

    def __init__(self,
                 *args,  # agent
                 topology: List[tuple] = None,
                 root_agent: BaseAgent = None,
                 max_steps: int = 0,
                 register_agents: List[BaseAgent] = None,
                 builder_cls: str = None,
                 event_driven: bool = True):
        super().__init__(*args,
                         topology=topology,
                         root_agent=root_agent,
                         max_steps=max_steps,
                         register_agents=register_agents,
                         build_type=GraphBuildType.TEAM,
                         builder_cls=builder_cls,
                         event_driven=event_driven)


class HandoffSwarm(Swarm):
    """Collaborative paradigm."""

    def __init__(self,
                 *args,  # agent
                 topology: List[tuple] = None,
                 max_steps: int = 0,
                 register_agents: List[BaseAgent] = None,
                 builder_cls: str = None,
                 event_driven: bool = True):
        super().__init__(*args,
                         topology=topology,
                         max_steps=max_steps,
                         register_agents=register_agents,
                         build_type=GraphBuildType.HANDOFF,
                         builder_cls=builder_cls,
                         event_driven=event_driven)


class EdgeInfo:
    def __init__(self,
                 condition: Optional[Callable[..., Any]] = None,
                 weight: float = 0.):
        self.condition = condition
        self.weight = weight


class AgentGraph:
    """The agent's graph is a directed graph, and can update the topology at runtime."""

    def __init__(self,
                 build_type: str,
                 root_agent: BaseAgent = None,
                 ordered_agents: List[BaseAgent] = None,
                 agents: Dict[str, BaseAgent] = None,
                 predecessor: Dict[str, Dict[str, EdgeInfo]] = None,
                 successor: Dict[str, Dict[str, EdgeInfo]] = None):
        """Agent graph init.

        Args:
            ordered_agents: Agents ordered.
            agents: Agent nodes.
            predecessor: The direct predecessor of the agent.
            successor: The direct successor of the agent.
        """
        self.build_type = build_type
        self.ordered_agents = ordered_agents if ordered_agents else []
        self.agents: OrderedDict = agents if agents else OrderedDict()
        self.predecessor = predecessor if predecessor else {}
        self.successor = successor if successor else {}
        self.has_cycle = False
        self.root_agent = root_agent

    def topological_sequence(self) -> List[List[str]]:
        """Obtain the agent sequence of topology, and be able to determine whether the topology has cycle during the process.

        Returns:
            Topological sequence and whether it is a cycle topology, False represents DAG, True represents DCG.
        """
        in_degree = dict(filter(lambda k: k[1] > 0, self.in_degree().items()))
        zero_list = [v[0] for v in list(filter(lambda k: k[1] == 0, self.in_degree().items()))]

        res = []
        while zero_list:
            tmp = zero_list
            zero_list = []
            for agent_id in tmp:
                if agent_id not in self.agents:
                    raise RuntimeError("Agent topology changed during iteration")

                for key, _ in self.successor.get(agent_id).items():
                    try:
                        in_degree[key] -= 1
                    except KeyError as err:
                        raise RuntimeError("Agent topology changed during iteration")

                    if in_degree[key] == 0:
                        zero_list.append(key)
                        del in_degree[key]
            res.append(tmp)

        if in_degree:
            logger.info("Agent topology contains cycle!")
            # sequence may be incomplete
            res.clear()
            self.has_cycle = True

        if not self.ordered_agents:
            for agent_ids in res:
                for agent_id in agent_ids:
                    self.ordered_agents.append(self.agents[agent_id])

        if not self.root_agent:
            if self.ordered_agents:
                self.root_agent = self.ordered_agents[0]
            else:
                self.root_agent = list(self.agents.values())[0]

        # workflow root agent can be a list
        if self.build_type == GraphBuildType.WORKFLOW.value:
            zero_list = [v[0] for v in list(filter(lambda k: k[1] == 0, self.in_degree().items()))]
            agents = []
            for agent_id in zero_list:
                agents.append(self.agents.get(agent_id))
            self.root_agent = agents
        return res

    def add_node(self, agent: BaseAgent):
        if not agent:
            raise AworldException("agent is None, can not build the graph.")

        if agent.id() not in self.agents:
            self.agents[agent.id()] = agent
            self.successor[agent.id()] = {}
            self.predecessor[agent.id()] = {}
        else:
            logger.info(f"{agent.id()} already in agent graph.")

    def add_nodes(self, *args):
        for agent in args:
            if not isinstance(agent, BaseAgent):
                raise AworldException("params is not a agent instance.")

            self.add_node(agent)

    def del_node(self, agent: BaseAgent):
        if not agent or agent.id() not in self.agents:
            return

        self.ordered_agents.remove(agent)
        del self.agents[agent.id()]

        successor = self.successor.get(agent.id(), {})
        for key, _ in successor.items():
            del self.predecessor[key][agent.id()]
        del self.successor[agent.id()]

        for key, _ in self.predecessor.get(agent.id(), {}):
            del self.successor[key][agent.id()]
        del self.predecessor[agent.id()]

    def add_edge(self, left_agent: BaseAgent, right_agent: BaseAgent, edge_info: EdgeInfo = EdgeInfo()):
        """Adding an edge between the left and the right agent means establishing the relationship
        between these two agents.

        Args:
            left_agent: As the agent node of the predecessor node.
            right_agent: As the agent node of the successor node.
            edge_info: Edge info between the agents.
        """
        if left_agent and left_agent.id() not in self.agents:
            raise RuntimeError(f"{left_agent.id()} not in agents node.")
        if right_agent and right_agent.id() not in self.agents:
            raise RuntimeError(f"{right_agent.id()} not in agents node.")

        if left_agent.id() not in self.successor:
            self.successor[left_agent.id()] = {}
            self.predecessor[left_agent.id()] = {}

        if right_agent.id() not in self.successor:
            self.successor[right_agent.id()] = {}
            self.predecessor[right_agent.id()] = {}

        self.successor[left_agent.id()][right_agent.id()] = edge_info
        self.predecessor[right_agent.id()][left_agent.id()] = edge_info

    def remove_edge(self, left_agent: BaseAgent, right_agent: BaseAgent):
        """Removing an edge between the left and the right agent means removing the relationship
        between these two agents.

        Args:
            left_agent: As the agent node of the predecessor node.
            right_agent: As the agent node of the successor node.
        """
        if left_agent.id() in self.successor and right_agent.id() in self.successor[left_agent.id()]:
            del self.successor[left_agent.id()][right_agent.id()]
        if right_agent.id() in self.predecessor and left_agent.id() in self.successor[right_agent.id()]:
            del self.predecessor[right_agent.id()][left_agent.id()]

    def in_degree(self) -> Dict[str, int]:
        """In degree map of the agent is the number of agents pointing to the agent."""
        in_degree = {}
        for k, _ in self.agents.items():
            agents = self.predecessor[k]
            in_degree[k] = len(agents.values())
        return in_degree

    def node_in_degree(self, node: BaseAgent) -> int:
        """In degree of the agent is the number of agents pointing to the node."""

        agents = self.predecessor.get(node.id())
        if agents is None:
            logger.warning(f"{node.id()} not in graph.")
            return -1
        return len(agents.values())

    def out_degree(self) -> Dict[str, int]:
        """Out degree map of the agent is the number of agents pointing out of the agent."""
        out_degree = {}
        for k, _ in self.agents.items():
            agents = self.successor[k]
            out_degree[k] = len(agents.values())
        return out_degree

    def node_out_degree(self, node: BaseAgent) -> int:
        """Out degree of the agent is the number of agents pointing to the node."""

        agents = self.successor.get(node.id())
        if agents is None:
            logger.warning(f"{node.id()} not in graph.")
            return -1
        return len(agents.values())


class TopologyBuilder:
    """Multi-agent topology base builder."""
    __metaclass__ = abc.ABCMeta

    def __init__(self,
                 topology: List[Union[BaseAgent, Swarm, list, tuple]],
                 root_agent: Union[BaseAgent, List[BaseAgent], Swarm] = None,
                 keep_build_type: bool = True):
        self.topology = topology
        self.root_agent = self._norm_agent(root_agent)
        self.standard_format: bool = self._standard_format(topology)
        self.keep_type: bool = keep_build_type

        if not self._valid_check():
            raise AWorldRuntimeException(f"root_agent {self.root_agent} in swarm check is invalid.")

    @abc.abstractmethod
    def build(self) -> AgentGraph:
        """Build a multi-agent topology diagram using custom build strategies or syntax."""

    def _valid_check(self) -> bool:
        """Validity detection of topology, different build types of topology in generally different detections."""

        return True

    def _standard_format(self, topology: List[Union[BaseAgent, Swarm, list, tuple]]) -> bool:
        """Check if the topology is in a standard format, where all agent pairs are in the topology."""
        standard = True
        for agent in topology:
            if not isinstance(agent, tuple):
                standard = False
                break
        return standard

    def _norm_agent(
            self,
            agent: Union[BaseAgent, List[BaseAgent], Swarm] = None
    ) -> Union[BaseAgent, List[BaseAgent], None]:
        """Standardize the agent, such as use swarm as an agent."""
        if isinstance(agent, list):
            agent = self._to_parallel_agent(agent)
            return agent.agents
        elif isinstance(agent, Swarm):
            return self._to_task_agent(swarm=agent)
        else:
            return agent

    def _to_parallel_agent(self, agents: list):
        """Agent wrapped with `ParallelizableAgent`, used to support agents parallel or a mix of serial-parallel."""
        from aworld.agents.parallel_llm_agent import ParallelizableAgent

        single_agents = []
        for one in agents:
            if isinstance(one, Swarm):
                one = self._to_task_agent(one)
            single_agents.append(one)
        return ParallelizableAgent(name=f"parallel_{'_'.join([agent.name() for agent in agents])}",
                                   agents=single_agents)

    def _to_serial_agent(self, agents: list):
        """Agent wrapped with `SerialableAgent`, used to support a mix of serial-parallel."""
        from aworld.agents.serial_llm_agent import SerialableAgent

        single_agents = []
        for one in agents:
            if isinstance(one, Swarm):
                one = self._to_task_agent(one)
            single_agents.append(one)
        return SerialableAgent(name=f"serial_{'_'.join([agent.name() for agent in agents])}",
                               agents=single_agents)

    def _to_task_agent(self, swarm: Swarm):
        """Nested swarm wrapped with `TaskAgent`, used to support mixed topology."""
        from aworld.agents.task_llm_agent import TaskAgent

        return TaskAgent(name=f"swarm_{swarm.build_type}", swarm=swarm)

    def _is_star(self, single_agents: list) -> bool:
        # special process, identify whether it is a star topology
        same_agent = True
        last = None
        for agent in single_agents:
            if not last:
                last = agent[0].id()
            else:
                if last != agent[0].id():
                    same_agent = False
                    break
        return same_agent


class WorkflowBuilder(TopologyBuilder):
    """Workflow mechanism, workflow is a deterministic process orchestration where each node must execute.

    There are three forms supported by the workflow builder: single agent, tuple of paired agents, and agent list.
    Examples:
    >>> agent1 = Agent(name='agent1'); agent2 = Agent(name='agent2'); agent3 = Agent(name='agent3')
    >>> agent4 = Agent(name='agent4'); agent5 = Agent(name='agent5'); agent6 = Agent(name='agent6')
    >>> agent7 = Agent(name='agent7'); agent8 = Agent(name='agent8')
    >>> Swarm(agent1, [(agent2, (agent4, [agent6, agent7])), (agent3, agent5)], agent8)

    This is a rather complex example, with an overall topology of:
                   ┌────── agent1 ──────┐
              ┌── agent2              agent3
      ┌───agent4────┐                  ┌┘
    agent6        agent7             agent5
      └─────────────└──────agent8───────┘

    The meaning of the topology is that after agent1 completes execution, agent2 and agent3 are executed in parallel,
    but agent3 and agent5 are executed sequentially, and agent2 and agent4 are also executed in sequentially,
    then agent6 and agent7 are executed in parallel after the sequential execution of agent2 and agent4, and
    agent8 is executed after completion.
    """

    def _valid_check(self) -> bool:
        from aworld.agents.task_llm_agent import TaskAgent

        def __check(verify_agent):
            for idx, agent in enumerate(self.topology):
                if isinstance(agent, tuple):
                    val = isinstance(agent[0], Swarm) and isinstance(verify_agent, TaskAgent)
                    if verify_agent == agent[0] or (val and verify_agent.swarm.topology == agent[0].topology):
                        self.topology.__setitem__(idx, (verify_agent, agent[1]))
                        return True
                elif isinstance(agent, list):
                    if verify_agent in agent:
                        return True
                elif isinstance(agent, Swarm):
                    if isinstance(verify_agent, TaskAgent) and verify_agent.swarm.topology == agent.topology:
                        self.topology.__setitem__(idx, verify_agent)
                        return True
                else:
                    if verify_agent == agent:
                        return True
            return False

        if not self.root_agent:
            return True

        if isinstance(self.root_agent, list):
            valid_list = []
            for one_agent in self.root_agent:
                valid_list.append(__check(one_agent))
            return all(valid_list)
        else:
            return __check(self.root_agent)

    def _secondary_check(self, agent_graph: AgentGraph, agent: Union[BaseAgent, List[BaseAgent]]):
        def __check(one_agent: BaseAgent):
            in_degree = agent_graph.node_in_degree(one_agent)
            if in_degree > 0:
                raise AWorldRuntimeException(f"{one_agent.id()} is not the start node in agent graph.")

        if not agent:
            return
        if isinstance(agent, BaseAgent):
            __check(agent)
        else:
            [__check(one) for one in agent]

    def build(self):
        """Built as workflow, different forms will be internally constructed as different agents,
        such as ParallelizableAgent, SerialableAgent or LoopableAgent.

        Returns:
            Direct topology diagram (AgentGraph) of the agents.
        """
        if self.standard_format:
            # All are node pairs
            return self._standard_build()
        else:
            return self._opt_build()

    def _standard_build(self):
        agent_graph = AgentGraph(GraphBuildType.WORKFLOW.value, root_agent=self.root_agent)
        for agent_pair in self.topology:
            pair = []
            for agent in agent_pair:
                if isinstance(agent, Swarm):
                    agent = self._to_task_agent(swarm=agent)
                pair.append(agent)
                agent_graph.add_node(agent)
            agent_graph.add_edge(pair[0], pair[1])

        # secondary check，in-degree of all agent in root_agent must be 0.
        self._secondary_check(agent_graph, self.root_agent)
        return agent_graph

    def _opt_build(self):
        if isinstance(self.root_agent, list):
            raise AWorldRuntimeException("root_agent can not be a list in opt mode.")

        agent_graph = AgentGraph(GraphBuildType.WORKFLOW.value, root_agent=self.root_agent)
        single_agents = []
        for agent in self.topology:
            if isinstance(agent, (BaseAgent, Swarm, list, tuple)):
                single_agents.append(agent)
            else:
                raise RuntimeError(f"agent in {agent} is not a agent or agent tuple or list, please check it.")

        if not single_agents:
            raise RuntimeError(f"no valid agent in swarm to build execution graph.")

        if not self.keep_type and self._is_star(single_agents):
            # star topology means team
            builder = TeamBuilder(self.topology, self.root_agent, [], self.keep_type)
            return builder.build()

        last_agent = None
        for agent in single_agents:
            if isinstance(agent, BaseAgent):
                agent_graph.add_node(agent)
            elif isinstance(agent, Swarm):
                task_agent = self._to_task_agent(agent)
                agent_graph.add_node(task_agent)
                agent = task_agent
            elif isinstance(agent, tuple):
                agents = self._flatten_agent(agent)
                serial_agent = self._to_serial_agent(agents)
                agent_graph.add_node(serial_agent)
                agent = serial_agent
            else:
                agents = self._flatten_agent(agent)
                parallel_agent = self._to_parallel_agent(agents)
                agent_graph.add_node(parallel_agent)
                agent = parallel_agent

            if last_agent:
                agent_graph.add_edge(last_agent, agent)
            last_agent = agent
        return agent_graph

    def _flatten_agent(self, agents: Union[tuple, list]) -> List[BaseAgent]:
        """Flatten the nesting of agents and recursively construct corresponding agents."""

        res_agents = []
        for agent in agents:
            if isinstance(agent, BaseAgent):
                res_agents.append(agent)
            if isinstance(agent, Swarm):
                task_agent = self._to_task_agent(agent)
                res_agents.append(task_agent)
            elif isinstance(agent, tuple) and len(agent) > 0:
                flatten_agents = self._flatten_agent(agent)
                s_agent = self._to_serial_agent(flatten_agents)
                res_agents.append(s_agent)
            elif isinstance(agent, list) and len(agent) > 0:
                flatten_agents = self._flatten_agent(agent)
                p_agent = self._to_parallel_agent(flatten_agents)
                res_agents.append(p_agent)
        return res_agents


class HandoffBuilder(TopologyBuilder):
    """Handoff mechanism using agents as tools, but during the runtime,
    the agent remains an independent entity with a state.

    Handoffs builder only supports tuple of paired agents forms.
    Examples:
    >>> agent1 = Agent(name='agent1'); agent2 = Agent(name='agent2'); agent3 = Agent(name='agent3')
    >>> agent4 = Agent(name='agent4'); agent5 = Agent(name='agent5'); agent6 = Agent(name='agent6')
    >>> Swarm((agent1, agent2), (agent1, agent3), (agent2, agent3), build_type=GraphBuildType.HANDOFF)

    If the topology is constructed in this way, it will be automatically recognized as team swarm.
    >>> Swarm((agent1, agent2), (agent1, agent3), (agent1, agent4), (agent1, agent5), build_type=GraphBuildType.HANDOFF)
    So the star topology will be built and executed in a team swarm.
    """

    def _valid_check(self) -> bool:
        from aworld.agents.task_llm_agent import TaskAgent

        if isinstance(self.root_agent, list):
            raise AWorldRuntimeException("`root_agent` can not a list in handoff swarm.")

        if not self.standard_format:
            logger.warning("Handoff swarm format must is the standard agent pair format")
            return False

        if not self.root_agent:
            return True

        if isinstance(self.root_agent, TaskAgent):
            for idx, agent in enumerate(self.topology):
                if isinstance(agent[0], Swarm) and self.root_agent.swarm.topology == agent.topology:
                    self.topology.__setitem__(idx, (self.root_agent, agent[1]))
                    return True
        else:
            for idx, agent in enumerate(self.topology):
                if self.root_agent == agent[0]:
                    return True

        logger.warning(f"root agent {self.root_agent.id()} must in the swarm.")
        return False

    def build(self):
        """Build a graph in pairs, with the right agent serving as the tool on the left.

        Using pure AI to drive the flow of the entire topology diagram, one agent's decision
        hands off control to another. Agents may be fully connected or circular, depending
        on the defined pairs of agents.

        Returns:
            Direct topology diagram (AgentGraph) of the agents.
        """
        valid_agent_pair = []
        for pair in self.topology:
            if not isinstance(pair, (list, tuple)):
                raise RuntimeError(f"{pair} is not a tuple or list value, please check it.")
            if len(pair) != 2:
                raise RuntimeError(f"{pair} is not a pair, please check it.")

            valid_agent_pair.append(pair)

        if not valid_agent_pair:
            raise RuntimeError(f"no valid agent pair to build execution graph.")

        if not self.keep_type and self._is_star(valid_agent_pair):
            # star topology means team
            builder = TeamBuilder(self.topology, self.root_agent, [], self.keep_type)
            return builder.build()

        # agent handoffs graph build.
        agent_graph = AgentGraph(GraphBuildType.HANDOFF.value, root_agent=self.root_agent)
        for agent_pair in valid_agent_pair:
            pair = []
            for agent in agent_pair:
                if isinstance(agent, Swarm):
                    agent = self._to_task_agent(swarm=agent)
                agent.feedback_tool_result = True

                pair.append(agent)
                agent_graph.add_node(agent)
            agent_graph.add_edge(pair[0], pair[1])
            # explicitly set handoffs in the agent
            pair[0].handoffs.append(pair[1].id())
            if pair[1].id() in pair[1].handoffs:
                pair[1].handoffs.remove(pair[1].id())

        return agent_graph


class TeamBuilder(TopologyBuilder):
    """Team mechanism requires a leadership agent, and other agents follow its command.
    If there is interaction between agents other than the leadership agent, they need to explicitly
    set `agent_names` themselves or use a tuple with two agents.

    Team builder supported form of single agent, tuple of paired agents, and agent list, similar to workflow.
    Examples:
    >>> agent1 = Agent(name='agent1'); agent2 = Agent(name='agent2'); agent3 = Agent(name='agent3')
    >>> agent4 = Agent(name='agent4'); agent5 = Agent(name='agent5'); agent6 = Agent(name='agent6')
    >>> Swarm(agent1, agent2, agent3, (agent4, agent5), agent6, build_type=GraphBuildType.TEAM)

    The topology means that agent1 is the leader agent, and agent2, agent3, agent6, agent4 are executors of agent1.
    Note that here is different from that of workflow, instead of executing the sequence of agent4 and agent5,
    agent5 as a tool of agent4.

    Using the `root_agent` parameter, will obtain the same topology as above.
    >>> Swarm(agent2, agent3, (agent4, agent5), agent6, root_agent=agent1, build_type=GraphBuildType.TEAM)
    >>> Swarm(agent1, agent2, agent3, (agent4, agent5), agent6, root_agent=agent1, build_type=GraphBuildType.TEAM)
    """

    def _valid_check(self) -> bool:
        from aworld.agents.task_llm_agent import TaskAgent

        if isinstance(self.root_agent, list):
            raise AWorldRuntimeException("`root_agent` can not a list in team swarm.")

        if not self.root_agent:
            return True

        for idx, agent in enumerate(self.topology):
            if isinstance(agent, Swarm):
                # agent is Swarm, root agent need is a TaskAgent
                if isinstance(self.root_agent, TaskAgent) and self.root_agent.swarm.topology == agent.topology:
                    self.topology.__setitem__(idx, self.root_agent)
                    return True
            elif isinstance(agent, tuple):
                # agent is tuple of agent or swarm, root agent need is an Agent or TaskAgent
                if self.root_agent == agent[0]:
                    return True

                val = isinstance(agent[0], Swarm) and isinstance(self.root_agent, TaskAgent)
                if val and self.root_agent.swarm.topology == agent[0].topology:
                    self.topology.__setitem__(idx, (self.root_agent, agent[1]))
                    return True
            elif self.root_agent == agent:
                return True

        # root agent not in the topology, add it to the first
        logger.info(f"root agent not in the swarm, will add it.")
        self.topology.insert(0, self.root_agent)
        return True

    def build(self):
        agent_graph = AgentGraph(GraphBuildType.TEAM.value, root_agent=self.root_agent)
        valid_agents = []
        root_agent = self.topology[0]
        if isinstance(root_agent, tuple):
            valid_agents.append(root_agent)
            root_agent = root_agent[0]
        if isinstance(root_agent, Swarm):
            root_agent = self._to_task_agent(root_agent)
        agent_graph.add_node(root_agent)
        root_agent.feedback_tool_result = True

        single_agents = []
        for agent in self.topology[1:]:
            if isinstance(agent, (BaseAgent, Swarm)):
                single_agents.append(agent)
            elif isinstance(agent, tuple):
                valid_agents.append(agent)
            else:
                raise RuntimeError(f"agent in {agent} is not a agent or agent list, please check it.")

        if not valid_agents and not single_agents:
            raise RuntimeError(f"no valid agent in swarm to build execution graph.")

        for agent in single_agents:
            if isinstance(root_agent, Swarm):
                agent = self._to_task_agent(agent)

            agent.feedback_tool_result = True
            agent_graph.add_node(agent)
            agent_graph.add_edge(root_agent, agent)

            root_agent.handoffs.append(agent.id())
            if agent.id() in agent.handoffs:
                agent.handoffs.remove(agent.id())

        for pair in valid_agents:
            left_agent = pair[0]
            if isinstance(left_agent, Swarm):
                left_agent = self._to_task_agent(left_agent)

            left_agent.feedback_tool_result = True
            agent_graph.add_nodes(left_agent)
            if len(pair) > 1:
                right_agent = pair[1]
                if isinstance(right_agent, Swarm):
                    right_agent = self._to_task_agent(right_agent)

                right_agent.feedback_tool_result = True
                agent_graph.add_nodes(right_agent)

            if left_agent != root_agent:
                agent_graph.add_edge(root_agent, left_agent)
                root_agent.handoffs.append(left_agent.id())
                if left_agent.id() in left_agent.handoffs:
                    left_agent.handoffs.remove(left_agent.id())
            else:
                # right agent must not None
                agent_graph.add_edge(root_agent, right_agent)
                root_agent.handoffs.append(right_agent.id())
                if right_agent.id() in right_agent.handoffs:
                    right_agent.handoffs.remove(right_agent.id())
        return agent_graph


BUILD_CLS = {
    GraphBuildType.WORKFLOW.value: WorkflowBuilder,
    GraphBuildType.HANDOFF.value: HandoffBuilder,
    GraphBuildType.TEAM.value: TeamBuilder,
}
