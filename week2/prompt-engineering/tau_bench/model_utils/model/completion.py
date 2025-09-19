import abc
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
    add_md_close_tag,
    approx_num_tokens,
    display_choices,
    json_response_to_obj_or_partial_obj,
    optionalize_type,
    parse_json_or_json_markdown,
    try_classify_recover,
    type_to_json_schema_string,
)

T = TypeVar("T", bound=BaseModel)


class Score(BaseModel):
    score: int


class Classification(BaseModel):
    classification: str


def task_prompt(task: str, text: str) -> str:
    return f"# Task\n{task}\n\n{text}"


def force_json_prompt(text: str, with_prefix: bool = False) -> str:
    suffix = (
        'For example:\nassistant:```json\n{"key": "value"}\n```'
        if not with_prefix
        else "\n\n```json\n"
    )
    return f"{text}\n\nThe result should be a valid JSON object in a markdown block only. {suffix}"


def build_score_state(
    instruction: str,
    text: str,
    min: int,
    max: int,
    examples: list[ScoreDatapoint] | None = None,
) -> str:
    def display_sample(instr: str, t: str, min: int, max: int, response: int | None = None) -> str:
        p = task_prompt(
            task='Score the following text with the provided instruction and range as an integer value in valid JSON:\n{"score": number}',
            text=force_json_prompt(
                f"Instruction:\n{instr}\n\nText:\n{t}\n\nRange:\n[{min}, {max}]",
                with_prefix=True,
            ),
        )
        if response is not None:
            # the json markdown block is opened in the prompt
            return f'{p}\n{{"score": {response}}}\n```'
        return p

    p = (
        "\n\n".join(
            [display_sample(ex.instruction, ex.text, min, max, ex.response) for ex in examples]
        )
        if examples is not None
        else ""
    )
    return f"{p}\n\n{display_sample(instr=instruction, t=text, min=min, max=max)}"


def build_parse_force_state(
    instruction: str,
    typ: type[T] | dict[str, Any],
    text: str | None = None,
    examples: list[ParseForceDatapoint] | None = None,
) -> str:
    def display_sample(
        instr: str,
        t: str,
        ty: type[T] | dict[str, Any],
        response: T | dict[str, Any] | None = None,
    ) -> str:
        if isinstance(ty, dict):
            json_schema_string = json.dumps(ty)
        else:
            json_schema_string = type_to_json_schema_string(ty)
        text_insert = "" if t is None else f"\n\nText:\n{t}"
        input_text = force_json_prompt(
            text=f"Instruction:\n{instr}{text_insert}\n\nSchema:\n{json_schema_string}",
            with_prefix=True,
        )
        if response is not None:
            if isinstance(response, dict):
                response_display = json.dumps(response)
            else:
                response_display = response.model_dump_json()
            # the json markdown block is opened in the prompt
            return f"{input_text}\n{response_display}\n```"
        return input_text

    p = (
        "".join(
            [
                display_sample(
                    instr=ex.instruction,
                    t=ex.text,
                    ty=ex.typ,
                    response=ex.response,
                )
                for ex in examples
            ]
        )
        + "\n\n"
        if examples is not None and len(examples) > 0
        else ""
    )
    p += display_sample(instr=instruction, t=text, ty=typ)
    return task_prompt(
        task="Generate an object with the provided instruction, text, and schema.",
        text=p,
    )


def build_parse_state(
    text: str,
    typ: type[T] | dict[str, Any],
    examples: list[ParseDatapoint] | None = None,
) -> str:
    instruction = "Parse the following text with the provided JSON schema."

    def display_sample(
        t: str,
        ty: type[T] | dict[str, Any],
        response: T | PartialObj | dict[str, Any] | None = None,
    ) -> str:
        if isinstance(ty, dict):
            json_schema_string = json.dumps(ty)
        else:
            optionalized_typ = optionalize_type(ty)
            json_schema_string = type_to_json_schema_string(optionalized_typ)
        # instruction is repeated to emphasize the task
        prompt = task_prompt(
            task=instruction,
            text=force_json_prompt(
                f"Text:\n{t}\n\nSchema:\n{json_schema_string}", with_prefix=True
            ),
        )
        if response is None:
            return prompt
        if isinstance(response, dict):
            response_display = json.dumps(response)
        else:
            response_display = response.model_dump_json()
        # the json markdown block is opened in the prompt
        json_response = f"{response_display}\n```"
        return f"{prompt}\n{json_response}"

    p = ""
    if examples is not None and len(examples) > 0:
        p = "\n\n".join(
            [display_sample(t=ex.text, ty=ex.typ, response=ex.response) for ex in examples]
        )
    return f"{p}\n\n{display_sample(t=text, ty=typ)}"


