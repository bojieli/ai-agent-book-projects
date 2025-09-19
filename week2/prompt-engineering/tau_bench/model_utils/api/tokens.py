import json

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


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    by_primitive: dict[str, "TokenUsage"]


def batch_token_analysis(dps: list[Datapoint], encoding_for_model: str = "gpt-4o") -> TokenUsage:
    import tiktoken

    enc = tiktoken.encoding_for_model(encoding_for_model)
    # very rough estimates
    inputs_by_primitive: dict[str, list[str]] = {}
    outputs_by_primitive: dict[str, list[str]] = {}
    for dp in dps:
        input = json.dumps({k: v for k, v in dp.model_dump().items() if k != "response"})
        inputs_by_primitive.setdefault(type(dp).__name__, []).append(input)
        if isinstance(dp, ClassifyDatapoint):
            output = f'{{"classification": {dp.response}}}'
        elif isinstance(dp, BinaryClassifyDatapoint):
            output = f'{{"classification": {0 if dp.response else 1}}}'
        elif isinstance(dp, ParseForceDatapoint):
            output = (
                json.dumps(dp.response)
                if isinstance(dp.response, dict)
                else dp.response.model_dump_json()
            )
        elif isinstance(dp, GenerateDatapoint):
            output = json.dumps(dp.response)
        elif isinstance(dp, ParseDatapoint):
            output = (
                json.dumps(dp.response)
                if isinstance(dp.response, dict)
                else dp.response.model_dump_json()
            )
        elif isinstance(dp, ScoreDatapoint):
            output = f"{{'score': {dp.response}}}"
        else:
            raise ValueError(f"Unknown datapoint type: {type(dp)}")
        outputs_by_primitive.setdefault(type(dp).__name__, []).append(output)
    input_tokens_by_primitive = {}
    output_tokens_by_primitive = {}
    for primitive, inputs in inputs_by_primitive.items():
        input_tokens = sum([len(item) for item in enc.encode_batch(inputs)])
        input_tokens_by_primitive[primitive] = input_tokens
    for primitive, outputs in outputs_by_primitive.items():
        output_tokens = sum([len(item) for item in enc.encode_batch(outputs)])
        output_tokens_by_primitive[primitive] = output_tokens
    return TokenUsage(
        input_tokens=sum(input_tokens_by_primitive.values()),
        output_tokens=sum(output_tokens_by_primitive.values()),
        by_primitive={
            primitive: TokenUsage(
                input_tokens=input_tokens_by_primitive.get(primitive, 0),
                output_tokens=output_tokens_by_primitive.get(primitive, 0),
                by_primitive={},
            )
            for primitive in set(input_tokens_by_primitive.keys())
            | set(output_tokens_by_primitive.keys())
        },
    )


def token_analysis(dp: Datapoint, encoding_for_model: str = "gpt-4o") -> TokenUsage:
    return batch_token_analysis([dp], encoding_for_model)
