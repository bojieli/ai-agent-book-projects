from agentbook.providers.resolution import resolve_backend


def test_resolve_backend_whitespace_model_uses_default():
    backend = resolve_backend("ollama", model="   ")
    assert backend.model == "qwen3:8b"