def build_classify_state(
    instruction: str,
    text: str,
    options: list[str],
    examples: list[ClassifyDatapoint] | None = None,
) -> tuple[str, dict[str, int]]:
    def display_sample(
        instr: str, t: str, opts: list[str], response: int | None = None
    ) -> str | tuple[str, dict[str, int]]:
        choices_display, decode_map = display_choices(opts)
        input_text = force_json_prompt(
            f"Instruction:\n{instr}\n\nText:\n{t}\n\nChoices:\n{choices_display}",
            with_prefix=True,
        )
        prompt = task_prompt(task=instr, text=input_text)
        if response is not None:
            label = None
            for k, v in decode_map.items():
                if v == response:
                    label = k
                    break
            assert label is not None
            # the json markdown block is opened in the prompt
            json_display = f'{{"classification": "{label}"}}\n```'
            return f"{prompt}\n{json_display}"
        return prompt, decode_map

    p = 'Classify the following text with the provided instruction and choices. To classify, provide the key of the choice:\n{"classification": string}\n\nFor example, if the correct choice is \'Z. description of choice Z\', then provide \'Z\' as the classification as valid JSON:\n```json\n{"classification": "Z"}\n```'
    if examples is not None and len(examples) > 0:
        example_displays = "\n\n".join(
            [
                display_sample(
                    instr=ex.instruction,
                    t=ex.text,
                    opts=ex.options,
                    response=ex.response,
                )
                for ex in examples
            ]
        )
        p += f"\n\n{example_displays}"
    prompt, decode_map = display_sample(instr=instruction, t=text, opts=options)
    return f"{p}\n\n{prompt}", decode_map


def build_generate_state(
    instruction: str,
    text: str,
    examples: list[GenerateDatapoint] | None = None,
) -> str:
    def display_sample(instr: str, t: str, response: str | None = None) -> str:
        prompt = task_prompt(task=instr, text=t)
        if response is not None:
            return f"{prompt}\n\nText: {response}"
        return prompt

    prompt = (
        "\n\n".join([display_sample(ex.instruction, ex.text) for ex in examples]) + "\n\n"
        if examples is not None and len(examples) > 0
        else ""
    )
    return f"{prompt}\n\n{display_sample(instruction, text)}\n\nText:"


