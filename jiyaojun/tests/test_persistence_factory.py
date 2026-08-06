"""配置 backend 校验与工厂分支单测。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config import InfrastructureSettings
from app.memory.repository import InMemoryJournalRepository
from app.runtime.factory import (
    build_journal_repository,
    build_meeting_store,
    build_session_cache,
    reset_postgres_connection_cache,
)
from app.store.meetings import MeetingStore


def test_storage_backend_postgres_requires_database_url():
    settings = InfrastructureSettings(storage_backend="postgres", database_url="")
    errors = settings.validate()
    assert any("JIYAOJUN_DATABASE_URL required" in e for e in errors)


def test_redis_backend_redis_requires_redis_url():
    settings = InfrastructureSettings(redis_backend="redis", redis_url="")
    errors = settings.validate()
    assert any("JIYAOJUN_REDIS_URL required" in e for e in errors)


def test_invalid_storage_backend_rejected():
    settings = InfrastructureSettings(storage_backend="sqlite")
    errors = settings.validate()
    assert any("JIYAOJUN_STORAGE_BACKEND" in e for e in errors)


def test_invalid_redis_backend_rejected():
    settings = InfrastructureSettings(redis_backend="memcached")
    errors = settings.validate()
    assert any("JIYAOJUN_REDIS_BACKEND" in e for e in errors)


def test_default_backends_are_memory():
    settings = InfrastructureSettings()
    assert settings.storage_backend == "memory"
    assert settings.redis_backend == "memory"
    assert settings.validate() == []


def test_factory_memory_journal_repository():
    settings = InfrastructureSettings()
    repo = build_journal_repository(settings)
    assert isinstance(repo, InMemoryJournalRepository)


def test_factory_memory_meeting_store():
    settings = InfrastructureSettings()
    store = build_meeting_store(settings)
    assert isinstance(store, MeetingStore)


def test_factory_memory_session_cache():
    settings = InfrastructureSettings()
    cache = build_session_cache(settings)
    assert cache.get("sess_test") is None


def test_scheduler_backend_celery_requires_broker():
    settings = InfrastructureSettings(scheduler_backend="celery", redis_url="", celery_broker_url="")
    errors = settings.validate()
    assert any("scheduler_backend=celery" in e for e in errors)


def test_invalid_scheduler_backend_rejected():
    settings = InfrastructureSettings(scheduler_backend="rq")
    errors = settings.validate()
    assert any("JIYAOJUN_SCHEDULER_BACKEND" in e for e in errors)


def test_factory_default_scheduler_is_in_process():
    from app.runtime.factory import build_scheduler
    from app.scheduler.tasks import InProcessScheduler

    settings = InfrastructureSettings()
    sched = build_scheduler(settings)
    assert isinstance(sched, InProcessScheduler)


def test_factory_celery_scheduler_type():
    from unittest.mock import MagicMock, patch

    from app.runtime.factory import build_scheduler
    from app.scheduler.celery_scheduler import CeleryScheduler

    settings = InfrastructureSettings(
        scheduler_backend="celery",
        celery_broker_url="redis://127.0.0.1:56379/2",
    )
    with patch("app.runtime.factory.RedisCache") as mock_redis:
        mock_redis.return_value = MagicMock()
        sched = build_scheduler(settings)
    assert isinstance(sched, CeleryScheduler)


@patch("app.runtime.factory.connect")
@patch("app.runtime.factory.apply_migrations")
def test_factory_postgres_journal_repository(mock_migrate, mock_connect):
    reset_postgres_connection_cache()
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_connect.return_value = mock_conn
    settings = InfrastructureSettings(
        storage_backend="postgres",
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
    )
    repo = build_journal_repository(settings)
    mock_migrate.assert_called_once()
    mock_conn.commit.assert_called_once()
    from app.memory.postgres_repository import PostgresJournalRepository

    assert isinstance(repo, PostgresJournalRepository)
    reset_postgres_connection_cache()


@patch("app.runtime.factory.connect")
@patch("app.runtime.factory.apply_migrations")
def test_factory_postgres_meeting_store(mock_migrate, mock_connect):
    reset_postgres_connection_cache()
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_connect.return_value = mock_conn
    settings = InfrastructureSettings(
        storage_backend="postgres",
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
    )
    store = build_meeting_store(settings)
    mock_migrate.assert_called_once()
    from app.store.postgres_meetings import PostgresMeetingStore

    assert isinstance(store, PostgresMeetingStore)
    reset_postgres_connection_cache()
