"""Shared contracts for Experiment 10-5.

The contracts are deliberately serialisable: every Computer/Phone Agent exchange is
also written to the timing trace, so a run can prove what was decided and when.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FieldSpec:
    name: str
    label: str
    input_type: str = "text"
    required: bool = True
    selector: str = ""
    format_hint: str = ""
    pattern: str = ""
    options: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "FieldSpec":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in value.items() if k in allowed})

    def validate(self, value: Optional[str]) -> tuple[bool, str]:
        val = (str(value) if value is not None else "").strip()
        if self.required and not val:
            return False, "该项为必填项，不能留空"
        if not val:
            return True, ""
        if self.options and val not in self.options:
            lowered = {o.casefold(): o for o in self.options}
            if val.casefold() not in lowered:
                return False, f"请选择以下选项之一：{', '.join(self.options)}"
        if self.pattern:
            try:
                if re.fullmatch(self.pattern, val) is None:
                    return False, self.format_hint or f"格式应匹配 {self.pattern}"
            except re.error:
                # A malformed pattern from a web page must not crash the call.
                pass
        kind = self.input_type.lower()
        if kind == "email" and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", val) is None:
            return False, self.format_hint or "请输入有效邮箱，例如 name@example.com"
        if kind in {"tel", "phone"} and re.fullmatch(r"[+()\d][+()\d .-]{5,24}", val) is None:
            return False, self.format_hint or "请输入包含区号的有效电话号码"
        if kind == "date" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", val) is None:
            return False, self.format_hint or "日期格式应为 YYYY-MM-DD"
        if kind == "number":
            try:
                float(val)
            except ValueError:
                return False, self.format_hint or "请输入数字"
        return True, ""


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    type: str
    payload: Dict[str, Any]
    sequence: int = 0
    monotonic_seconds: float = 0.0
    wall_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionRecord:
    page_url: str
    page_title: str
    known_fields: List[str]
    discovered_fields: List[FieldSpec]
    tool_called: Optional[str]
    purpose: str
    required_info: List[FieldSpec]
    rationale_summary: str
    model: str
    monotonic_seconds: float
    provider: str = ""
    provider_response_id: Optional[str] = None
    provider_usage: Dict[str, int] = field(default_factory=dict)
    wall_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data
