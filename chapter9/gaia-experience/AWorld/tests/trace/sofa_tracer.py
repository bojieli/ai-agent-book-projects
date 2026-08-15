import os  # noqa: E402

os.environ["MONITOR_SERVICE_NAME"] = "otlp_example"  # noqa
os.environ["ANT_OTEL_ENDPOINT"] = "https://antcollector.alipay.com/namespace/aworld/task/aworld/otlp/api/v1/metrics"  # noqa
os.environ["OTLP_TRACES_ENDPOINT"] = "https://antcollector.alipay.com/namespace/aworld/task/aworld_trace/otlp/api/v1/traces"  # noqa

from aworld.trace.config import ObservabilityConfig
from aworld.logs.util import logger
from aworld.trace.baggage import BaggageContext
from aworld.trace.base import get_tracer_provider
from aworld.trace.instrumentation.requests import instrument_requests
from aworld.trace.instrumentation.flask import instrument_flask
import flask
import threading
import aworld.trace as trace


trace.configure(ObservabilityConfig(
    trace_provider="otlp",
    trace_backends=["other_otlp"],
    trace_base_url="https://antcollector.alipay.com/namespace/aworld/task/aworld_trace/otlp/api/v1/traces",
    metrics_provider="otlp",
    metrics_backend="antmonitor",
    metrics_base_url="https://antcollector.alipay.com/namespace/aworld/task/aworld/otlp/api/v1/metrics"
))
instrument_flask()
instrument_requests()

app = flask.Flask(__name__)


@app.route('/api/test')
def test():
    sofa_trace_id = BaggageContext.get_baggage_value("attributes.sofa.traceid")
    sofa_rpc_id = BaggageContext.get_baggage_value("attributes.sofa.rpcid")
    sofa_pen_attrs = BaggageContext.get_baggage_value(
        "attributes.sofa.penattrs")
    sofa_sys_pen_attrs = BaggageContext.get_baggage_value(
        "attributes.sofa.syspenattrs")
    logger.info(
        f"test sofa_trace_id={sofa_trace_id}, sofa_rpc_id={sofa_rpc_id}, sofa_pen_attrs={sofa_pen_attrs}, sofa_sys_pen_attrs={sofa_sys_pen_attrs}"
    )
    return 'Hello, World!'


def invoke_api():
    import requests
    session = requests.session()
    session.headers.update({
        "SOFA-TraceId": "12345678901234567890123456789012",
        "SOFA-RpcId": "0.1.1",
        "sofaPenAttrs": "key1=value1&key2=value2",
        "sysPenAttrs": "key1=value1&key2=value2"
    })
    response = session.get('http://localhost:7070/api/test')
    logger.info(f"invoke_api response={response.text}")


def main():
    logger.info("main running")
    invoke_api()


# if __name__ == "__main__":
#     thread = threading.Thread(target=lambda: app.run(port=7070), daemon=True)
#     thread.start()
#     main()
#     get_tracer_provider().force_flush(1000)
#     thread.join()
