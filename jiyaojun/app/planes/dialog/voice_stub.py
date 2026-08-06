"""Voice interface stub — V1 不做全双工，但预留契约接口。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VoiceSessionStub:
    session_id: str
    status: str = "reserved_not_implemented"


class VoiceInterfaceStub:
    """03 §8: Ch9 live voice out of V1 — interface exists, operations raise."""

    def start_duplex(self, meeting_id: str) -> VoiceSessionStub:
        raise NotImplementedError("V1 does not implement full-duplex voice; interface reserved")

    def reserve(self, meeting_id: str) -> VoiceSessionStub:
        return VoiceSessionStub(session_id=f"voice_rsv_{meeting_id}", status="reserved_not_implemented")
