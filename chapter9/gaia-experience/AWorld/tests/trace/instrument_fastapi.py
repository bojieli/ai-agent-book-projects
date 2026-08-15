import os
import time
import threading
from aworld.trace.config import ObservabilityConfig
from aworld.trace.instrumentation.fastapi import instrument_fastapi
from aworld.trace.instrumentation.requests import instrument_requests
from aworld.logs.util import logger, trace_logger
import aworld.trace as trace
from aworld.utils.import_package import import_packages
import_packages(['fastapi', 'uvicorn'])  # noqa
import fastapi  # noqa
import uvicorn  # noqa

os.environ["MONITOR_SERVICE_NAME"] = "otlp_example"
os.environ["ANT_OTEL_ENDPOINT"] = "https://antcollector.alipay.com/namespace/aworld/task/aworld/otlp/api/v1/metrics"

trace.configure(ObservabilityConfig(
    metrics_provider="otlp",
    metrics_backend="antmonitor"
))

instrument_fastapi()
instrument_requests()

app = fastapi.FastAPI()


@app.get("/api/hello")
async def hello():
    return {"message": "Hello World"}


def invoke_api():
    import requests
    response = requests.get('http://127.0.0.1:7071/api/hello')
    logger.info(f"invoke_api response={response.text}")


def main():
    logger.info("main running")
    with trace.span("test_fastapi") as span:
        trace_logger.info("start invoke_api")
        invoke_api()


# if __name__ == "__main__":
#     server_thread = threading.Thread(
#         target=lambda: uvicorn.run(app, host="0.0.0.0", port=7071),
#         daemon=True
#     )
#     server_thread.start()
#     time.sleep(1)
#     main()
#     server_thread.join()
