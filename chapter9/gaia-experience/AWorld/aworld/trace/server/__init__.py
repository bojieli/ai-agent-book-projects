# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import threading
import os
from fastapi.staticfiles import StaticFiles
from .routes import setup_routes
from aworld.logs.util import logger
from aworld.utils.import_package import import_package

GLOBAL_TRACE_SERVER = None


class TraceServer:
    def __init__(self, storage, port: int = 7079):
        self._storage = storage
        self._port = port
        self._thread = None
        self.app = None
        self._started = False

    def start(self):
        self._thread = threading.Thread(target=self._start_app, daemon=True)
        self._thread.start()
        self._started = True

    def join(self):
        if self._thread:
            self._thread.join()
        else:
            raise Exception("Trace server not started.")

    def get_storage(self):
        return self._storage

    def is_started(self):
        return self._started

    def _start_app(self):
        import_package('uvicorn')  # noqa
        import uvicorn
        app = setup_routes(self._storage)

        webui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../cmd/web/webui")
        static_path = os.path.join(webui_path, "public")
        app.mount("/static", StaticFiles(directory=static_path), name="static")

        self.app = app
        # app.run(port=self._port)
        uvicorn.run(app, host="0.0.0.0", port=self._port, loop="asyncio")


def set_trace_server(storage, port: int = 7079, start_server=False):
    global GLOBAL_TRACE_SERVER
    if GLOBAL_TRACE_SERVER is None:
        GLOBAL_TRACE_SERVER = TraceServer(storage, port)
    if GLOBAL_TRACE_SERVER.is_started():
        setup_routes(storage)
        return
    if start_server:
        GLOBAL_TRACE_SERVER.start()


def get_trace_server():
    if GLOBAL_TRACE_SERVER is None:
        logger.warning("No trace server has been set.")
    return GLOBAL_TRACE_SERVER
