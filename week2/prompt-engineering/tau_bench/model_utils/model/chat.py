import abc
import enum
import json
from typing import Any, TypeVar

from pydantic import BaseModel

from tau_bench.model_utils.api.datapoint import (
    BinaryClassifyDatapoint,
    ClassifyDatapoint,
    Datapoint,
    GenerateDatapoint,
    ParseDatapoint,
    ParseForceDatapoint,
    ScoreDatapoint,
)
from tau_bench.model_utils.api.types import PartialObj
from tau_bench.model_utils.model.exception import ModelError
from tau_bench.model_utils.model.general_model import GeneralModel
from tau_bench.model_utils.model.utils import (
    add_md_tag,
    clean_top_level_keys,
    display_choices,
    json_response_to_obj_or_partial_obj,
    optionalize_type,
    parse_json_or_json_markdown,
    try_classify_recover,
    type_to_json_schema_string,
)

T = TypeVar("T", bound=BaseModel)


class Role(str, enum.Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


class Message(BaseModel):
    role: Role
    content: str
    obj: dict[str, Any] | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        if self.obj is not None:
            return super().model_dump(**kwargs)
        return {"role": self.role, "content": self.content}


class PromptSuffixStrategy(str, enum.Enum):
    JSON = "json"
    JSON_MD_BLOCK = "json_md_block"


def force_json_prompt(
    text: str,
    suffix_strategy: PromptSuffixStrategy = PromptSuffixStrategy.JSON,
) -> str:
    if suffix_strategy == PromptSuffixStrategy.JSON:
        return f"{text}\n\nValid JSON:"
    elif suffix_strategy == PromptSuffixStrategy.JSON_MD_BLOCK:
        return f'{text}\n\nThe result should be a valid JSON object (according to the definition in the provided schema) in a markdown block only. For example:\nassistant:```json\n{{"items": ["value"]}}\n```'
    else:
        raise ValueError(f"Invalid suffix strategy: {suffix_strategy}")


def build_generate_state(
    instruction: str,
    text: str,
    examples: list[GenerateDatapoint] | None = None,
) -> list[Message]:
    messages = []
    if examples is not None:
        for example in examples:
            example_msgs = [
                Message(role=Role.SYSTEM, content=example.instruction),
                Message(role=Role.USER, content=example.text),
                Message(role=Role.ASSISTANT, content=example.response),
            ]
            messages.extend(example_msgs)
    messages.append(Message(role=Role.SYSTEM, content=instruction))
    messages.append(Message(role=Role.USER, content=text))
    return messages


def build_parse_force_state(
    instruction: str,
    typ: type[T] | dict[str, Any],
    text: str | None = None,
    examples: list[ParseForceDatapoint] | None = None,
    suffix_strategy: PromptSuffixStrategy = PromptSuffixStrategy.JSON,
) -> list[Message]:
    def display_sample(
        instr: str,
        ty: type[T] | dict[str, Any],
        t: str | None = None,
        response: T | dict[str, Any] | None = None,
    ) -> Message | list[Message]:
        if isinstance(ty, dict):
            json_schema_string = json.dumps(ty)
        else:
            json_schema_string = type_to_json_schema_string(ty)
        text_insert = "" if t is None else f"\n\nText:\n{t}"
        input_text = force_json_prompt(
            text=f"Instruction:\n{instr}{text_insert}\n\nSchema:\n{json_schema_string}",
            suffix_strategy=suffix_strategy,
        )
        if response is not None:
            if isinstance(response, dict):
                response_display = json.dumps(response)
            else:
                response_display = json.dumps(response.model_dump())
            return [
                Message(role=Role.USER, content=input_text),
                Message(role=Role.ASSISTANT, content=response_display),
            ]
        else:
            return Message(role=Role.USER, content=input_text)

    messages = [
        Message(
            role=Role.SYSTEM,
            content="Generate an object with the provided instruction, text, and schema.",
        ),
    ]
    if examples is not None:
        for example in examples:
            example_msgs = display_sample(
                instr=example.instruction,
                ty=example.typ,
                t=example.text,
                response=example.response,
            )
            assert isinstance(example_msgs, list) and all(
                isinstance(msg, Message) for msg in example_msgs
            )
            messages.extend(example_msgs)
    messages.append(display_sample(instr=instruction, ty=typ, t=text))
    return messages


def build_score_state(
    instruction: str,
    text: str,
    min: int,
    max: int,
    examples: list[ScoreDatapoint] | None = None,
    suffix_strategy: PromptSuffixStrategy = PromptSuffixStrategy.JSON,
) -> list[Message]:
    def display_sample(
        instr: str, t: str, mn: int, mx: int, response: int | None = None
    ) -> list[Message] | Message:
        if mn > mx:
            raise ValueError(f"Invalid range: [{mn}, {mx}]")
        input_text = force_json_prompt(
            f"Instruction:\n{instr}\n\nText:\n{t}\n\nRange:\n[{mn}, {mx}]",
            suffix_strategy,
        )
        if response is not None:
            return [
                Message(role=Role.USER, content=input_text),
                Message(role=Role.ASSISTANT, content=f'{{"score": {response}}}'),
            ]
        else:
            return Message(role=Role.USER, content=input_text)

    messages = [
        Message(
            role=Role.SYSTEM,
            content='Score the following text with the provided instruction and range as an integer value in valid JSON:\n{"score": number}',
        ),
    ]
    if examples is not None:
        for example in examples:
            example_msgs = display_sample(
                instr=example.instruction,
                t=example.text,
                mn=example.min,
                mx=example.max,
                response=example.response,
            )
            assert isinstance(example_msgs, list) and all(
                isinstance(msg, Message) for msg in example_msgs
            ), example_msgs
            messages.extend(example_msgs)
    messages.append(display_sample(instr=instruction, t=text, mn=min, mx=max))
    return messages


def build_parse_state(
    text: str,
    typ: type[T] | dict[str, Any],
    examples: list[ParseDatapoint] | None = None,
    suffix_strategy: PromptSuffixStrategy = PromptSuffixStrategy.JSON,
) -> list[Message]:
    def display_sample(
        t: str,
        ty: type[T] | dict[str, Any],
        response: T | PartialObj | dict[str, Any] | None = None,
    ) -> Message | list[Message]:
        if isinstance(ty, dict):
            json_schema_string = json.dumps(ty)
        else:
            optionalized_typ = optionalize_type(ty)
            json_schema_string = type_to_json_schema_string(optionalized_typ)
        input_text = force_json_prompt(
            f"Text:\n{t}\n\nSchema:\n{json_schema_string}",
            suffix_strategy=suffix_strategy,
        )
        if response is not None:
            if isinstance(response, dict):
                response_display = json.dumps(response)
            else:
                response_display = response.model_dump_json()
            return [
                Message(role=Role.USER, content=input_text),
                Message(role=Role.ASSISTANT, content=response_display),
            ]
        else:
            return Message(role=Role.USER, content=input_text)

    messages = [
        Message(
            role=Role.SYSTEM,
            content="Parse the following text with the provided JSON schema.",
        ),
    ]
    if examples is not None:
        for example in examples:
            example_msgs = display_sample(t=example.text, ty=typ, response=example.response)
            assert isinstance(example_msgs, list) and all(
                isinstance(msg, Message) for msg in example_msgs
            ), example_msgs
            messages.extend(example_msgs)
    messages.append(display_sample(t=text, ty=typ))
    return messages


def build_classify_state(
    instruction: str,
    text: str,
    options: list[str],
    examples: list[ClassifyDatapoint] | None = None,
    suffix_strategy: PromptSuffixStrategy = PromptSuffixStrategy.JSON,
) -> tuple[list[Message], dict[str, int]]:
    def display_sample(
        instr: str, t: str, opts: list[str], response: int | None = None
    ) -> list[Message] | tuple[Message, dict[str, int]]:
        choices_display, decode_map = display_choices(opts)
        input_text = force_json_prompt(
            f"Instruction:\n{instr}\n\nText:\n{t}\n\nChoices:\n{choices_display}",
            suffix_strategy=suffix_strategy,
        )
        if response is not None:
            response_label = None
            for label, idx in decode_map.items():
                if idx == response:
                    response_label = label
                    break
            assert response_label is not None, f"Invalid response: {response}"
            return [
                Message(role=Role.USER, content=input_text),
                Message(
                    role=Role.ASSISTANT,
                    content=f'{{"classification": "{response_label}"}}',
                ),
            ]
        else:
            return Message(role=Role.USER, content=input_text), decode_map

    messages = [
        Message(
            role=Role.SYSTEM,
            content='Classify the following text with the provided instruction and choices. To classify, provide the key of the choice:\n{"classification": string}\n\nFor example, if the correct choice is \'Z. description of choice Z\', then provide \'Z\' as the classification as valid JSON:\n{"classification": "Z"}',
        ),
    ]
    if examples is not None:
        for example in examples:
            example_msgs = display_sample(
                instr=example.instruction,
                t=example.text,
                opts=example.options,
                response=example.response,
            )
            assert isinstance(example_msgs, list) and all(
                isinstance(msg, Message) for msg in example_msgs
            ), example_msgs
            messages.extend(example_msgs)
    message, decode_map = display_sample(instr=instruction, t=text, opts=options)
    messages.append(message)
    return messages, decode_map


class ChatModel(GeneralModel):
    @abc.abstractmethod
    def generate_message(
        self, messages: list[Message], force_json: bool, temperature: float | None = None
    ) -> Message:
        raise NotImplementedError

    def handle_generate_message_response(
        self, prompt: list[dict[str, str] | Message], content: str, force_json: bool
    ) -> Message:
        if force_json:
            try:
                parsed = parse_json_or_json_markdown(content)
            except (json.JSONDecodeError, ValueError) as e:
                msgs = []
                for msg in prompt:
                    if isinstance(msg, Message):
                        msgs.append(msg.model_dump())
                    else:
                        msgs.append(msg)
                raise ModelError(
                    short_message=f"Failed to parse JSON: {content}",
                    prompt=msgs,
                    response=content,
                ) from e
            cleaned = clean_top_level_keys(parsed)
            return Message(role=Role.ASSISTANT, content=content, obj=cleaned)
        return Message(role=Role.ASSISTANT, content=content, obj=None)

    def build_generate_message_state(self, messages: list[Message]) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = []
        for msg in messages:
            if msg.obj is not None:
                content = json.dumps(msg.obj)
            else:
                content = msg.content
            msgs.append({"role": msg.role.value, "content": content})
        return msgs

    def _handle_classify_response(self, res: Message, decode_map: dict[str, int]) -> int:
        assert res.obj is not None
        if "classification" not in res.obj:
            raise ModelError(f"Invalid response from model: {res.content}")
        choice = res.obj["classification"]
        if choice not in decode_map:
            key = try_classify_recover(s=choice, decode_map=decode_map)
            if key is not None:
                return decode_map[key]
            raise ModelError(f"Invalid choice: {choice}")
        return decode_map[choice]

    def classify(
        self,
        instruction: str,
        text: str,
        options: list[str],
        examples: list[ClassifyDatapoint] | None = None,
        temperature: float | None = None,
    ) -> int:
        messages, decode_map = build_classify_state(instruction, text, options, examples=examples)
        res = self.generate_message(messages, force_json=True, temperature=temperature)
        return self._handle_classify_response(res, decode_map)

    def parse(
        self,
        text: str,
        typ: type[T] | dict[str, Any],
        examples: list[ParseDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | PartialObj | dict[str, Any]:
        messages = build_parse_state(text, typ, examples=examples)
        res = self.generate_message(messages, force_json=True, temperature=temperature)
        assert res.obj is not None
        return json_response_to_obj_or_partial_obj(response=res.obj, typ=typ)

    def generate(
        self,
        instruction: str,
        text: str,
        examples: list[GenerateDatapoint] | None = None,
        temperature: float | None = None,
    ) -> str:
        messages = build_generate_state(instruction=instruction, text=text, examples=examples)
        return self.generate_message(messages, force_json=False, temperature=temperature).content

    def _handle_parse_force_response(
        self, res: Message, typ: type[T] | dict[str, Any]
    ) -> T | dict[str, Any]:
        assert res.obj is not None
        obj = json_response_to_obj_or_partial_obj(response=res.obj, typ=typ)
        if not isinstance(typ, dict) and isinstance(obj, dict):
            raise ModelError(f"Invalid response from model: {res.content}")
        return obj

    def parse_force(
        self,
        instruction: str,
        typ: type[T] | dict[str, Any],
        text: str | None = None,
        examples: list[ParseForceDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | dict[str, Any]:
        messages = build_parse_force_state(
            instruction=instruction,
            typ=typ,
            text=text,
            examples=examples,
        )
        res = self.generate_message(messages, force_json=True, temperature=temperature)
        return self._handle_parse_force_response(res, typ)

    def _handle_score_response(
        self,
        res: Message,
        min: int,
        max: int,
    ) -> int:
        if res.obj is None or "score" not in res.obj:
            raise ModelError(f"Invalid response from model: {res.content}")
        score = res.obj["score"]
        if not isinstance(score, int):
            raise ModelError(f"Invalid score type: {type(score)}")
        if score < min or score > max:
            raise ModelError(f"Invalid score value: {score}")
        return score

    def score(
        self,
        instruction: str,
        text: str,
        min: int,
        max: int,
        examples: list[ScoreDatapoint] | None = None,
        temperature: float | None = None,
    ) -> int:
        messages = build_score_state(instruction, text, min, max, examples=examples)
        res = self.generate_message(messages, force_json=True, temperature=temperature)
        return self._handle_score_response(res, min, max)


def build_prompts(
    dps: list[Datapoint], prompt_suffix_strategy: PromptSuffixStrategy | None
) -> list[str | list[Message]]:
    if len(dps) == 0:
        return []
    typ = type(dps[0])
    for i, dp in enumerate(dps):
        if not isinstance(dp, typ):
            raise ValueError(
                f"All elements must be of type Datapoint, expected type {typ} at index {i}, got {type(dp)}"
            )
    if isinstance(dps[0], ParseDatapoint):
        build_func = build_parse_prompts
    elif isinstance(dps[0], BinaryClassifyDatapoint):
        build_func = build_binary_classify_prompts
    elif isinstance(dps[0], ClassifyDatapoint):
        build_func = build_classify_prompts
    elif isinstance(dps[0], ParseForceDatapoint):
        build_func = build_parse_force_prompts
    elif isinstance(dps[0], GenerateDatapoint):
        build_func = build_generate_prompts
    elif isinstance(dps[0], ScoreDatapoint):
        build_func = build_score_prompts
    else:
        raise ValueError(f"Unknown datapoint type: {type(dps[0])}")
    return build_func(dps, suffix_strategy=prompt_suffix_strategy)


def build_parse_prompts(
    dps: list[ParseDatapoint],
    suffix_strategy: PromptSuffixStrategy | None = None,
) -> list[str | list[Message]]:
    datapoints = []
    for dp in dps:
        json_response_object = (
            dp.response.model_dump_json()
            if isinstance(dp.response, BaseModel)
            else json.dumps(dp.response)
        )
        prompt_msgs = build_parse_state(
            text=dp.text,
            typ=dp.typ,
            suffix_strategy=(
                suffix_strategy if suffix_strategy is not None else PromptSuffixStrategy.JSON
            ),
        )
        json_response = apply_suffix_strategy(
            response=json_response_object, suffix_strategy=suffix_strategy
        )
        datapoints.append(prompt_msgs + [Message(role=Role.ASSISTANT, content=json_response)])
    return datapoints


def build_binary_classify_prompts(
    dps: list[BinaryClassifyDatapoint],
    suffix_strategy: PromptSuffixStrategy | None = None,
) -> list[str | list[Message]]:
    return build_classify_prompts(
        [
            ClassifyDatapoint(
                instruction=dp.instruction,
                text=dp.text,
                options=["true", "false"],
                response=0 if dp.response else 1,
            )
            for dp in dps
        ],
        suffix_strategy=suffix_strategy,
    )


def build_classify_prompts(
    dps: list[ClassifyDatapoint],
    suffix_strategy: PromptSuffixStrategy | None = None,
) -> list[str | list[Message]]:
    def label_idx_to_label_json(idx: int, decode_map: dict[str, int]) -> str:
        label = None
        for k, v in decode_map.items():
            if v == idx:
                label = k
                break
        if label is None:
            raise ValueError(f"Label index {idx} not found in decode map")
        return f'{{"classification": "{label}"}}'

    datapoints = []
    for dp in dps:
        suffix_strategy = PromptSuffixStrategy.JSON if suffix_strategy is None else suffix_strategy
        prompt_msgs, decode_map = build_classify_state(
            instruction=dp.instruction,
            text=dp.text,
            options=dp.options,
            suffix_strategy=suffix_strategy,
        )
        json_response_object = label_idx_to_label_json(idx=dp.response, decode_map=decode_map)
        json_response = apply_suffix_strategy(
            response=json_response_object, suffix_strategy=suffix_strategy
        )
        datapoints.append(
            prompt_msgs
            + [
                Message(
                    role=Role.ASSISTANT,
                    content=json_response,
                )
            ]
        )
    return datapoints


def build_parse_force_prompts(
    dps: list[ParseForceDatapoint],
    suffix_strategy: PromptSuffixStrategy | None = None,
) -> list[str | list[Message]]:
    datapoints = []
    for dp in dps:
        json_response_obj = (
            dp.response.model_dump_json()
            if isinstance(dp.response, BaseModel)
            else json.dumps(dp.response)
        )
        suffix_strategy = PromptSuffixStrategy.JSON if suffix_strategy is None else suffix_strategy
        prompt_msgs = build_parse_force_state(
            instruction=dp.instruction,
            text=dp.text,
            typ=dp.typ,
            suffix_strategy=suffix_strategy,
        )
        json_response = apply_suffix_strategy(
            response=json_response_obj, suffix_strategy=suffix_strategy
        )
        datapoints.append(prompt_msgs + [Message(role=Role.ASSISTANT, content=json_response)])
    return datapoints


def build_generate_prompts(dps: list[GenerateDatapoint]) -> list[str | list[Message]]:
    datapoints = []
    for dp in dps:
        prompt_msgs = build_generate_state(instruction=dp.instruction, text=dp.text)
        datapoints.append(prompt_msgs + [Message(role=Role.ASSISTANT, content=dp.response)])
    return datapoints


def build_score_prompts(
    dps: list[ScoreDatapoint],
    suffix_strategy: PromptSuffixStrategy | None = None,
) -> list[str | list[Message]]:
    datapoints = []
    for dp in dps:
        json_response_object = f'{{"score": {dp.response}}}'
        suffix_strategy = (
            suffix_strategy if suffix_strategy is not None else PromptSuffixStrategy.JSON
        )
        prompt_msgs = build_score_state(
            instruction=dp.instruction,
            text=dp.text,
            min=dp.min,
            max=dp.max,
            suffix_strategy=suffix_strategy,
        )
        json_response = apply_suffix_strategy(
            response=json_response_object, suffix_strategy=suffix_strategy
        )
        datapoints.append(prompt_msgs + [Message(role=Role.ASSISTANT, content=json_response)])
    return datapoints


def apply_suffix_strategy(response: str, suffix_strategy: PromptSuffixStrategy) -> str:
    if suffix_strategy == PromptSuffixStrategy.JSON:
        return response
    elif suffix_strategy == PromptSuffixStrategy.JSON_MD_BLOCK:
        return add_md_tag(response)
    else:
        raise ValueError(f"Unknown suffix strategy: {suffix_strategy}")
