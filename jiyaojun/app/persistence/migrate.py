"""CLI：应用 PostgreSQL 迁移。"""

from __future__ import annotations

import sys

from app.config import InfrastructureSettings
from app.persistence.postgres import apply_migrations, connect


def main() -> int:
    settings = InfrastructureSettings.from_env()
    errors = settings.validate()
    if errors:
        for e in errors:
            print(f"配置错误: {e}", file=sys.stderr)
        return 1
    if not settings.database_url:
        print("JIYAOJUN_DATABASE_URL 未设置", file=sys.stderr)
        return 1

    conn = connect(settings.database_url)
    try:
        newly = apply_migrations(conn)
        conn.commit()
        if newly:
            print(f"已应用迁移: {', '.join(newly)}")
        else:
            print("无新迁移（已全部应用）")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
