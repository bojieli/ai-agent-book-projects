"""Fail-closed Docker boundary for model-generated policy code."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
from typing import Any, Iterable
import uuid


ROOT = Path(__file__).resolve().parent
DOCKERFILE = ROOT / "Dockerfile.sandbox"
RUNNER = ROOT / "sandbox_runner.py"
DEFAULT_TIMEOUT_SECONDS = 8.0
MAX_REQUEST_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 256 * 1024


class SandboxError(RuntimeError):
    """The candidate sandbox could not produce a trusted response."""


def _default_image() -> str:
    digest = hashlib.sha256(DOCKERFILE.read_bytes() + RUNNER.read_bytes()).hexdigest()[:12]
    return f"ai-agent-book/self-modifying-agent-sandbox:{digest}"


def sandbox_image() -> str:
    """Return an operator-supplied image or the content-addressed local image."""
    return os.environ.get("SELF_MODIFY_SANDBOX_IMAGE", _default_image())


@lru_cache(maxsize=None)
def _ensure_image(image: str) -> None:
    try:
        inspect_result = subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise SandboxError("Docker is required for candidate evaluation") from exc
    if inspect_result.returncode == 0:
        return
    if os.environ.get("SELF_MODIFY_SANDBOX_IMAGE"):
        raise SandboxError(f"Configured sandbox image is unavailable: {image}")
    try:
        build = subprocess.run(
            [
                "docker", "build", "--file", str(DOCKERFILE),
                "--tag", image, str(ROOT),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise SandboxError("Docker is required to build the candidate sandbox") from exc
    if build.returncode != 0:
        detail = build.stderr[-2000:].strip()
        raise SandboxError(f"Could not build candidate sandbox: {detail}")


def _docker_command(image: str, name: str) -> list[str]:
    return [
        "docker", "run", "--rm", "--interactive", "--name", name,
        "--hostname", "candidate-sandbox",
        "--network", "none",
        "--ipc", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--user", "65534:65534",
        "--pids-limit", "16",
        "--memory", "64m",
        "--memory-swap", "64m",
        "--cpus", "0.5",
        "--ulimit", "cpu=2:2",
        "--ulimit", "nofile=64:64",
        "--ulimit", "core=0:0",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
        "--workdir", "/tmp",
        "--log-driver", "none",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        image,
    ]


def _bounded_reader(stream: Any, destination: bytearray, overflow: list[bool]) -> None:
    while chunk := stream.read(8192):
        remaining = MAX_OUTPUT_BYTES - len(destination)
        if remaining > 0:
            destination.extend(chunk[:remaining])
        if len(chunk) > remaining:
            overflow[0] = True


def _remove_container(name: str) -> None:
    try:
        subprocess.run(
            ["docker", "rm", "--force", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def run_in_sandbox(
    action: str,
    source: str,
    trajectories: Iterable[dict[str, Any]],
    *,
    stable_source: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Evaluate source in a disposable, resource-limited Docker container."""
    try:
        if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise SandboxError("Candidate source exceeds 256 KiB")
        if stable_source is not None and len(stable_source.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise SandboxError("Stable source exceeds 256 KiB")
        request = json.dumps({
            "action": action,
            "source": source,
            "trajectories": list(trajectories),
            "stable_source": stable_source,
        }).encode("utf-8")
    except (TypeError, UnicodeError, ValueError) as exc:
        raise SandboxError("Candidate sandbox request is not valid JSON data") from exc
    if len(request) > MAX_REQUEST_BYTES:
        raise SandboxError("Candidate sandbox request exceeds 1 MiB")

    image = sandbox_image()
    _ensure_image(image)
    name = f"agent-candidate-{uuid.uuid4().hex}"
    try:
        process = subprocess.Popen(
            _docker_command(image, name),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise SandboxError("Docker is required for candidate evaluation") from exc

    stdout = bytearray()
    stderr = bytearray()
    stdout_overflow = [False]
    stderr_overflow = [False]
    stdout_thread = threading.Thread(
        target=_bounded_reader,
        args=(process.stdout, stdout, stdout_overflow),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_bounded_reader,
        args=(process.stderr, stderr, stderr_overflow),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    assert process.stdin is not None
    try:
        process.stdin.write(request)
        process.stdin.close()
        returncode = process.wait(timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as exc:
        _remove_container(name)
        process.kill()
        process.wait()
        if isinstance(exc, subprocess.TimeoutExpired):
            raise SandboxError("Candidate evaluation exceeded the wall-clock limit") from exc
        raise SandboxError("Candidate sandbox closed its input unexpectedly") from exc
    finally:
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)

    if stdout_overflow[0] or stderr_overflow[0]:
        raise SandboxError("Candidate sandbox output exceeded 1 MiB")
    if returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()[-1000:]
        raise SandboxError(f"Candidate sandbox exited with {returncode}: {detail}")
    try:
        response = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SandboxError("Candidate sandbox returned an invalid response") from exc
    if not isinstance(response, dict) or response.get("ok") is not True:
        raise SandboxError("Candidate sandbox rejected the evaluation request")
    result = response.get("result")
    if not isinstance(result, dict):
        raise SandboxError("Candidate sandbox response has no result object")
    return result
