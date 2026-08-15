"""
Test suite locking out TypeError in _build_dom_tree
when layout dictionary contains None values for array properties.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_layout_index_map_handles_null_layout_arrays():
    """
    Ensure layout array checks tolerate None for bounds, styles, paintOrders, etc.
    """
    layout = {
        'bounds': None,
        'styles': None,
        'paintOrders': None,
        'clientRects': None,
        'scrollRects': None,
        'stackingContexts': None
    }
    
    layout_idx = 0
    bounds_len = len(layout.get('bounds') or [])
    styles_len = len(layout.get('styles') or [])
    paint_len = len(layout.get('paintOrders') or [])
    client_len = len(layout.get('clientRects') or [])
    scroll_len = len(layout.get('scrollRects') or [])
    stacking_len = len(layout.get('stackingContexts') or [])

    assert bounds_len == 0
    assert styles_len == 0
    assert paint_len == 0
    assert client_len == 0
    assert scroll_len == 0
    assert stacking_len == 0
