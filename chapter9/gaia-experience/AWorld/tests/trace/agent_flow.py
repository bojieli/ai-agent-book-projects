from aworld.trace.server import get_trace_server
from aworld.trace.constants import RunType, SPAN_NAME_PREFIX_EVENT_AGENT
from aworld.trace.instrumentation import semconv


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
    storage = get_trace_server().get_storage()
    spans = storage.get_all_spans(trace_id)
    spans_dict = {span.span_id: span.dict() for span in spans}
    children_spans = []

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
                if str(parent_span['attributes'].get(semconv.TASK_IS_SUB_TASK)).lower() == 'true':
                    sub_task_spans.append(span)
                    skip_this_span = True
                    break
                else:
                    print(f"parent_span_name: {parent_span['name']}")
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
    return data
