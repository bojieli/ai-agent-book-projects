import json
import logging
from fastapi import APIRouter
from aworld.trace.server import get_trace_server
from aworld.trace.server.util import build_trace_tree, get_agent_flow
from aworld.cmd.utils.trace_summarize import get_summarize_trace

logger = logging.getLogger(__name__)

router = APIRouter()

prefix = "/api/trace"


@router.get("/list")
async def list_traces():
    storage = get_trace_server().get_storage()
    trace_data = []
    for trace_id in storage.get_all_traces():
        spans = storage.get_all_spans(trace_id)
        spans_sorted = sorted(spans, key=lambda x: x.start_time)
        trace_tree = build_trace_tree(spans_sorted)
        trace_data.append({
            'trace_id': trace_id,
            'root_span': trace_tree,
        })
    return {
        "data": trace_data
    }


@router.get("/agent")
async def get_agent_trace(trace_id: str):
    data = get_agent_flow(trace_id)
    await _add_trace_summary(trace_id, data.get('nodes'))
    return data


async def _add_trace_summary(trace_id, spans):
    summary = await get_summarize_trace(trace_id)
    json_summary_dict = {}
    if summary:
        json_summary = json.loads(summary)
        json_summary_dict = {item['agent']: json.dumps(
            item) for item in json_summary}

    for span in spans:
        if summary and "event_id" in span:
            span['summary'] = json_summary_dict.get(span['event_id'])
        span['attributes'] = None
