# coding: utf-8

# Derived from browser_use DomService, we use it as a utility method, and supports sync and async.

import gc
import json

from typing import Dict, Any, Tuple, Optional

from aworld.utils.async_func import async_func
from examples.common.tools.browsers.util.dom import DOMElementNode, DOMBaseNode, DOMTextNode, ViewportInfo
from aworld.logs.util import logger


async def async_build_dom_tree(page, js_code: str, args: Dict[str, Any]) -> Tuple[DOMElementNode, Dict[int, DOMElementNode]]:
    if await page.evaluate('1+1') != 2:
        raise ValueError('The page cannot evaluate javascript code properly')

    # NOTE: We execute JS code in the browser to extract important DOM information.
    #       The returned hash map contains information about the DOM tree and the
    #       relationship between the DOM elements.
    try:
        eval_page = await page.evaluate(js_code, args)
    except Exception as e:
        logger.error('Error evaluating JavaScript: %s', e)
        raise

    # Only log performance metrics in debug mode
    if args.get("debugMode") and 'perfMetrics' in eval_page:
        logger.debug('DOM Tree Building Performance Metrics:\n%s', json.dumps(eval_page['perfMetrics'], indent=2))

    return await async_func(_construct_dom_tree)(eval_page)


def build_dom_tree(page, js_code: str, args: Dict[str, Any]) -> Tuple[DOMElementNode, Dict[int, DOMElementNode]]:
    if page.evaluate('1+1') != 2:
        raise ValueError('The page cannot evaluate javascript code properly')

    # NOTE: We execute JS code in the browser to extract important DOM information.
    #       The returned hash map contains information about the DOM tree and the
    #       relationship between the DOM elements.
    try:
        eval_page = page.evaluate(js_code, args)
    except Exception as e:
        logger.error('Error evaluating JavaScript: %s', e)
        raise

    # Only log performance metrics in debug mode
    if args.get("debugMode") and 'perfMetrics' in eval_page:
        logger.debug('DOM Tree Building Performance Metrics:\n%s', json.dumps(eval_page['perfMetrics'], indent=2))

    return _construct_dom_tree(eval_page)


def _construct_dom_tree(eval_page: dict, ) -> tuple[DOMElementNode, Dict[int, DOMElementNode]]:
    js_node_map = eval_page['map']
    js_root_id = eval_page['rootId']

    selector_map = {}
    node_map = {}

    for id, node_data in js_node_map.items():
        node, children_ids = _parse_node(node_data)
        if node is None:
            continue

        node_map[id] = node

        if isinstance(node, DOMElementNode) and node.highlight_index is not None:
            selector_map[node.highlight_index] = node

        # NOTE: We know that we are building the tree bottom up
        #       and all children are already processed.
        if isinstance(node, DOMElementNode):
            for child_id in children_ids:
                if child_id not in node_map:
                    continue

                child_node = node_map[child_id]

                child_node.parent = node
                node.children.append(child_node)

    html_to_dict = node_map[str(js_root_id)]

    del node_map
    del js_node_map
    del js_root_id

    gc.collect()

    if html_to_dict is None or not isinstance(html_to_dict, DOMElementNode):
        raise ValueError('Failed to parse HTML to dictionary')

    return html_to_dict, selector_map


def _parse_node(node_data: dict, ) -> Tuple[Optional[DOMBaseNode], list[int]]:
    if not node_data:
        return None, []

    # Process text nodes immediately
    if node_data.get('type') == 'TEXT_NODE':
        text_node = DOMTextNode(
            text=node_data['text'],
            is_visible=node_data['isVisible'],
            parent=None,
        )
        return text_node, []

    # Process coordinates if they exist for element nodes

    viewport_info = None

    if 'viewport' in node_data:
        viewport_info = ViewportInfo(
            width=node_data['viewport']['width'],
            height=node_data['viewport']['height'],
        )

    element_node = DOMElementNode(
        tag_name=node_data['tagName'],
        xpath=node_data['xpath'],
        attributes=node_data.get('attributes', {}),
        children=[],
        is_visible=node_data.get('isVisible', False),
        is_interactive=node_data.get('isInteractive', False),
        is_top_element=node_data.get('isTopElement', False),
        is_in_viewport=node_data.get('isInViewport', False),
        highlight_index=node_data.get('highlightIndex'),
        shadow_root=node_data.get('shadowRoot', False),
        parent=None,
        viewport_info=viewport_info,
    )

    children_ids = node_data.get('children', [])

    return element_node, children_ids
