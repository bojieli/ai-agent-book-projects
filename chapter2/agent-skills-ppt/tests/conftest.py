"""Shared bootstrap for agent-skills-ppt regression tests."""

import sys
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS_DIR = PROJECT_ROOT / "skills" / "pptx" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    import openai  # noqa: F401
except ImportError:
    openai_stub = ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

try:
    import pptx  # noqa: F401
except ImportError:
    pptx_stub = ModuleType("pptx")
    pptx_stub.Presentation = object
    sys.modules["pptx"] = pptx_stub
