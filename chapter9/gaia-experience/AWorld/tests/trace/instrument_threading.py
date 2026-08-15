import threading
import aworld.trace as trace
import os
import time
from aworld.trace.instrumentation.threading import instrument_theading
from aworld.logs.util import logger, trace_logger

os.environ["MONITOR_SERVICE_NAME"] = "otlp_example"
trace.configure()
instrument_theading()


def child_thread_func():
    logger.info("child thread running")
    with trace.span("child_thread") as span:
        trace_logger.info("child thread running")
    time.sleep(1000)


def main():
    logger.info("main running")
    with trace.span("test_fastapi") as span:
        trace_logger.info("start run child_thread_func")
        threading.Thread(target=child_thread_func).start()
        threading.Thread(target=child_thread_func).start()
