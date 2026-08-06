#!/usr/bin/env python3
"""验证本地 Core 基础设施并输出机器可读结果。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPOSE = ROOT / "deploy" / "local" / "docker-compose.yml"
DEFAULT_ENV = ROOT / "deploy" / "local" / ".env"
EXAMPLE_ENV = ROOT / "deploy" / "local" / ".env.example"


def load_env_file(path: Path) -> dict[str, str]:
    """读取简单 KEY=VALUE 文件；不解析 shell 表达式，也不覆盖进程环境。"""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def run_command(command: list[str], *, timeout: float) -> tuple[bool, str]:
    """执行无交互命令并返回经过裁剪的诊断文本。"""
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (completed.stdout or completed.stderr).strip()
    return completed.returncode == 0, output[-1000:]


def check_http(url: str, *, timeout: float) -> dict[str, Any]:
    """检查 HTTP 健康端点；只记录状态，不输出响应中的潜在敏感内容。"""
    started = time.monotonic()
    try:
        request = Request(url, headers={"User-Agent": "meeting-assistant-health/1"})
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - 本地固定端点
            status = int(response.status)
        return {
            "ok": 200 <= status < 300,
            "status": status,
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }
    except HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "error": f"http_{exc.code}",
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }
    except (URLError, OSError) as exc:
        return {
            "ok": False,
            "error": str(exc.reason if isinstance(exc, URLError) else exc),
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }


def check_tcp(host: str, port: int, *, timeout: float) -> dict[str, Any]:
    """检查 TCP 端口是否可连接。"""
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {
                "ok": True,
                "latency_ms": round((time.monotonic() - started) * 1000, 2),
            }
    except OSError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }


def check_redis(host: str, port: int, *, timeout: float) -> dict[str, Any]:
    """使用 Redis RESP 协议发送 PING，避免依赖本机 redis-cli。"""
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout) as conn:
            conn.sendall(b"*1\r\n$4\r\nPING\r\n")
            response = conn.recv(64)
        ok = response.startswith(b"+PONG")
        return {
            "ok": ok,
            "response": "PONG" if ok else "unexpected",
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }
    except OSError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }


def compose_command(compose_file: Path, env_file: Path, *args: str) -> list[str]:
    """生成统一的 Docker Compose 命令，确保所有检查使用同一环境文件。"""
    return [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(compose_file),
        *args,
    ]


def verify(args: argparse.Namespace) -> dict[str, Any]:
    """运行全部检查；Docker 不可用时仍检查端点并返回完整诊断。"""
    env_file = args.env_file
    env_values = load_env_file(env_file)

    def value(name: str, default: str) -> str:
        return os.getenv(name, env_values.get(name, default))

    result: dict[str, Any] = {
        "ok": False,
        "compose_file": str(args.compose_file),
        "env_file": str(env_file),
        "docker": {},
        "services": {},
    }

    docker_ok, docker_detail = run_command(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        timeout=args.timeout,
    )
    result["docker"] = {
        "ok": docker_ok,
        "server_version": docker_detail if docker_ok else None,
        "error": None if docker_ok else (docker_detail or "docker_daemon_unavailable"),
    }

    if docker_ok:
        compose_ok, compose_detail = run_command(
            compose_command(args.compose_file, env_file, "ps", "--format", "json"),
            timeout=args.timeout,
        )
        result["docker"]["compose_ps_ok"] = compose_ok
        if not compose_ok:
            result["docker"]["compose_ps_error"] = compose_detail

    host = value("PLATFORM_HOST", "127.0.0.1")
    postgres_port = int(value("PLATFORM_POSTGRES_PORT", "55432"))
    redis_port = int(value("PLATFORM_REDIS_PORT", "56379"))
    seaweed_port = int(value("PLATFORM_SEAWEED_MASTER_PORT", "59333"))
    qdrant_port = int(value("PLATFORM_QDRANT_HTTP_PORT", "56333"))

    result["services"]["postgres"] = check_tcp(
        host, postgres_port, timeout=args.timeout
    )
    result["services"]["redis"] = check_redis(
        host, redis_port, timeout=args.timeout
    )
    result["services"]["seaweedfs"] = check_http(
        f"http://{host}:{seaweed_port}/cluster/healthz",
        timeout=args.timeout,
    )
    result["services"]["qdrant"] = check_http(
        f"http://{host}:{qdrant_port}/healthz",
        timeout=args.timeout,
    )

    result["ok"] = docker_ok and all(
        bool(service.get("ok")) for service in result["services"].values()
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行；实际 .env 不存在时安全回退到示例配置。"""
    parser = argparse.ArgumentParser(description="验证本地 Core 基础设施")
    parser.add_argument("--compose-file", type=Path, default=DEFAULT_COMPOSE)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV if DEFAULT_ENV.exists() else EXAMPLE_ENV,
    )
    parser.add_argument("--timeout", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """输出 JSON；全部服务健康时返回 0，否则返回 1。"""
    args = parse_args(argv)
    report = verify(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
