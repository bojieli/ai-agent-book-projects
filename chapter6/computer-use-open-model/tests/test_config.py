import pytest
from config import DEFAULT_BASE_URL, DEFAULT_MODEL, ConfigError, resolve_endpoint


def test_openrouter_reference_route() -> None:
    endpoint = resolve_endpoint({"OPENROUTER_API_KEY": "secret"})

    assert endpoint.api_key == "secret"
    assert endpoint.api_key_env == "OPENROUTER_API_KEY"
    assert endpoint.base_url == DEFAULT_BASE_URL
    assert endpoint.model == DEFAULT_MODEL
    assert endpoint.public_dict()["requested_model"] == DEFAULT_MODEL
    assert "secret" not in str(endpoint.public_dict())


def test_generic_endpoint_takes_precedence() -> None:
    endpoint = resolve_endpoint(
        {
            "OPEN_MODEL_API_KEY": "local",
            "OPENROUTER_API_KEY": "gateway-secret",
            "OPEN_MODEL_BASE_URL": "http://127.0.0.1:8000/v1/",
            "OPEN_MODEL_MODEL": "Qwen/Qwen3-VL-32B-Instruct",
            "OPEN_MODEL_SCHEMA_MODE": "prompt",
        }
    )

    assert endpoint.api_key == "local"
    assert endpoint.api_key_env == "OPEN_MODEL_API_KEY"
    assert endpoint.base_url == "http://127.0.0.1:8000/v1"
    assert endpoint.schema_mode == "prompt"


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({}, "OPEN_MODEL_API_KEY"),
        ({"OPEN_MODEL_API_KEY": "x", "OPEN_MODEL_BASE_URL": "localhost:8000/v1"}, "absolute"),
        ({"OPEN_MODEL_API_KEY": "x", "OPEN_MODEL_SCHEMA_MODE": "xml"}, "native"),
    ],
)
def test_invalid_configuration_fails_closed(values: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        resolve_endpoint(values)
