import uuid
from aworld.logs.util import logger
from aworld.trace.opentelemetry.memory_storage import SpanModel
from aworld.trace.constants import RunType, SPAN_NAME_PREFIX_EVENT_AGENT
from aworld.trace.instrumentation import semconv


def build_trace_tree(spans: list[SpanModel]):
    spans_dict = {span.span_id: span.dict() for span in spans}
    for span in list(spans_dict.values()):
        parent_id = span['parent_id'] if span['parent_id'] else None
        if parent_id:
            parent_span = spans_dict.get(parent_id)
            if not parent_span:
                logger.warning(f"span[{parent_id}] not be exported")
                parent_span = {
                    'span_id': parent_id,
                    'trace_id': span['trace_id'],
                    'name': 'Pengding-Span',
                    'start_time': span['start_time'],
                    'end_time': span['end_time'],
                    'duration_ms': span['duration_ms'],
                    'attributes': {},
                    'status': {},
                    'parent_id': None,
                    'run_type': 'OTHER'
                }
                spans_dict[parent_id] = parent_span
            if 'children' not in parent_span:
                parent_span['children'] = []
            parent_span['children'].append(span)

    root_spans = [span for span in spans_dict.values()
                  if span['parent_id'] is None]
    return root_spans


def _get_agent_show_name(span: dict):
    agent_name_prefix = SPAN_NAME_PREFIX_EVENT_AGENT
    name = span.get("name")
    if name and name.startswith(agent_name_prefix):
        name = name[len(agent_name_prefix):]
    if name and '---' in name:
        name = name.split('---', 1)[0]
    return name


def _remove_span_detail(root_spans: list):
    keys_to_keep = {'span_id', 'show_name', 'task_group_id', 'event_id'}
    for span in root_spans:
        keys_to_remove = [key for key in span.keys() if key not in keys_to_keep]
        for key in keys_to_remove:
            span.pop(key, None)
        if 'children' in span:
            _remove_span_detail(span['children'])


def _get_top_task_nodes(spans_dict):
    task_nodes = [
        span for span in spans_dict.values()
        if span.get('name', '').startswith('task.')
    ]
    top_task_nodes = []
    for task_node in task_nodes:
        parent_id = task_node.get('parent_id')
        is_top = True

        while parent_id:
            parent_span = spans_dict.get(parent_id)
            if not parent_span:
                break

            if parent_span.get('name', '').startswith('task.'):
                is_top = False
                break

            parent_id = parent_span.get('parent_id')

        if is_top:
            top_task_nodes.append(task_node)

    return top_task_nodes


def _get_root_nodes(edges):
    sources = set()
    targets = set()
    for edge in edges:
        sources.add(edge['source'])
        targets.add(edge['target'])
    return sources - targets


def _build_graph(root_spans: list):
    nodes = []
    edges = []

    group_id_counter = 0

    def __process_group_span(parent_spans, group_id, group_spans):
        nonlocal group_id_counter
        group_id_counter += 1
        # add group node
        group_node = {
            'span_id': f'group_{group_id_counter}',
            'group_id': group_id,
            'show_name': 'Task Group'
        }
        nodes.append(group_node)

        # add edges from parent_spans to group node
        for parent_span in parent_spans:
            edges.append({
                'source': parent_span['span_id'],
                'target': group_node['span_id']
            })

        # add edges from group node to children spans
        last_spans = []
        for child in group_spans:
            edges.append({
                'source': group_node['span_id'],
                'target': child['span_id']
            })
            last_spans.extend(__process_span(child))
        return last_spans

    def __process_span(span):
        nonlocal group_id_counter
        nodes.append(span)
        if 'children' in span:
            groups = {}
            for child in span['children']:
                group_id = child.get('task_group_id', id(child))
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append(child)

            last_spans = [span]  # The leaf nodes of the current subtree
            for group_id, group_spans in groups.items():
                if len(group_spans) > 1:
                    parent_spans = last_spans
                    last_spans = __process_group_span(parent_spans, group_id, group_spans)
                else:
                    child_span = group_spans[0]
                    # add edges from last_spans to child
                    for prev_node in last_spans:
                        edges.append({
                            'source': prev_node['span_id'],
                            'target': child_span['span_id']
                        })
                    last_spans = __process_span(child_span)
        return last_spans

    for span in root_spans:
        __process_span(span)

    return {
        'nodes': nodes,
        'edges': edges
    }


def get_agent_flow(trace_id):
    from aworld.trace.server import get_trace_server

    storage = get_trace_server().get_storage()
    spans = storage.get_all_spans(trace_id)
    spans_dict = {span.span_id: span.dict() for span in spans}
    children_spans = []
    top_task_nodes = _get_top_task_nodes(spans_dict)

    filtered_spans = {}
    for span_id, span in spans_dict.items():
        if span.get('is_event', False) and span.get('run_type') == RunType.AGNET.value:
            span['show_name'] = _get_agent_show_name(span)
            span['event_id'] = span.get('attributes', {}).get('event.id')
            filtered_spans[span_id] = span

    sub_task_spans = []
    for span in list(filtered_spans.values()):
        skip_this_span = False
        parent_id = span['parent_id'] if span['parent_id'] else None

        while parent_id and parent_id not in filtered_spans:
            parent_span = spans_dict.get(parent_id)
            if parent_span and parent_span.get('run_type') == RunType.TASK.value:
                # if str(parent_span['attributes'].get(semconv.TASK_IS_SUB_TASK)).lower() == 'true':
                #     sub_task_spans.append(span)
                #     skip_this_span = True
                #     break
                # else:
                # print(f"parent_span_name: {parent_span['name']}")
                span['task_group_id'] = parent_span['attributes'].get(semconv.TASK_GROUP_ID)
            parent_id = parent_span['parent_id'] if parent_span and parent_span['parent_id'] else None

        if skip_this_span:
            continue
        if parent_id:
            parent_span = filtered_spans.get(parent_id)
            if not parent_span:
                continue

            if 'children' not in parent_span:
                parent_span['children'] = []
            parent_span['children'].append(span)
            children_spans.append(span)

    filtered_span_list = [span for span in filtered_spans.values() if span not in sub_task_spans]
    root_spans = [span for span in filtered_span_list
                  if span not in children_spans]

    data = _build_graph(root_spans)
    _remove_span_detail(data["nodes"])

    # add query start node
    _add_query_node(data, top_task_nodes)
    return data

def _add_query_node(data, top_task_nodes):
    top_task_node = top_task_nodes[0] if top_task_nodes else None
    if top_task_node:
        start_node_span_id = f'{uuid.uuid4().hex[:16]}'
        data['nodes'].append({
            'span_id': start_node_span_id,
            'show_name': top_task_node['attributes'].get(semconv.TASK_INPUT),
        })
        root_nodes = _get_root_nodes(data['edges'])
        if root_nodes:
            for root_node in root_nodes:
                data['edges'].append({
                    'source': start_node_span_id,
                    'target': root_node,
                })
        else:
            for root_node in data['nodes']:
                if root_node['span_id'] != start_node_span_id:
                    data['edges'].append({
                        'source': start_node_span_id,
                        'target': root_node['span_id'],
                    })
