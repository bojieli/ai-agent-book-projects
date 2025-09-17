"""
Formatter for memory operations output
Provides consistent formatting for memory operation lists
"""

from typing import List, Dict, Any
import json


def format_memory_operations(operations: List[Dict[str, Any]], verbose: bool = False) -> str:
    """
    Format memory operations for display
    
    Args:
        operations: List of memory operations
        verbose: Whether to show detailed output
        
    Returns:
        Formatted string representation of operations
    """
    if not operations:
        return "📝 Memory Operations: None (no updates needed)"
    
    lines = []
    lines.append(f"📝 Memory Operations ({len(operations)} total):")
    lines.append("-" * 50)
    
    for i, op in enumerate(operations, 1):
        # Choose icon based on action
        icon_map = {
            'add': '➕',
            'update': '📝',
            'delete': '🗑️'
        }
        icon = icon_map.get(op['action'], '❓')
        
        # Main operation line
        lines.append(f"{i}. {icon} {op['action'].upper()}")
        
        # Content or memory ID
        if op.get('content'):
            content = op['content']
            # Truncate if too long and not verbose
            if not verbose and len(content) > 100:
                content = content[:97] + "..."
            lines.append(f"   Content: {content}")
        elif op.get('memory_id'):
            lines.append(f"   Memory ID: {op['memory_id']}")
        
        # Reason
        if op.get('reason'):
            lines.append(f"   Reason: {op['reason']}")
        
        # Tags
        if op.get('tags'):
            lines.append(f"   Tags: {', '.join(op['tags'])}")
        
        lines.append("")  # Empty line between operations
    
    return "\n".join(lines)


def format_operation_summary(summary: Dict[str, int]) -> str:
    """
    Format operation summary statistics
    
    Args:
        summary: Dictionary with counts of operations
        
    Returns:
        Formatted summary string
    """
    added = summary.get('added', 0)
    updated = summary.get('updated', 0)
    deleted = summary.get('deleted', 0)
    failed = summary.get('failed', 0)
    
    parts = []
    if added > 0:
        parts.append(f"{added} added")
    if updated > 0:
        parts.append(f"{updated} updated")
    if deleted > 0:
        parts.append(f"{deleted} deleted")
    if failed > 0:
        parts.append(f"{failed} failed")
    
    if not parts:
        return "No operations performed"
    
    return "Summary: " + ", ".join(parts)


def display_memory_operations(results: Dict[str, Any], verbose: bool = False):
    """
    Display memory operations from processing results
    
    Args:
        results: Processing results containing operations
        verbose: Whether to show detailed output
    """
    operations = results.get('operations', [])
    summary = results.get('summary', {})
    
    # Display operations
    print(format_memory_operations(operations, verbose))
    
    # Display summary
    print(format_operation_summary(summary))
    print("-" * 50)


def operations_to_json(operations: List[Dict[str, Any]], pretty: bool = True) -> str:
    """
    Convert operations to JSON string
    
    Args:
        operations: List of memory operations
        pretty: Whether to pretty-print the JSON
        
    Returns:
        JSON string representation
    """
    if pretty:
        return json.dumps(operations, indent=2, ensure_ascii=False)
    else:
        return json.dumps(operations, ensure_ascii=False)


def filter_operations_by_action(operations: List[Dict[str, Any]], action: str) -> List[Dict[str, Any]]:
    """
    Filter operations by action type
    
    Args:
        operations: List of memory operations
        action: Action type to filter ('add', 'update', 'delete')
        
    Returns:
        Filtered list of operations
    """
    return [op for op in operations if op.get('action') == action]

