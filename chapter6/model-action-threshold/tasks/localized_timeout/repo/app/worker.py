"""Worker construction kept separate from configuration parsing."""

from app.config import resolve_timeout


def worker_options(timeout=None, env=None):
    return {"timeout": resolve_timeout(timeout, env), "retries": 2}
