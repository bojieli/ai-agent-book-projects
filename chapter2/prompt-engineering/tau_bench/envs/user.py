# Copyright Sierra

import abc
import copy
import enum
import time
from datetime import datetime, timezone
from litellm import completion

from typing import Optional, List, Dict, Any, Union


class BaseUserSimulationEnv(abc.ABC):
    metadata = {}

    @abc.abstractmethod
    def reset(self, instruction: Optional[str] = None) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def step(self, content: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_total_cost(self) -> float:
        raise NotImplementedError


class HumanUserSimulationEnv(BaseUserSimulationEnv):
    def reset(self, instruction: str) -> str:
        return input(f"{instruction}\n")

    def step(self, content: str) -> str:
        return input(f"{content}\n")

    def get_total_cost(self) -> float:
        return 0


class LLMUserSimulationEnv(BaseUserSimulationEnv):
    def __init__(self, model: str, provider: str, seed: Optional[int] = None) -> None:
        super().__init__()
        self.messages: List[Dict[str, Any]] = []
        self.model = model
        self.provider = provider
        self.seed = seed
        self.call_index = 0
        self.api_records: List[Dict[str, Any]] = []
        self.total_cost = 0.0

    def _completion(self, messages: List[Dict[str, Any]]):
        """Call the real user model and retain a credential-free receipt."""
        requested_seed = (
            self.seed + self.call_index if self.seed is not None else None
        )
        # Kimi K3 reports hidden reasoning inside the completion-token budget.
        # Difficult simulator turns can legitimately spend the first 1,024
        # tokens on reasoning and finish with empty visible content.  Give K3
        # enough room to emit the actual user reply; keep the historical bound
        # for non-reasoning user models.
        max_tokens = 4096 if "kimi-k3" in self.model.lower() else 1024
        kwargs = {
            "model": self.model,
            "custom_llm_provider": self.provider,
            "messages": messages,
            "temperature": 1 if "kimi-k3" in self.model.lower() else 0,
            "max_tokens": max_tokens,
        }
        if requested_seed is not None:
            kwargs["seed"] = requested_seed
        started = time.perf_counter()
        requested_at = datetime.now(timezone.utc).isoformat()
        try:
            res = completion(**kwargs)
        except Exception as exc:
            self.api_records.append({
                "requested_at": requested_at,
                "provider": self.provider,
                "model": self.model,
                "requested_seed": requested_seed,
                "messages": copy.deepcopy(messages),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": {"type": type(exc).__name__, "message": str(exc)},
            })
            self.call_index += 1
            raise
        choice = res.choices[0]
        usage = getattr(res, "usage", None)
        usage_payload = (
            usage.model_dump() if usage is not None and hasattr(usage, "model_dump")
            else None
        )
        hidden_cost = getattr(res, "_hidden_params", {}).get("response_cost")
        self.api_records.append({
            "requested_at": requested_at,
            "provider": self.provider,
            "model": self.model,
            "requested_seed": requested_seed,
            "messages": copy.deepcopy(messages),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "response": {
                "id": getattr(res, "id", None),
                "model": getattr(res, "model", None),
                "created": getattr(res, "created", None),
                "finish_reason": getattr(choice, "finish_reason", None),
                "content": choice.message.content,
                "reasoning_content": getattr(choice.message, "reasoning_content", None),
                "usage": usage_payload,
                "litellm_estimated_cost": hidden_cost,
            },
        })
        self.call_index += 1
        if hidden_cost is not None:
            self.total_cost += hidden_cost
        return res

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        request_messages = messages
        for attempt in range(3):
            res = self._completion(request_messages)
            message = res.choices[0].message
            content = message.content
            if isinstance(content, str) and content.strip():
                if request_messages is not self.messages:
                    # Retain the nonempty repair instruction that produced the
                    # accepted reply, while never inserting an empty assistant
                    # message that Moonshot rejects on the following request.
                    self.messages.append(request_messages[-1])
                self.messages.append(message.model_dump())
                return content
            repair = {
                "role": "user",
                "content": (
                    "Your previous simulated-user reply was empty. Return one non-empty line now, "
                    "or return ###STOP### if the user's goal is satisfied."
                ),
            }
            request_messages = copy.deepcopy(self.messages) + [repair]
        raise ValueError("User simulator returned empty content on three accepted responses")

    def get_api_records(self) -> List[Dict[str, Any]]:
        return list(self.api_records)

    def build_system_prompt(self, instruction: Optional[str]) -> str:
        instruction_display = (
            ("\n\nInstruction: " + instruction + "\n")
            if instruction is not None
            else ""
        )
        return f"""You are a user interacting with an agent.{instruction_display}
Rules:
- Just generate one line at a time to simulate the user's message.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as a standalone message without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction."""

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


class ReactUserSimulationEnv(LLMUserSimulationEnv):
    def __init__(self, model: str, provider: str, seed: Optional[int] = None) -> None:
        super().__init__(model=model, provider=provider, seed=seed)

    def build_system_prompt(self, instruction: Optional[str]) -> str:
        instruction_display = (
            ("\n\nInstruction: " + instruction + "\n")
            if instruction is not None
            else ""
        )
        return f"""You are a user interacting with an agent.{instruction_display}
Rules:
- First, generate a Thought about what to do next (this message will not be sent to the agent).
- Then, generate a one line User Response to simulate the user's message (this message will be sent to the agent).
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as the User Response without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction.

Format:

Thought:
<the thought>

User Response:
<the user response (this will be parsed and sent to the agent)>"""

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        res = self._completion(messages)
        message = res.choices[0].message
        self.messages.append(message.model_dump())
        return self.parse_response(message.content)

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def parse_response(self, response: str) -> str:
        if "###STOP###" in response:
            return "###STOP###"
        elif "Thought:" in response:
            _, user_response = response.split("Thought:")
            return user_response.strip()
        elif "User Response:" in response:
            _, user_response = response.split("User Response:")
            return user_response.strip()
        else:
            raise ValueError(f"Invalid response format: {response}")

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


class VerifyUserSimulationEnv(LLMUserSimulationEnv):
    def __init__(self, model: str, provider: str, max_attempts: int = 3,
                 seed: Optional[int] = None) -> None:
        super().__init__(model=model, provider=provider, seed=seed)
        self.max_attempts = max_attempts

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        attempts = 0
        cur_message = None
        while attempts < self.max_attempts:
            res = self._completion(messages)
            cur_message = res.choices[0].message
            if verify(self.model, self.provider, cur_message, messages):
                self.messages.append(cur_message.model_dump())
                return cur_message.content
            attempts += 1
        assert cur_message is not None
        return cur_message.content

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


def map_role_label(role: str) -> str:
    if role == "user":
        return "Customer"
    elif role == "assistant":
        return "Agent"
    else:
        return role.capitalize()


def verify(
    model: str, provider: str, response: str, messages: List[Dict[str, Any]]
) -> bool:
    transcript = "\n".join(
        [
            f"{map_role_label(message['role'])}: {message['content']}"
            for message in messages
        ]
    )
    prompt = f"""You are a supervisor of the Agent in the conversation. You are given a Transcript of a conversation between a Customer and an Agent. The Customer has generated a Response, and you need to verify if it is satisfactory (true) or not (false).
Your answer will be parsed, so do not include any other text than the classification (true or false).
    
# Transcript:
{transcript}

# Response:
{response}

-----

Classification:"""
    res = completion(
        model=model,
        custom_llm_provider=provider,
        messages=[{"role": "user", "content": prompt}],
    )
    return "true" in res.choices[0].message.content.lower()


def reflect(
    model: str, provider: str, response: str, messages: List[Dict[str, Any]]
) -> str:
    transcript = "\n".join(
        [
            f"{map_role_label(message['role'])}: {message['content']}"
            for message in messages
        ]
    )
    prompt = f"""You are a supervisor of the Agent in the conversation. You are given a Transcript of a conversation between a (simulated) Customer and an Agent. The Customer generated a Response that was marked as unsatisfactory by you.
You need to generate a Reflection on what went wrong in the conversation, and propose a new Response that should fix the issues.
Your answer will be parsed, so do not include any other text than the classification (true or false).
    
# Transcript:
{transcript}

# Response:
{response}

# Format:

Reflection:
<the reflection>

Response:
<the response (this will be parsed and sent to the agent)>"""
    res = completion(
        model=model,
        custom_llm_provider=provider,
        messages=[{"role": "user", "content": prompt}],
    )
    _, response = res.choices[0].message.content.split("Response:")
    return response.strip()


class ReflectionUserSimulationEnv(LLMUserSimulationEnv):
    def __init__(self, model: str, provider: str, max_attempts: int = 2,
                 seed: Optional[int] = None) -> None:
        super().__init__(model=model, provider=provider, seed=seed)
        self.max_attempts = max_attempts

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        cur_messages = messages.copy()
        initial_response = super().generate_next_message(cur_messages)
        if verify(self.model, self.provider, initial_response, cur_messages):
            return initial_response
        attempts = 1
        while attempts < self.max_attempts:
            new_message = reflect(
                self.model, self.provider, initial_response, cur_messages
            )
            cur_messages.append({"role": "user", "content": new_message})
            new_response = super().generate_next_message(cur_messages)
            if verify(self.model, self.provider, new_response, cur_messages):
                return new_response
            attempts += 1
        return initial_response

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


class UserStrategy(enum.Enum):
    HUMAN = "human"
    LLM = "llm"
    REACT = "react"
    VERIFY = "verify"
    REFLECTION = "reflection"


def load_user(
    user_strategy: Union[str, UserStrategy],
    model: Optional[str] = "gpt-4o",
    provider: Optional[str] = None,
    seed: Optional[int] = None,
) -> BaseUserSimulationEnv:
    if isinstance(user_strategy, str):
        user_strategy = UserStrategy(user_strategy)
    if user_strategy == UserStrategy.HUMAN:
        return HumanUserSimulationEnv()
    elif user_strategy == UserStrategy.LLM:
        if model is None:
            raise ValueError("LLM user strategy requires a model")
        if provider is None:
            raise ValueError("LLM user strategy requires a model provider")
        return LLMUserSimulationEnv(model=model, provider=provider, seed=seed)
    elif user_strategy == UserStrategy.REACT:
        if model is None:
            raise ValueError("React user strategy requires a model")
        if provider is None:
            raise ValueError("React user strategy requires a model provider")
        return ReactUserSimulationEnv(model=model, provider=provider, seed=seed)
    elif user_strategy == UserStrategy.VERIFY:
        if model is None:
            raise ValueError("Verify user strategy requires a model")
        if provider is None:
            raise ValueError("Verify user strategy requires a model provider")
        return VerifyUserSimulationEnv(model=model, provider=provider, seed=seed)
    elif user_strategy == UserStrategy.REFLECTION:
        if model is None:
            raise ValueError("Reflection user strategy requires a model")
        if provider is None:
            raise ValueError("Reflection user strategy requires a model provider")
        return ReflectionUserSimulationEnv(model=model, provider=provider, seed=seed)
    raise ValueError(f"Unknown user strategy {user_strategy}")
