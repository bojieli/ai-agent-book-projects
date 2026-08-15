# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os
import traceback
import uuid
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from aworld.logs.util import logger


def load_config(file_name: str, dir_name: str = None) -> Dict[str, Any]:
    """Dynamically load config file form current path.

    Args:
        file_name: Config file name.
        dir_name: Config file directory.

    Returns:
        Config dict.
    """

    if dir_name:
        file_path = os.path.join(dir_name, file_name)
    else:
        # load conf form current path
        current_dir = Path(__file__).parent.absolute()
        file_path = os.path.join(current_dir, file_name)
    if not os.path.exists(file_path):
        logger.debug(f"{file_path} not exists, please check it.")

    configs = dict()
    try:
        with open(file_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        configs.update(yaml_data)
    except FileNotFoundError:
        logger.debug(f"Can not find the file: {file_path}")
    except Exception:
        logger.warning(f"{file_name} read fail.\n", traceback.format_exc())
    return configs


def wipe_secret_info(config: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """Return a deep copy of this config as a plain Dict as well ass wipe up secret info, used to log."""

    def _wipe_secret(conf):
        def _wipe_secret_plain_value(v):
            if isinstance(v, List):
                return [_wipe_secret_plain_value(e) for e in v]
            elif isinstance(v, Dict):
                return _wipe_secret(v)
            else:
                return v

        key_list = []
        for key in conf.keys():
            key_list.append(key)
        for key in key_list:
            if key.strip('"') in keys:
                conf[key] = '-^_^-'
            else:
                _wipe_secret_plain_value(conf[key])
        return conf

    if not config:
        return config
    return _wipe_secret(config)


class ClientType(Enum):
    SDK = "sdk"
    HTTP = "http"


class ConfigDict(dict):
    """Object mode operates dict, can read non-existent attributes through `get` method."""
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

    def __init__(self, seq: dict = None, **kwargs):
        if seq is None:
            seq = OrderedDict()
        super(ConfigDict, self).__init__(seq, **kwargs)
        self.nested(self)

    def nested(self, seq: dict):
        """Nested recursive processing dict.

        Args:
            seq: Python original format dict
        """
        for k, v in seq.items():
            if isinstance(v, dict):
                seq[k] = ConfigDict(v)
                self.nested(v)


class BaseConfig(BaseModel):
    def to_dict(self) -> ConfigDict:
        return ConfigDict(self.model_dump())


class ModelConfig(BaseConfig):
    llm_provider: str = "openai"
    llm_model_name: str = None
    llm_temperature: float = 1.
    llm_base_url: str = None
    llm_api_key: str = None
    llm_client_type: ClientType = ClientType.SDK
    llm_sync_enabled: bool = True
    llm_async_enabled: bool = True
    max_retries: int = 3
    max_model_len: Optional[int] = None  # Maximum model context length
    model_type: Optional[str] = 'qwen'  # Model type determines tokenizer and maximum length
    params: Optional[Dict[str, Any]] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # init max_model_len
        if self.max_model_len is None:
            # qwen or other default model_type
            self.max_model_len = 128000 if self.model_type != 'claude' else 200000


class LlmCompressionConfig(BaseConfig):
    enabled: bool = False
    compress_type: str = 'llm'  # llm, llmlingua
    trigger_compress_token_length: int = 10000  # Trigger compression when exceeding this length
    compress_model: Optional[ModelConfig] = Field(default=None, description="Compression model configuration")


class OptimizationConfig(BaseConfig):
    enabled: bool = False
    max_token_budget_ratio: float = 0.5  # Maximum context length ratio


class ContextRuleConfig(BaseConfig):
    """Context interference rule configuration"""

    # ===== Performance optimization configuration =====
    optimization_config: OptimizationConfig = OptimizationConfig()

    # ===== LLM conversation compression configuration =====
    llm_compression_config: LlmCompressionConfig = LlmCompressionConfig()


class AgentMemoryConfig(BaseConfig):
    """Configuration for procedural memory."""

    model_config = ConfigDict(
        from_attributes=True, validate_default=True, revalidate_instances='always', validate_assignment=True,
        arbitrary_types_allowed=True
    )
    # short-term config
    history_rounds: int = Field(default=100,
                                description="rounds of message msg; when the number of messages is greater than the history_rounds, the memory will be trimmed")
    enable_summary: bool = Field(default=False,
                                 description="enable_summary use llm to create summary short-term memory")
    summary_model: Optional[str] = Field(default=None, description="short-term summary model")
    summary_rounds: Optional[int] = Field(default=5,
                                          description="rounds of message msg; when the number of messages is greater than the summary_rounds, the summary will be created")
    summary_context_length: Optional[int] = Field(default=40960,
                                                  description=" when the content length is greater than the summary_context_length, the summary will be created")
    # summary_prompt: str = Field(default=SUMMARY_PROMPT, description="summary prompt")

    # Long-term memory config
    enable_long_term: bool = Field(default=False, description="enable_long_term use to store long-term memory")
    long_term_model: Optional[str] = Field(default=None, description="long-term extract model")
    # LongTermConfig
    long_term_config: Optional[BaseModel] = Field(default=None, description="long_term_config")


class AgentConfig(BaseConfig):
    llm_config: ModelConfig = ModelConfig()
    memory_config: AgentMemoryConfig = AgentMemoryConfig()
    context_rule: ContextRuleConfig = ContextRuleConfig()

    # default reset init in first
    need_reset: bool = True
    # use vision model
    use_vision: bool = True
    max_steps: int = 10
    max_input_tokens: int = 128000
    max_actions_per_step: int = 10
    system_prompt: Optional[str] = None
    system_prompt_template: Optional[str] = None
    agent_prompt: Optional[str] = None
    working_dir: Optional[str] = None
    enable_recording: bool = False
    use_tools_in_prompt: bool = False
    exit_on_failure: bool = False
    ext: dict = {}
    human_tools: List[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize llm_config with relevant kwargs
        llm_config_kwargs = {k: v for k, v in kwargs.items() if k in ModelConfig.model_fields}
        # Reassignment if it has llm config args
        if llm_config_kwargs or not self.llm_config:
            self.llm_config = ModelConfig(**llm_config_kwargs)

    @property
    def llm_model_name(self) -> str:
        return self.llm_config.llm_model_name

    @property
    def llm_provider(self) -> str:
        return self.llm_config.llm_provider


class TaskConfig(BaseConfig):
    task_id: str = str(uuid.uuid4())
    task_name: str | None = None
    max_steps: int = 100
    stream: bool = False
    resp_carry_context: bool = True
    exit_on_failure: bool = False
    ext: dict = {}


class ToolConfig(BaseConfig):
    name: str = None
    custom_executor: bool = False
    enable_recording: bool = False
    working_dir: str = ""
    max_retry: int = 3
    llm_config: ModelConfig = None
    reuse: bool = False
    use_async: bool = False
    exit_on_failure: bool = False
    ext: dict = {}


class EngineName:
    # Use asyncio or MultiProcess run in local
    LOCAL = "local"
    # Stateless(task) run in ray. Ray actor will use a new name
    RAY = "ray"
    SPARK = "spark"


class RunConfig(BaseConfig):
    job_name: str = "aworld_job"
    engine_name: str = EngineName.LOCAL
    worker_num: int = 1
    # engine whether to run in local
    in_local: bool = True
    # run in local whether to use the same process
    reuse_process: bool = True
    # Is the task sequence dependent
    sequence_dependent: bool = False
    # The custom implement of RuntimeEngine
    cls: Optional[str] = None
    event_bus: Optional[Dict[str, Any]] = None
    tracer: Optional[Dict[str, Any]] = None


class EvaluationConfig(BaseConfig):
    work_dir: Optional[str] = None
    run_times: int = 1
