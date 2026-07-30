#!/usr/bin/env python3
"""Write a sanitized, fail-closed Experiment 9-2 readiness/blocker artifact."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
from datetime import datetime, timezone
from pathlib import Path

from pineclaw_tool import AUTHORIZED_NUMBER_ENV, CONSENT_ENV, CONSENT_VALUE

HERE = Path(__file__).parent


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    number = os.getenv(AUTHORIZED_NUMBER_ENV, "").strip()
    number_valid = bool(re.fullmatch(r"\+[1-9]\d{7,14}", number))
    consent_confirmed = os.getenv(CONSENT_ENV, "").strip() == CONSENT_VALUE
    credentials_in_environment = all(os.getenv(key) for key in ("PINE_ACCESS_TOKEN", "PINE_USER_ID"))
    ready = number_valid and consent_confirmed and credentials_in_environment
    artifact = {
        "schema_version": 1,
        "experiment": "9-2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "preflight_only",
        "real_call_placed": False,
        "authorized_destination": {
            "configured": bool(number),
            "valid_e164": number_valid,
            "consent_confirmed": consent_confirmed,
            "value_saved": False,
            "sha256": hashlib.sha256(number.encode()).hexdigest() if number_valid else None,
        },
        "credentials": {
            "pine_environment_pair_present": credentials_in_environment,
            "previous_gateway_authentication_evidence": "validation/credential_check.json",
            "values_saved": False,
        },
        "provenance": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "pine_voice_sdk": importlib.metadata.version("pine-voice"),
            "implementation_sha256": {
                "pineclaw_tool.py": file_sha256(HERE / "pineclaw_tool.py"),
                "agent.py": file_sha256(HERE / "agent.py"),
                "direct_call.py": file_sha256(HERE / "direct_call.py"),
            },
        },
        "acceptance": {
            "ready_to_place_authorized_calls": ready,
            "direct_call_completed": False,
            "react_call_completed": False,
            "real_transcripts_saved": False,
            "critical_fields_extracted": False,
            "direct_vs_react_compared": False,
            "passed": False,
        },
        "blocker": (
            "No explicitly authorized consenting E.164 destination is configured; no call was placed."
            if not (number_valid and consent_confirmed)
            else "The authorized destination is configured, but Pine environment credentials are absent; no call was placed."
            if not credentials_in_environment
            else "Preflight is ready, but a human must intentionally start the direct and ReAct validation calls."
        ),
    }
    output = HERE / "validation" / "preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
