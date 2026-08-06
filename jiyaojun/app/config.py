"""纪要君基础设施配置契约；默认离线，不读取或打印真实凭据。"""

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlparse


def _valid_service_url(value: str) -> bool:
    """只接受显式 HTTP(S) 服务地址，空值表示使用离线实现。"""
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@dataclass(frozen=True)
class InfrastructureSettings:
    """本地真实基础设施与离线替身共用的配置边界。"""

    database_url: str = ""
    redis_url: str = ""
    storage_backend: str = "memory"
    redis_backend: str = "memory"
    vector_backend: str = "memory"
    object_backend: str = "mock"
    s3_endpoint: str = ""
    s3_bucket: str = "jiyaojun"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    qdrant_url: str = ""
    qdrant_collection: str = "meeting_knowledge"
    safety_gateway_url: str = ""
    safety_gateway_token: str = ""
    # 商业模型预算契约（ADR-0003）；普通调用不可放宽
    model_max_input_tokens: int = 8192
    model_max_output_tokens: int = 2048
    model_daily_call_limit: int = 100
    model_monthly_budget_cny: float = 200.0
    scheduler_backend: str = "memory"
    celery_broker_url: str = ""
    celery_pipeline: str = "orchestrator"  # orchestrator | stub

    def effective_celery_broker_url(self) -> str:
        """Celery broker/result 地址；优先独立 broker，否则复用 redis_url。"""
        return self.celery_broker_url or self.redis_url

    @classmethod
    def from_env(cls) -> "InfrastructureSettings":
        """从环境变量加载；缺失配置继续使用现有离线路径。"""
        return cls(
            database_url=os.getenv("JIYAOJUN_DATABASE_URL", "").strip(),
            redis_url=os.getenv("JIYAOJUN_REDIS_URL", "").strip(),
            storage_backend=os.getenv("JIYAOJUN_STORAGE_BACKEND", "memory").strip().lower(),
            redis_backend=os.getenv("JIYAOJUN_REDIS_BACKEND", "memory").strip().lower(),
            vector_backend=os.getenv("JIYAOJUN_VECTOR_BACKEND", "memory").strip().lower(),
            object_backend=os.getenv("JIYAOJUN_OBJECT_BACKEND", "mock").strip().lower(),
            s3_endpoint=os.getenv("JIYAOJUN_S3_ENDPOINT", "").strip(),
            s3_bucket=os.getenv("JIYAOJUN_S3_BUCKET", "jiyaojun").strip(),
            s3_access_key=os.getenv("JIYAOJUN_S3_ACCESS_KEY", "").strip(),
            s3_secret_key=os.getenv("JIYAOJUN_S3_SECRET_KEY", "").strip(),
            qdrant_url=os.getenv("JIYAOJUN_QDRANT_URL", "").strip(),
            qdrant_collection=os.getenv(
                "JIYAOJUN_QDRANT_COLLECTION", "meeting_knowledge"
            ).strip(),
            safety_gateway_url=os.getenv("JIYAOJUN_SAFETY_GATEWAY_URL", "").strip(),
            safety_gateway_token=os.getenv(
                "JIYAOJUN_SAFETY_GATEWAY_TOKEN", ""
            ).strip(),
            model_max_input_tokens=int(
                os.getenv("JIYAOJUN_MODEL_MAX_INPUT_TOKENS", "8192")
            ),
            model_max_output_tokens=int(
                os.getenv("JIYAOJUN_MODEL_MAX_OUTPUT_TOKENS", "2048")
            ),
            model_daily_call_limit=int(
                os.getenv("JIYAOJUN_MODEL_DAILY_CALL_LIMIT", "100")
            ),
            model_monthly_budget_cny=float(
                os.getenv("JIYAOJUN_MODEL_MONTHLY_BUDGET_CNY", "200")
            ),
            scheduler_backend=os.getenv(
                "JIYAOJUN_SCHEDULER_BACKEND", "memory"
            ).strip().lower(),
            celery_broker_url=os.getenv("JIYAOJUN_CELERY_BROKER_URL", "").strip(),
            celery_pipeline=os.getenv("JIYAOJUN_CELERY_PIPELINE", "orchestrator")
            .strip()
            .lower(),
        )

    def validate(self) -> list[str]:
        """返回配置错误；调用方必须在启用真实适配器前 fail-closed。"""
        errors: list[str] = []
        if self.database_url and not self.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://")
        ):
            errors.append("JIYAOJUN_DATABASE_URL must use PostgreSQL")
        if self.redis_url and not self.redis_url.startswith(("redis://", "rediss://")):
            errors.append("JIYAOJUN_REDIS_URL must use redis:// or rediss://")
        if self.storage_backend not in ("memory", "postgres"):
            errors.append("JIYAOJUN_STORAGE_BACKEND must be memory or postgres")
        if self.redis_backend not in ("memory", "redis"):
            errors.append("JIYAOJUN_REDIS_BACKEND must be memory or redis")
        if self.vector_backend not in ("memory", "qdrant"):
            errors.append("JIYAOJUN_VECTOR_BACKEND must be memory or qdrant")
        if self.object_backend not in ("mock", "s3"):
            errors.append("JIYAOJUN_OBJECT_BACKEND must be mock or s3")
        if self.vector_backend == "qdrant" and not self.qdrant_url:
            errors.append("JIYAOJUN_QDRANT_URL required when vector_backend=qdrant")
        if self.object_backend == "s3" and not self.s3_endpoint:
            errors.append("JIYAOJUN_S3_ENDPOINT required when object_backend=s3")
        if self.object_backend == "s3" and not self.s3_bucket:
            errors.append("JIYAOJUN_S3_BUCKET required when object_backend=s3")
        if self.storage_backend == "postgres" and not self.database_url:
            errors.append("JIYAOJUN_DATABASE_URL required when storage_backend=postgres")
        if self.redis_backend == "redis" and not self.redis_url:
            errors.append("JIYAOJUN_REDIS_URL required when redis_backend=redis")
        if self.scheduler_backend not in ("memory", "celery"):
            errors.append("JIYAOJUN_SCHEDULER_BACKEND must be memory or celery")
        if self.celery_pipeline not in ("orchestrator", "stub"):
            errors.append("JIYAOJUN_CELERY_PIPELINE must be orchestrator or stub")
        if self.model_max_input_tokens <= 0 or self.model_max_output_tokens <= 0:
            errors.append("model token limits must be positive")
        if self.model_daily_call_limit <= 0:
            errors.append("JIYAOJUN_MODEL_DAILY_CALL_LIMIT must be positive")
        if self.model_monthly_budget_cny <= 0:
            errors.append("JIYAOJUN_MODEL_MONTHLY_BUDGET_CNY must be positive")
        if self.scheduler_backend == "celery" and not self.effective_celery_broker_url():
            errors.append(
                "JIYAOJUN_CELERY_BROKER_URL or JIYAOJUN_REDIS_URL required "
                "when scheduler_backend=celery"
            )
        broker = self.effective_celery_broker_url()
        if broker and not broker.startswith(("redis://", "rediss://")):
            errors.append(
                "JIYAOJUN_CELERY_BROKER_URL must use redis:// or rediss://"
            )
        for name, value in (
            ("JIYAOJUN_S3_ENDPOINT", self.s3_endpoint),
            ("JIYAOJUN_QDRANT_URL", self.qdrant_url),
            ("JIYAOJUN_SAFETY_GATEWAY_URL", self.safety_gateway_url),
        ):
            if not _valid_service_url(value):
                errors.append(f"{name} must be an absolute HTTP(S) URL")
        if self.s3_endpoint and not self.s3_bucket:
            errors.append("JIYAOJUN_S3_BUCKET is required when S3 is enabled")
        if self.qdrant_url and not self.qdrant_collection:
            errors.append(
                "JIYAOJUN_QDRANT_COLLECTION is required when Qdrant is enabled"
            )
        return errors

    def public_summary(self) -> dict[str, object]:
        """仅暴露非敏感状态，禁止把 access key/token 写入日志。"""
        return {
            "database_enabled": bool(self.database_url),
            "redis_enabled": bool(self.redis_url),
            "storage_backend": self.storage_backend,
            "redis_backend": self.redis_backend,
            "vector_backend": self.vector_backend,
            "object_backend": self.object_backend,
            "s3_endpoint": self.s3_endpoint,
            "s3_bucket": self.s3_bucket,
            "qdrant_url": self.qdrant_url,
            "qdrant_collection": self.qdrant_collection,
            "safety_gateway_url": self.safety_gateway_url,
            "safety_gateway_enabled": bool(self.safety_gateway_url),
            "model_max_input_tokens": self.model_max_input_tokens,
            "model_max_output_tokens": self.model_max_output_tokens,
            "model_daily_call_limit": self.model_daily_call_limit,
            "model_monthly_budget_cny": self.model_monthly_budget_cny,
            "scheduler_backend": self.scheduler_backend,
            "celery_pipeline": self.celery_pipeline,
            "celery_broker_configured": bool(self.effective_celery_broker_url()),
            "credentials_configured": bool(
                self.s3_access_key
                or self.s3_secret_key
                or self.safety_gateway_token
            ),
        }


settings = InfrastructureSettings.from_env()
