import os
from pydantic import BaseModel, ConfigDict
from typing import Sequence, Optional
from aworld.trace.span_cosumer import SpanConsumer
from logging import Logger
from aworld.logs.util import trace_logger
from aworld.trace.context_manager import trace_configure
from aworld.metrics.context_manager import MetricContext
from aworld.logs.log import set_log_provider, instrument_logging
from aworld.trace.instrumentation.uni_llmmodel import LLMModelInstrumentor
from aworld.trace.instrumentation.eventbus import EventBusInstrumentor
from aworld.trace.instrumentation.agent import AgentInstrumentor
from aworld.trace.instrumentation.tool import ToolInstrumentor

from aworld.trace.opentelemetry.memory_storage import TraceStorage


class ObservabilityConfig(BaseModel):
    '''
    Observability configuration
    '''
    model_config = ConfigDict(arbitrary_types_allowed=True)

    trace_provider: Optional[str] = "otlp"
    trace_backends: Optional[Sequence[str]] = ["memory"]
    trace_base_url: Optional[str] = None
    trace_write_token: Optional[str] = None
    trace_span_consumers: Optional[Sequence[SpanConsumer]] = None
    trace_storage: Optional[TraceStorage] = None
    # whether to start the trace service
    trace_server_enabled: Optional[bool] = False
    trace_server_port: Optional[int] = 7079
    metrics_provider: Optional[str] = None
    metrics_backend: Optional[str] = None
    metrics_base_url: Optional[str] = None
    metrics_write_token: Optional[str] = None
    # whether to instrument system metrics
    metrics_system_enabled: Optional[bool] = False
    logs_provider: Optional[str] = None
    logs_backend: Optional[str] = None
    logs_base_url: Optional[str] = None
    logs_write_token: Optional[str] = None
    # The loggers that need to record the log as a span
    logs_trace_instrumented_loggers: Sequence[Logger] = [trace_logger]


def configure(config: ObservabilityConfig = None):
    if config is None:
        config = ObservabilityConfig()
    _trace_configure(config)
    _metrics_configure(config)
    _log_configure(config)
    LLMModelInstrumentor().instrument()
    EventBusInstrumentor().instrument()
    AgentInstrumentor().instrument()
    ToolInstrumentor().instrument()


def _trace_configure(config: ObservabilityConfig):
    if not config.trace_base_url and config.trace_provider == "otlp":
        if "logfire" in config.trace_backends:
            config.trace_base_url = os.getenv("LOGFIRE_WRITE_TOKEN")
        elif os.getenv("OTLP_TRACES_ENDPOINT"):
            config.trace_base_url = os.getenv("OTLP_TRACES_ENDPOINT")
            config.trace_backends.append("other_otlp")

    trace_configure(
        provider=config.trace_provider,
        backends=config.trace_backends,
        base_url=config.trace_base_url,
        write_token=config.trace_write_token,
        span_consumers=config.trace_span_consumers,
        server_enabled=config.trace_server_enabled,
        server_port=config.trace_server_port,
        storage=config.trace_storage
    )


def _metrics_configure(config: ObservabilityConfig):
    if config.metrics_provider and config.metrics_backend:
        MetricContext.configure(
            provider=config.metrics_provider,
            backend=config.metrics_backend,
            base_url=config.metrics_base_url,
            write_token=config.metrics_write_token,
            metrics_system_enabled=config.metrics_system_enabled
        )


def _log_configure(config: ObservabilityConfig):
    if config.logs_provider and config.logs_backend:
        if config.logs_backend == "logfire" and not config.logs_write_token:
            config.logs_write_token = os.getenv("LOGFIRE_WRITE_TOKEN")
        set_log_provider(provider=config.logs_provider,
                         backend=config.logs_backend,
                         base_url=config.logs_base_url,
                         write_token=config.logs_write_token)

    if config.logs_trace_instrumented_loggers:
        for logger in config.logs_trace_instrumented_loggers:
            instrument_logging(logger)
