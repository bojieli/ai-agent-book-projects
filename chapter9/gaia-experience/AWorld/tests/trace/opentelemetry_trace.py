import os  # noqa
# os.environ["START_TRACE_SERVER"] = "false"  # noqa
os.environ["MONITOR_SERVICE_NAME"] = "otlp_example"  # noqa
# os.environ["OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
# os.environ["METRICS_SYSTEM_ENABLED"] = "true"
# os.environ["LOGFIRE_WRITE_TOKEN"] = (
#     "Your logfire write token, "
#     "create guide refer to "
#     "https://logfire.pydantic.dev/docs/how-to-guides/create-write-tokens/"
# )

import aworld.trace as trace  # noqa
from aworld.logs.util import logger, trace_logger
from aworld.trace.server import get_trace_server
from aworld.output.artifact import Artifact, ArtifactType


trace.configure(trace.ObservabilityConfig(trace_server_enabled=True))


class TestClass:
    @trace.func_span(span_name="test_func_args")
    def test_func(self, artifact: Artifact = None):
        logger.info(f"this is a test func, artifact={artifact}")


@trace.func_span(span_name="test_func", attributes={"test_attr": "test_value"}, extract_args=["param1"], add_attr="add_attr_value")
def traced_func(param1: str = None, param2: int = None):
    trace_logger.info("this is a traced func")
    traced_func2(param1="func2_param1_value", param2=222)
    traced_func3(param1="func3_param1_value", param2=333)


@trace.func_span(span_name="test_func_2", add_attr="add_attr_value")
def traced_func2(param1: str = None, param2: int = None):
    name = 'func2'
    trace_logger.info(f"this is a traced {name}")
    raise Exception("this is a traced func2 exception")


@trace.func_span
def traced_func3(param1: str = None, param2: int = None):
    trace_logger.info("this is a traced func3")


def main():

    logger.info("this is a no trace log")

    trace.auto_tracing("examples.trace.*", 0.01)

    with trace.span("hello") as span:
        span.set_attribute("parent_test_attr", "pppppp")
        logger.info("hello aworld")
        trace_logger.info("trace hello aworld")
        with trace.span("child hello") as span2:
            span2.set_attribute("child_test_attr", "cccccc")
            logger.info("child hello aworld")
            current_span = trace.get_current_span()
            logger.info("trace_id=%s", current_span.get_trace_id())
    try:
        test_class = TestClass()
        test_class.test_func(artifact=Artifact(
            artifact_id="123",
            artifact_type=ArtifactType.IMAGE,
            content="123",
        ))
        traced_func(param1="func1_param1_value", param2=111)
    except Exception as e:
        logger.error(f"exception: {e}")
    # from examples.trace.autotrace_demo import TestClassB
    # b = TestClassB()
    # b.classb_function_1()
    # b.classb_function_2()
    # b.classb_function_1()
    # b.classb_function_2()
    if get_trace_server():
        get_trace_server().join()
