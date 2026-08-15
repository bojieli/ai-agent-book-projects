import os
import importlib
import subprocess
import sys
import traceback
import logging
from typing import List, Dict
from aworld.cmd.data_model import AgentModel

logger = logging.getLogger(__name__)

_agent_cache: Dict[str, AgentModel] = {}


def list_agents(server_dir: str) -> Dict[str, AgentModel]:
    """
    List all cached agents

    Returns:
        Dict[str, AgentModel]: The map of agent models
    """
    if len(_agent_cache) == 0:
        for m in _list_agents(server_dir):
            _agent_cache[m.id] = m
    return _agent_cache


def _list_agents(server_dir: str) -> List[AgentModel]:
    agents_dir = os.path.join(server_dir, "agent_deploy")

    if not os.path.exists(agents_dir):
        logger.warning(f"Agents directory {agents_dir} does not exist")
        return []

    if agents_dir not in sys.path:
        sys.path.append(agents_dir)

    agents = []
    for agent_id in os.listdir(agents_dir):
        if agent_id.startswith("_"):
            continue
        try:
            agent_path = os.path.join(agents_dir, agent_id)
            if os.path.isdir(agent_path):
                requirements_file = os.path.join(agent_path, "requirements.txt")
                if os.path.exists(requirements_file):
                    p = subprocess.Popen(
                        ["pip", "install", "-U", "-r", requirements_file],
                        cwd=agent_path,
                    )
                    p.wait()
                    if p.returncode != 0:
                        logger.error(
                            f"Error installing requirements for agent {agent_id}, path {agent_path}"
                        )
                        continue

                agent_file = os.path.join(agent_path, "agent.py")
                if os.path.exists(agent_file):
                    try:
                        instance = _get_agent_instance(agent_id)
                        if hasattr(instance, "name"):
                            name = instance.name()
                        else:
                            name = agent_id
                        if hasattr(instance, "description"):
                            description = instance.description()
                        else:
                            description = ""
                        agent_model = AgentModel(
                            id=agent_id,
                            name=name,
                            description=description,
                            path=agent_path,
                            instance=instance,
                        )

                        agents.append(agent_model)
                        logger.info(
                            f"Loaded agent {agent_id} successfully, path {agent_path}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error loading agent {agent_id}: {traceback.format_exc()}"
                        )
                        continue
                else:
                    logger.warning(f"Agent {agent_id} does not have agent.py file")
        except Exception as e:
            logger.error(
                f"Error loading agent {agent_id}, path {agent_path} : {traceback.format_exc()}"
            )
            continue

    return agents


def _get_agent_instance(agent_name):
    try:
        agent_module = importlib.import_module(
            name=f"{agent_name}.agent",
        )
    except Exception as e:
        msg = f"Error loading agent {agent_name}, cwd:{os.getcwd()}, sys.path:{sys.path}: {traceback.format_exc()}"
        logger.error(msg)
        raise Exception(msg)

    if hasattr(agent_module, "AWorldAgent"):
        agent = agent_module.AWorldAgent()
        return agent
    else:
        raise Exception(f"Agent {agent_name} does not have AWorldAgent class")
