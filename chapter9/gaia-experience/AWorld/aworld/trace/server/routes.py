from aworld.trace.opentelemetry.memory_storage import TraceStorage
from aworld.utils.import_package import import_package
from aworld.trace.server.util import build_trace_tree

import_package('fastapi')  # noqa
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

app = FastAPI()
current_storage = None
routes_setup = False


def setup_routes(storage: TraceStorage):
    global current_storage
    current_storage = storage

    global routes_setup

    if routes_setup:
        return app

    @app.get("/")
    async def root():
        return RedirectResponse("/static/trace_ui.html")

    @app.get('/api/trace/list')
    async def traces():
        trace_data = []
        for trace_id in current_storage.get_all_traces():
            spans = current_storage.get_all_spans(trace_id)
            spans_sorted = sorted(spans, key=lambda x: x.start_time)
            trace_tree = build_trace_tree(spans_sorted)
            trace_data.append({
                'trace_id': trace_id,
                'root_span': trace_tree,
            })
            response = {
                "data": trace_data
            }
        return JSONResponse(content=response)

    @app.get('/api/traces/{trace_id}')
    async def get_trace(trace_id):
        spans = current_storage.get_all_spans(trace_id)
        spans_sorted = sorted(spans, key=lambda x: x.start_time)
        trace_tree = build_trace_tree(spans_sorted)
        return JSONResponse(content={
            'trace_id': trace_id,
            'root_span': trace_tree,
        })

    routes_setup = True
    return app