class CompletionModel(GeneralModel):
    @abc.abstractmethod
    def generate_from_prompt(self, prompt: str, temperature: float | None = None) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def parse_force_from_prompt(
        self, prompt: str, typ: BaseModel | dict[str, Any], temperature: float | None = None
    ) -> dict[str, Any]:
        raise NotImplementedError

    def handle_parse_force_response(self, prompt: str, content: str) -> dict[str, Any]:
        try:
            return parse_json_or_json_markdown(content)
        except (json.decoder.JSONDecodeError, ValueError) as e:
            raise ModelError(
                short_message=f"Failed to decode JSON: {content}", prompt=prompt, response=content
            ) from e

    def _handle_classify_response(self, res: dict[str, int], decode_map: dict[str, int]) -> int:
        if "classification" not in res:
            raise ModelError(f"Invalid response from model: {res}")
        choice = res["classification"]
        if choice not in decode_map.keys():
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
        prompt, decode_map = build_classify_state(instruction, text, options, examples=examples)
        res = self.parse_force_from_prompt(prompt, typ=Classification, temperature=temperature)
        return self._handle_classify_response(res, decode_map)

    def parse(
        self,
        text: str,
        typ: type[T] | dict[str, Any],
        examples: list[ParseDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | PartialObj | dict[str, Any]:
        prompt = build_parse_state(text, typ, examples=examples)
        res = self.parse_force_from_prompt(prompt=prompt, typ=typ, temperature=temperature)
        return json_response_to_obj_or_partial_obj(response=res, typ=typ)

    def generate(
        self,
        instruction: str,
        text: str,
        examples: list[GenerateDatapoint] | None = None,
        temperature: float | None = None,
    ) -> str:
        prompt = build_generate_state(instruction=instruction, text=text, examples=examples)
        return self.generate_from_prompt(prompt=prompt, temperature=temperature)

    def _handle_parse_force_response(self, res: dict[str, Any], typ: type[T]) -> T:
        obj = json_response_to_obj_or_partial_obj(response=res, typ=typ)
        if isinstance(obj, dict):
            raise ModelError(f"Invalid response from model: {res}")
        return obj

    def parse_force(
        self,
        instruction: str,
        typ: type[T] | dict[str, Any],
        text: str | None = None,
        examples: list[ParseForceDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | dict[str, Any]:
        prompt = build_parse_force_state(
            instruction=instruction, text=text, typ=typ, examples=examples
        )
        res = self.parse_force_from_prompt(prompt=prompt, typ=typ, temperature=temperature)
        return self._handle_parse_force_response(res, typ)

    def _handle_score_response(
        self,
        res: dict[str, Any],
        min: int,
        max: int,
    ) -> int:
        if res is None or "score" not in res:
            raise ModelError(f"Invalid response from model: {res}")
        score = res["score"]
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
        prompt = build_score_state(instruction, text, min, max, examples=examples)
        res = self.parse_force_from_prompt(prompt=prompt, typ=Score, temperature=temperature)
        return self._handle_score_response(res, min, max)


def build_prompts(dps: list[Datapoint], include_response: bool = True) -> list[str]:
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
    return build_func(dps, include_response)


def build_parse_prompts(
    dps: list[ParseDatapoint],
    include_response: bool = True,
) -> list[str]:
    datapoints = []
    for dp in dps:
        json_response_object = (
            dp.response.model_dump_json()
            if isinstance(dp.response, BaseModel)
            else json.dumps(dp.response)
        )
        prompt = build_parse_state(text=dp.text, typ=dp.typ)
        if include_response:
            json_response = add_md_close_tag(json_response_object)
            datapoints.append(prompt + json_response)
        else:
            datapoints.append(prompt)
    return datapoints


def build_binary_classify_prompts(
    dps: list[BinaryClassifyDatapoint],
    include_response: bool = True,
) -> list[str]:
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
        include_response=include_response,
    )


def build_classify_prompts(
    dps: list[ClassifyDatapoint],
    include_response: bool = True,
) -> list[str]:
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
        prompt, decode_map = build_classify_state(
            instruction=dp.instruction, text=dp.text, options=dp.options
        )
        if include_response:
            json_response_object = label_idx_to_label_json(idx=dp.response, decode_map=decode_map)
            json_response = add_md_close_tag(json_response_object)
            datapoints.append(prompt + json_response)
        else:
            datapoints.append(prompt)
    return datapoints


def build_parse_force_prompts(
    dps: list[ParseForceDatapoint],
    include_response: bool = True,
) -> list[str]:
    datapoints = []
    for dp in dps:
        json_response_obj = (
            dp.response.model_dump_json()
            if isinstance(dp.response, BaseModel)
            else json.dumps(dp.response)
        )
        prompt = build_parse_force_state(
            instruction=dp.instruction,
            text=dp.text,
            typ=dp.typ,
        )
        if include_response:
            json_response = add_md_close_tag(json_response_obj)
            datapoints.append(prompt + json_response)
        else:
            datapoints.append(prompt)
    return datapoints


def build_generate_prompts(
    dps: list[GenerateDatapoint], include_response: bool = True
) -> list[str]:
    datapoints = []
    for dp in dps:
        prompt = build_generate_state(instruction=dp.instruction, text=dp.text)
        if include_response:
            datapoints.append(prompt + dp.response)
        else:
            datapoints.append(prompt)
    return datapoints


def build_score_prompts(
    dps: list[ScoreDatapoint],
    include_response: bool = True,
) -> list[str]:
    datapoints = []
    for dp in dps:
        json_response_object = f'{{"score": {dp.response}}}'
        prompt = build_score_state(
            instruction=dp.instruction,
            text=dp.text,
            min=dp.min,
            max=dp.max,
        )
        if include_response:
            json_response = add_md_close_tag(json_response_object)
            datapoints.append(prompt + json_response)
        else:
            datapoints.append(prompt)
    return datapoints


# TODO: handle examples
def approx_prompt_str(dp: Datapoint, include_response: bool = False) -> str:
    return build_prompts(dps=[dp], include_response=include_response)[0]


# TODO: handle examples
def approx_cost_for_datapoint(
    dp: Datapoint,
    price_per_input_token: float,
) -> float:
    """For now, we approximate the cost of a datapoint as the cost of the input (output tokens are priced as input tokens as well)."""
    prompt = approx_prompt_str(dp, include_response=True)
    assert isinstance(prompt, str)
    return price_per_input_token * approx_num_tokens(prompt)


# TODO: handle examples
def approx_latency_for_datapoint(dp: Datapoint, latency_ms_per_output_token: float) -> float:
    if isinstance(dp, BinaryClassifyDatapoint) or isinstance(dp, ClassifyDatapoint):
        approx_response = '{"classification": 0}'
    elif isinstance(dp, ParseDatapoint):
        # this is extremely approximate
        approx_response = '{"street": "main st", "city": "san francisco", "state": "CA"}'
    elif isinstance(dp, GenerateDatapoint):
        # this is extremely approximate
        approx_response = "This is a generated text response."
    elif isinstance(dp, ParseForceDatapoint):
        # this is extremely approximate
        approx_response = '{"street": "main st", "city": "san francisco", "state": "CA"}'
    elif isinstance(dp, ScoreDatapoint):
        approx_response = '{"score": 0}'
    else:
        raise ValueError(f"Unsupported datapoint type: {type(dp)}")
    return latency_ms_per_output_token * approx_num_tokens(approx_response)
