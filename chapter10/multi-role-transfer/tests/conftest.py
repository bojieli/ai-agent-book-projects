"""Shared bootstrap for multi-role-transfer regression tests."""

import sys
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import openai  # noqa: F401
except ImportError:
    openai_stub = ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub
