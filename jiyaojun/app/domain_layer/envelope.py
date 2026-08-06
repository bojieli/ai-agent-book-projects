"""ArtifactEnvelope validation — SoT: samples/schemas/artifact_envelope.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def envelope_schema_path() -> Path:
    # prefer symlink in domain_layer, fallback to docs
    here = Path(__file__).resolve().parent
    link = here / "artifact_envelope.json"
    if link.exists():
        return link
    return (
        here.parents[3]
        / "docs"
        / "meeting-assistant"
        / "samples"
        / "schemas"
        / "artifact_envelope.json"
    )


_validator: Draft202012Validator | None = None


def get_envelope_validator() -> Draft202012Validator:
    global _validator
    if _validator is None:
        schema = json.loads(envelope_schema_path().read_text(encoding="utf-8"))
        _validator = Draft202012Validator(schema)
    return _validator


def validate_envelope(doc: dict[str, Any]) -> list[str]:
    errs = sorted(get_envelope_validator().iter_errors(doc), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in errs]
