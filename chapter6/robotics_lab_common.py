"""Small, deterministic helpers shared by the chapter 9 robotics labs.

The labs deliberately avoid pretending that a Mac MPS run is a CUDA/ManiSkill
run.  They expose the accelerator used in the evidence and fail closed when a
caller asks for an accelerator that is not available.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch


def seed_everything(seed: int) -> None:
    """Seed every local RNG used by the self-contained experiments."""

    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def select_device(require_accelerator: bool = True) -> torch.device:
    """Prefer CUDA, then Apple MPS, and optionally reject CPU fallback."""

    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    if require_accelerator:
        raise RuntimeError("no local GPU accelerator is available (expected CUDA or Apple MPS)")
    return torch.device("cpu")


def device_info(device: torch.device) -> dict[str, Any]:
    info: dict[str, Any] = {"device": str(device), "torch": torch.__version__}
    if device.type == "cuda":
        info["name"] = torch.cuda.get_device_name(device)
        info["capability"] = list(torch.cuda.get_device_capability(device))
    elif device.type == "mps":
        info["name"] = "Apple Metal Performance Shaders"
    else:
        info["name"] = "CPU"
    return info


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())

