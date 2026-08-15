import os
import json
from aworld.logs.util import logger, trace_logger
from typing import Sequence
import aworld.trace as trace
from aworld.trace.base import Span
from aworld.trace.span_cosumer import register_span_consumer, SpanConsumer
from aworld.logs.util import logger, trace_logger

os.environ["MONITOR_SERVICE_NAME"] = "otlp_example"


@register_span_consumer({"test_param": "MockSpanConsumer111"})
class MockSpanConsumer(SpanConsumer):

    def __init__(self, test_param=None):
        self._test_param = test_param

    def consume(self, spans: Sequence[Span]) -> None:
        for span in spans:
            logger.info(
                f"_test_param={self._test_param}, trace_id={span.get_trace_id()}, span_id={span.get_span_id()}, attributes={span.attributes}")


def main():
    with trace.span("hello") as span:
        span.set_attribute("parent_test_attr", "pppppp")
        logger.info("hello aworld")
        trace_logger.info("trace hello aworld")
