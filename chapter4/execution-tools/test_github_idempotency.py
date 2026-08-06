"""Idempotency coverage for the Experiment 4-3 GitHub execution tool."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from external_tools import ExternalTools


class _Approval:
    def request_approval(self, _operation, _details):
        return True, "bounded test"


class _Ref:
    def __init__(self, ref: str):
        self.ref = ref


class _Pull:
    number = 605
    html_url = "https://github.com/bojieli/ai-agent-book/pull/605"
    title = "Experiment 4-3"
    state = "open"
    created_at = datetime(2026, 8, 2, tzinfo=timezone.utc)
    head = _Ref("exp/4-3-gui-environments")
    base = _Ref("main")


class _Repo:
    def get_branch(self, name):
        return _Ref(name)

    def get_pulls(self, *, state, head, base):
        assert (state, head, base) == (
            "open", "bojieli:exp/4-3-gui-environments", "main")
        return [_Pull()]

    def create_pull(self, **_kwargs):
        raise AssertionError("an existing PR must be reused, not duplicated")


class _GitHub:
    def get_repo(self, name):
        assert name == "bojieli/ai-agent-book"
        return _Repo()


def test_existing_open_pull_request_is_reused() -> None:
    tool = ExternalTools(_Approval())
    tool._github_client = _GitHub()
    result = asyncio.run(tool.github_create_pr(
        repo_name="bojieli/ai-agent-book",
        title="Experiment 4-3",
        body="bounded test",
        head_branch="exp/4-3-gui-environments",
        base_branch="main",
    ))
    assert result["success"] is True
    assert result["pr_number"] == 605
    assert result["idempotent_reuse"] is True
