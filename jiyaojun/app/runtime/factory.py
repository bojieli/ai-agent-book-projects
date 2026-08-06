"""运行时工厂 — 按配置构建 journal / meeting store / 会话缓存。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.cache.redis_client import (
    IdempotencyCache,
    InMemoryJsonCache,
    RedisCache,
    SessionProjectionCache,
)
from app.config import InfrastructureSettings
from app.knowledge.embedding import EmbeddingProvider, get_embedding_provider
from app.knowledge.rag import HybridRagIndex
from app.knowledge.vector_store import QdrantHybridIndex, VectorIndex
from app.memory.repository import InMemoryJournalRepository
from app.storage.object_store import MockObjectStore, ObjectStore, S3ObjectStore
from app.memory.session_journal import JournalRepository
from app.persistence.postgres import apply_migrations, connect
from app.store.meetings import MeetingStore

# postgres 模式下复用同一连接，避免重复迁移与连接泄漏。
_shared_pg_conn: Any = None


def reset_postgres_connection_cache() -> None:
    """测试或进程热切换时清空共享连接缓存。"""
    global _shared_pg_conn
    if _shared_pg_conn is not None:
        try:
            if not getattr(_shared_pg_conn, "closed", True):
                _shared_pg_conn.close()
        except Exception:
            pass
    _shared_pg_conn = None


def _postgres_conn(settings: InfrastructureSettings):
    """获取并缓存已迁移的 PostgreSQL 连接。"""
    global _shared_pg_conn
    errors = settings.validate()
    if errors:
        raise ValueError("; ".join(errors))
    closed = True
    if _shared_pg_conn is not None:
        closed = bool(getattr(_shared_pg_conn, "closed", True))
    if _shared_pg_conn is None or closed:
        conn = connect(settings.database_url)
        apply_migrations(conn)
        conn.commit()
        _shared_pg_conn = conn
    return _shared_pg_conn


def build_journal_repository(settings: InfrastructureSettings) -> JournalRepository:
    """构建 Session Journal 仓库；postgres 时自动应用迁移。"""
    if settings.storage_backend == "memory":
        return InMemoryJournalRepository()

    from app.memory.postgres_repository import PostgresJournalRepository

    return PostgresJournalRepository(_postgres_conn(settings))


def build_meeting_store(
    settings: InfrastructureSettings,
    persist_path: Path | None = None,
) -> MeetingStore | Any:
    """构建 MeetingStore；postgres 时自动应用迁移。"""
    if settings.storage_backend == "memory":
        return MeetingStore(persist_path=persist_path)

    from app.store.postgres_meetings import PostgresMeetingStore

    return PostgresMeetingStore(_postgres_conn(settings))


def build_task_projection_store(settings: InfrastructureSettings) -> Any | None:
    """postgres 时返回任务投影仓库；memory 返回 None。"""
    if settings.storage_backend != "postgres":
        return None
    from app.persistence.task_projection import PostgresTaskProjectionStore

    return PostgresTaskProjectionStore(_postgres_conn(settings))


def wrap_task_journal_hook(settings: InfrastructureSettings, inner: Any) -> Any:
    """postgres 模式下在 journal 回调外同步写任务投影。"""
    store = build_task_projection_store(settings)
    if store is None:
        return inner
    from app.persistence.task_projection import TaskProjectionJournalHook

    return TaskProjectionJournalHook(inner, store)


def build_session_cache(settings: InfrastructureSettings) -> SessionProjectionCache:
    """构建会话投影缓存；redis 或 memory 后端。"""
    if settings.redis_backend == "redis":
        backend = RedisCache(settings.redis_url)
    else:
        backend = InMemoryJsonCache()
    return SessionProjectionCache(backend)


def _scheduler_redis_url(settings: InfrastructureSettings) -> str:
    """调度器状态/幂等优先用 redis_url，否则 Celery broker。"""
    return settings.redis_url or settings.effective_celery_broker_url()


def build_idempotency_cache(settings: InfrastructureSettings) -> IdempotencyCache:
    """构建幂等键缓存；celery 模式可回退到 broker Redis。"""
    url = _scheduler_redis_url(settings)
    if url and settings.scheduler_backend == "celery":
        return IdempotencyCache(RedisCache(url))
    if settings.redis_backend == "redis" and settings.redis_url:
        return IdempotencyCache(RedisCache(settings.redis_url))
    return IdempotencyCache(InMemoryJsonCache())


def build_task_state_store(settings: InfrastructureSettings) -> Any:
    """Celery 任务状态 Redis/内存存储。"""
    from app.scheduler.task_state import CeleryTaskStateStore

    url = _scheduler_redis_url(settings)
    if url and settings.scheduler_backend == "celery":
        return CeleryTaskStateStore(RedisCache(url))
    return CeleryTaskStateStore(InMemoryJsonCache())


def build_scheduler(settings: InfrastructureSettings) -> Any:
    """构建调度器；默认 InProcessScheduler，celery 时切换 CeleryScheduler。"""
    if settings.scheduler_backend == "celery":
        errors = settings.validate()
        if errors:
            raise ValueError("; ".join(errors))
        from app.scheduler.celery_scheduler import CeleryScheduler

        return CeleryScheduler(settings)
    from app.scheduler.tasks import InProcessScheduler

    return InProcessScheduler()


def build_vector_index(
    settings: InfrastructureSettings,
    embedder: EmbeddingProvider | None = None,
) -> VectorIndex:
    """构建向量索引；memory（默认）或 Qdrant。"""
    errors = settings.validate()
    if errors:
        raise ValueError("; ".join(errors))
    provider = embedder or get_embedding_provider()
    if settings.vector_backend == "qdrant":
        return QdrantHybridIndex(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
            embedder=provider,
        )
    return HybridRagIndex(provider)


def build_object_store(settings: InfrastructureSettings) -> ObjectStore:
    """构建对象存储；mock（默认）或 S3-compatible。"""
    errors = settings.validate()
    if errors:
        raise ValueError("; ".join(errors))
    if settings.object_backend == "s3":
        return S3ObjectStore(
            endpoint=settings.s3_endpoint,
            bucket=settings.s3_bucket,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
        )
    return MockObjectStore(bucket="mock")


def build_safety_gateway(settings: InfrastructureSettings | None = None) -> Any:
    """构建安全控制面客户端；默认离线确定性网关。"""
    from app.safety.factory import build_safety_gateway as _build

    return _build(settings)
