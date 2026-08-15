import threading
import flask
from aworld.trace.instrumentation.flask import instrument_flask
from aworld.trace.instrumentation.requests import instrument_requests
from aworld.logs.util import logger, trace_logger
import aworld.trace as trace
import os
from aworld.trace.config import ObservabilityConfig

os.environ["MONITOR_SERVICE_NAME"] = "otlp_example"
os.environ["ANT_OTEL_ENDPOINT"] = "https://antcollector.alipay.com/namespace/aworld/task/aworld/otlp/api/v1/metrics"

trace.configure(ObservabilityConfig(
    metrics_provider="otlp",
    metrics_backend="antmonitor"
))
instrument_flask()
instrument_requests()

app = flask.Flask(__name__)


@app.route('/api/test')
def test():
    return 'Hello, World!'


def invoke_api():
    import requests
    response = requests.get('http://localhost:7070/api/test')
    logger.info(f"invoke_api response={response.text}")


def main():
    logger.info("main running")
    with trace.span("test_flask") as span:
        trace_logger.info("start invoke_api")
        invoke_api()


# if __name__ == "__main__":
#     thread = threading.Thread(target=lambda: app.run(port=7070), daemon=True)
#     thread.start()
#     main()
#     thread.join()
