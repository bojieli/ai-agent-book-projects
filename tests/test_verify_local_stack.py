"""本地 Core 健康检查脚本的离线单元测试。"""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.verify_local_stack import load_env_file, verify


class VerifyLocalStackTest(unittest.TestCase):
    """不依赖 Docker daemon 验证配置解析和总体判定。"""

    def test_load_env_file_ignores_comments_and_quotes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "# comment\nPORT=1234\nTOKEN='not-a-real-secret'\n",
                encoding="utf-8",
            )
            values = load_env_file(path)

        self.assertEqual(values["PORT"], "1234")
        self.assertEqual(values["TOKEN"], "not-a-real-secret")

    @patch("scripts.verify_local_stack.check_http", return_value={"ok": True})
    @patch("scripts.verify_local_stack.check_redis", return_value={"ok": True})
    @patch("scripts.verify_local_stack.check_tcp", return_value={"ok": True})
    @patch(
        "scripts.verify_local_stack.run_command",
        side_effect=[(True, "29.5.3"), (True, "[]")],
    )
    def test_verify_requires_docker_and_all_services(
        self,
        _run_command,
        _check_tcp,
        _check_redis,
        _check_http,
    ) -> None:
        args = argparse.Namespace(
            compose_file=Path("deploy/local/docker-compose.yml"),
            env_file=Path("deploy/local/.env.example"),
            timeout=0.1,
        )

        report = verify(args)

        self.assertTrue(report["ok"])
        self.assertTrue(report["docker"]["ok"])
        self.assertEqual(set(report["services"]), {
            "postgres",
            "redis",
            "seaweedfs",
            "qdrant",
        })


if __name__ == "__main__":
    unittest.main()
