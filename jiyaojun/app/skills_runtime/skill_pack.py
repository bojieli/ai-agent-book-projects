"""Skill Pack 元数据、schema、示例产物与成功标准加载。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


def parse_front_matter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def parse_success_criteria(skill_md: str) -> list[str]:
    """从 SKILL.md「成功标准」章节提取编号条目。"""
    if "## 成功标准" not in skill_md:
        return []
    section = skill_md.split("## 成功标准", 1)[1]
    section = section.split("##", 1)[0]
    items: list[str] = []
    for line in section.splitlines():
        m = re.match(r"^\s*\d+\.\s+(.+)$", line.strip())
        if m:
            items.append(m.group(1).strip())
    return items


@dataclass
class SkillPack:
    skill_dir: Path
    meta: dict[str, Any]
    success_criteria: list[str] = field(default_factory=list)
    example_artifact: dict[str, Any] | None = None
    payload_schema: dict[str, Any] | None = None
    schema_id: str = ""

    @classmethod
    def load(cls, skill_dir: Path) -> SkillPack:
        skill_md_path = skill_dir / "SKILL.md"
        text = skill_md_path.read_text(encoding="utf-8")
        meta = parse_front_matter(text)
        criteria = parse_success_criteria(text)

        example: dict[str, Any] | None = None
        examples_dir = skill_dir / "examples"
        if examples_dir.exists():
            for p in sorted(examples_dir.glob("*.json")):
                example = json.loads(p.read_text(encoding="utf-8"))
                break

        schema_id = ""
        payload_schema: dict[str, Any] | None = None
        if example:
            schema_id = str(example.get("schema_id", ""))
        schemas_dir = skill_dir / "schemas"
        if schema_id and schemas_dir.exists():
            schema_path = schemas_dir / f"{schema_id}.json"
            if schema_path.exists():
                payload_schema = json.loads(schema_path.read_text(encoding="utf-8"))

        return cls(
            skill_dir=skill_dir,
            meta=meta,
            success_criteria=criteria,
            example_artifact=example,
            payload_schema=payload_schema,
            schema_id=schema_id,
        )

    def build_artifact(
        self,
        *,
        meeting_id: str,
        scenario_type: str,
        skill_pack_id: str,
        org_domains: list[str],
        classification: str,
        continuum_write_class: str,
        references: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """基于示例 envelope 构造本场产物（替换 meeting 上下文）。"""
        if not self.example_artifact:
            raise ValueError(f"skill pack missing example artifact: {self.skill_dir}")
        art = json.loads(json.dumps(self.example_artifact))
        art["artifact_id"] = f"art_{meeting_id}"
        art["meeting_id"] = meeting_id
        art["scenario_type"] = scenario_type
        art["skill_pack_id"] = skill_pack_id
        art["org_domains"] = list(org_domains)
        art["classification"] = classification
        art["continuum_write_class"] = continuum_write_class
        if references is not None:
            art["references"] = references
        art["created_by_stage"] = "artifact"
        return art

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        if not self.payload_schema:
            return []
        validator = Draft202012Validator(self.payload_schema)
        return [
            f"{'/'.join(map(str, e.path))}: {e.message}"
            for e in sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
        ]
