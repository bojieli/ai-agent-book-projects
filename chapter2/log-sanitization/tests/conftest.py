"""Shared bootstrap for log-sanitization regression tests."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import ollama  # noqa: F401
except ImportError:
    ollama_stub = ModuleType("ollama")
    ollama_stub.Client = object
    sys.modules["ollama"] = ollama_stub

try:
    import dotenv  # noqa: F401
except ImportError:
    sys.modules["dotenv"] = SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)
