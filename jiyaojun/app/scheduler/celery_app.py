"""Celery 应用 — broker/result backend 指向 Redis（默认 DB2）。"""

from __future__ import annotations

from celery import Celery

from app.config import InfrastructureSettings, settings as default_settings

# 单例 Celery 实例，供 worker 与任务装饰器共享
celery_app = Celery("jiyaojun")


def configure_celery_app(
    cfg: InfrastructureSettings | None = None,
    *,
    task_always_eager: bool | None = None,
) -> Celery:
    """按基础设施配置更新 Celery 实例。"""
    cfg = cfg or default_settings
    broker = cfg.effective_celery_broker_url()
    celery_app.conf.update(
        broker_url=broker,
        result_backend=broker,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_default_queue="jiyaojun_pipeline",
        imports=("app.scheduler.celery_tasks",),
    )
    if task_always_eager is not None:
        celery_app.conf.task_always_eager = task_always_eager
        celery_app.conf.task_store_eager_result = task_always_eager
    return celery_app


# 模块加载时按环境变量初始化
configure_celery_app()

# 确保任务模块被导入并完成 @celery_app.task 注册
import app.scheduler.celery_tasks  # noqa: E402,F401
