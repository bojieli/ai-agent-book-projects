"""
Evidence manifest 的构建与校验（离线可测）。

manifest 记录每条路线每次运行的完整证据：输入、改写结果、
图片相对路径与 SHA-256、模型与 provider、token 用量。
"""

import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_VERSION = "1.0"
EXPERIMENT_ID = "1-4"
CANONICAL_SOURCE = "book/chapter1.md#实验-1-4-文生图工作流与原生图像生成的对照"

# manifest 必备字段（tests 离线校验用）
MANIFEST_REQUIRED_KEYS = [
    "schema_version",
    "experiment_id",
    "evidence_mode",
    "created_at",
    "canonical_source",
    "credential_value_recorded",
    "host",
    "repository",
    "requirements",
    "runs",
]
RUN_REQUIRED_KEYS = [
    "requirement_id",
    "route",
    "input",
    "nodes",
    "image",
    "error",
]
IMAGE_REQUIRED_KEYS = ["path", "sha256", "bytes", "mime"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def host_info() -> Dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": sys.version.replace("\n", " "),
        "machine": platform.machine(),
    }


def repo_info(project_root: Path) -> Dict[str, Any]:
    """只读地采集 git 信息；不在 git 仓库里时降级为 unknown。"""

    def _git(args: List[str]) -> str:
        try:
            out = subprocess.run(
                ["git", *args],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return out.stdout.strip()
        except Exception:
            return ""

    return {
        "commit": _git(["rev-parse", "HEAD"]) or "unknown",
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        "worktree_dirty": bool(_git(["status", "--porcelain"])),
    }


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    """离线校验 manifest 结构，返回问题列表（空列表表示通过）。"""
    problems: List[str] = []
    for key in MANIFEST_REQUIRED_KEYS:
        if key not in manifest:
            problems.append(f"manifest 缺少字段: {key}")
    if manifest.get("credential_value_recorded") is not False:
        problems.append("credential_value_recorded 必须为 false（不允许记录密钥值）")

    req_ids = {r.get("id") for r in manifest.get("requirements", [])}
    for i, run in enumerate(manifest.get("runs", [])):
        for key in RUN_REQUIRED_KEYS:
            if key not in run:
                problems.append(f"runs[{i}] 缺少字段: {key}")
        if run.get("requirement_id") not in req_ids:
            problems.append(f"runs[{i}].requirement_id 未在 requirements 中登记")
        valid_routes = ("workflow", "native", "native_gptimage")
        if run.get("route") not in valid_routes:
            problems.append(f"runs[{i}].route 必须是 {'/'.join(valid_routes)}")
        image = run.get("image")
        if run.get("error") is None:
            if not isinstance(image, dict):
                problems.append(f"runs[{i}] 成功运行必须有 image 记录")
            else:
                for key in IMAGE_REQUIRED_KEYS:
                    if key not in image:
                        problems.append(f"runs[{i}].image 缺少字段: {key}")
                digest = image.get("sha256", "")
                if not (isinstance(digest, str) and len(digest) == 64):
                    problems.append(f"runs[{i}].image.sha256 必须是 64 位十六进制")
        for j, node in enumerate(run.get("nodes", [])):
            calls = node.get("calls") or ([node["call"]] if "call" in node else [])
            if not calls:
                problems.append(f"runs[{i}].nodes[{j}] 没有任何 call record")
            for call in calls:
                for key in ("provider", "model", "started_at", "status"):
                    if key not in call:
                        problems.append(f"runs[{i}].nodes[{j}] call 缺少字段: {key}")
    return problems


def build_manifest(
    requirements: List[Dict[str, str]],
    runs: List[Dict[str, Any]],
    project_root: Path,
    notes: List[str],
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "evidence_mode": "real_api",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_source": CANONICAL_SOURCE,
        "credential_source_env": [
            "KIMI_API_KEY",
            "DASHSCOPE_API_KEY",
            "GEMINI_API_KEY",
        ],
        "credential_value_recorded": False,
        "host": host_info(),
        "repository": repo_info(project_root),
        "requirements": requirements,
        "runs": runs,
        "notes": notes,
    }
