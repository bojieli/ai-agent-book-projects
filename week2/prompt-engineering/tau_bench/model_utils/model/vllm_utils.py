from typing import Any

import requests

from tau_bench.model_utils.model.general_model import wrap_temperature


def generate_request(
    url: str,
    prompt: str,
    temperature: float = 0.0,
    force_json: bool = False,
    **req_body_kwargs: Any,
) -> str:
    args = {
        "prompt": prompt,
        "temperature": wrap_temperature(temperature),
        "max_tokens": 4096,
        **req_body_kwargs,
    }
    if force_json:
        # the prompt will have a suffix of '```json\n' to indicate that the response should be a JSON object
        args["stop"] = ["```"]
    res = requests.post(
        url,
        json=args,
    )
    res.raise_for_status()
    json_res = res.json()
    if "text" not in json_res:
        raise ValueError(f"Unexpected response: {json_res}")
    elif len(json_res["text"]) == 0:
        raise ValueError(f"Empty response: {json_res}")
    text = json_res["text"][0]
    assert isinstance(text, str)
    return text.removeprefix(prompt)
