# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import typing
from os import linesep
from aworld.trace.base import Span
from aworld.trace.span_cosumer import SpanConsumer, get_span_consumers
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult, SpanExporter
from aworld.logs.util import logger


class FileSpanExporter(SpanExporter):
    """Implementation of :class:`SpanExporter` that prints spans to the
    console.

    This class can be used for diagnostic purposes. It prints the exported
    spans to the console STDOUT.
    """

    def __init__(
        self,
        file_path: str = None,
        formatter: typing.Callable[
            [ReadableSpan], str
        ] = lambda span: span.to_json() + linesep,
    ):
        self.formatter = formatter
        self.file_path = file_path

    def export(self, spans: typing.Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            with open(self.file_path, 'a') as f:
                for span in spans:
                    f.write(self.formatter(span))

            return SpanExportResult.SUCCESS
        except Exception as e:
            logger.error(e)
            return SpanExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


class ReadOnlySpan(Span, ReadableSpan):
    """Implementation of :class:`Span` that wraps a :class:`ReadableSpan`.
    This class can be used to wrap a :class:`ReadableSpan` to make it
    read-only.
    Args:
        span: The span to wrap.
    """

    def __init__(self, span: ReadableSpan):
        self._span = span

    if not typing.TYPE_CHECKING:
        def __getattr__(self, name: str) -> typing.Any:
            return getattr(self._span, name)

    def end(self, end_time: typing.Optional[int] = None) -> None:
        pass

    def set_attribute(self, key: str, value: typing.Any) -> None:
        pass

    def set_attributes(self, attributes: dict[str, typing.Any]) -> None:
        pass

    def is_recording(self) -> bool:
        return False

    def record_exception(
            self,
            exception: BaseException,
            attributes: dict[str, typing.Any] = None,
            timestamp: typing.Optional[int] = None,
            escaped: bool = False,
    ) -> None:
        pass

    def get_trace_id(self) -> str:
        return f"{self._span.get_span_context().trace_id:032x}"

    def get_span_id(self) -> str:
        return f"{self._span.get_span_context().span_id:016x}"


class SpanConsumerExporter(SpanExporter):
    """Implementation of :class:`SpanExporter` that exports spans to
    multiple span consumers.
    This class can be used for exporting spans to multiple span consumers.
    It exports the spans to the span consumers in the order they are passed
    in the constructor.
    Args:
        span_consumers: A sequence of span consumers to export spans to. 
    """

    def __init__(
        self,
        span_consumers: typing.Sequence[SpanConsumer] = None,
    ):
        self._span_consumers = span_consumers or []
        self._loaded = False

    def _load_span_consumers(self):
        if not self._loaded:
            self._span_consumers.extend(get_span_consumers())
            self._loaded = True

    def export(
        self, spans: typing.Sequence[ReadableSpan]
    ) -> SpanExportResult:
        self._load_span_consumers()
        span_batches = []
        for span in spans:
            span_batches.append(ReadOnlySpan(span))
        for span_consumer in self._span_consumers:
            try:
                span_consumer.consume(span_batches)
            except Exception as e:
                logger.error(
                    f"Error consume spans: {e}, span_consumer: {span_consumer.__class__.__name__}")
        return SpanExportResult.SUCCESS


class NoOpSpanExporter(SpanExporter):
    """Implementation of :class:`SpanExporter` that does not export spans."""

    def export(
        self, spans: typing.Sequence[ReadableSpan]
    ) -> SpanExportResult:
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
