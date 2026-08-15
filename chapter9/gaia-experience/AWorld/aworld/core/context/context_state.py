#!/usr/bin/env python3
# coding: utf-8

"""
Context State Management System
Provides hierarchical state management with parent-child state inheritance
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ContextState:
    """
    Hierarchical state management class
    
    Supports the following features:
    - Parent-child state inheritance: Child states can access parent state data
    - State priority: Local state takes precedence over parent state
    - State isolation: Write operations only affect local state
    - Flexible lookup: Supports multi-level state lookup
    """
    
    def __init__(self, parent_state: Optional['ContextState'] = None):
        """
        Initialize ContextState
        
        Args:
            parent_state: Parent state object for implementing state inheritance
        """
        self._data: Dict[str, Any] = {}
        self._parent_state: Optional['ContextState'] = parent_state
    
    def __getitem__(self, key: str) -> Any:
        """Get state value with parent state inheritance support"""
        if key in self._data:
            return self._data[key]
        elif self._parent_state is not None:
            return self._parent_state[key]
        else:
            logger.error(f"Key '{key}' not found in state")
            return None
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set state value, only writes to local state"""
        self._data[key] = value
    
    def __delitem__(self, key: str) -> None:
        """Delete state value, only deletes from local state"""
        if key in self._data:
            del self._data[key]
        else:
            logger.error(f"Key '{key}' not found in local state")
    
    def __contains__(self, key: str) -> bool:
        """Check if contains specified key, including parent state"""
        return key in self._data or (self._parent_state is not None and key in self._parent_state)
    
    def __len__(self) -> int:
        """Return the count of all accessible states (including parent state)"""
        keys = set(self._data.keys())
        if self._parent_state is not None:
            keys.update(self._parent_state.keys())
        return len(keys)
    
    def __iter__(self):
        """Iterate over all accessible keys (including parent state)"""
        keys = set(self._data.keys())
        if self._parent_state is not None:
            keys.update(self._parent_state.keys())
        return iter(keys)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get state value, return default value if not exists
        
        Args:
            key: The key to get
            default: Default value
            
        Returns:
            Value corresponding to key or default value
        """
        if key in self._data:
            return self._data[key]
        elif self._parent_state is not None:
            return self._parent_state.get(key, default)
        else:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set state value, only writes to local state
        
        Args:
            key: The key to set
            value: The value to set
        """
        self._data[key] = value
    
    def update(self, other: Union[Dict[str, Any], 'ContextState'] = None, **kwargs) -> None:
        """
        Batch update state
        
        Args:
            other: Data to update, can be dict or another ContextState
            **kwargs: Keyword arguments to update
            
        Examples:
            # Traditional dict update
            state.update({"key1": "value1", "key2": "value2"})
            
            # ContextState update
            state.update(other_state)
            
            # Keyword arguments update
            state.update(task_list=plan_result.task_list, status="completed")
            
            # Mixed update
            state.update({"key1": "value1"}, key2="value2", key3="value3")
        """
        try:
            # Handle positional argument
            if other is not None:
                if isinstance(other, dict):
                    self._data.update(other)
                elif isinstance(other, ContextState):
                    self._data.update(other._data)
                else:
                    logger.error(f"update() first argument must be dict or ContextState, got {type(other)}")
                    return
            
            # Handle keyword arguments
            if kwargs:
                self._data.update(kwargs)
                
        except Exception as e:
            logger.error(f"Error updating state: {e}")
    
    def pop(self, key: str, default: Any = None) -> Any:
        """
        Delete and return value of specified key, only operates on local state
        
        Args:
            key: The key to delete
            default: Default value to return if key doesn't exist
            
        Returns:
            The deleted value or default value
        """
        return self._data.pop(key, default)
    
    def clear(self) -> None:
        """Clear local state (does not affect parent state)"""
        self._data.clear()
    
    def keys(self) -> List[str]:
        """Return list of all accessible keys (including parent state)"""
        keys = set(self._data.keys())
        if self._parent_state is not None:
            keys.update(self._parent_state.keys())
        return list(keys)
    
    def values(self) -> List[Any]:
        """Return list of all accessible values (including parent state)"""
        return [self[key] for key in self.keys()]
    
    def items(self) -> List[tuple]:
        """Return list of all accessible (key, value) pairs (including parent state)"""
        return [(key, self[key]) for key in self.keys()]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary, including inherited parent state
        
        Returns:
            Dictionary containing all accessible states
        """
        result = {}
        if self._parent_state is not None:
            result.update(self._parent_state.to_dict())
        result.update(self._data)
        return result
    
    def local_dict(self) -> Dict[str, Any]:
        """
        Get local state dictionary (excluding parent state)
        
        Returns:
            Dictionary containing only local state
        """
        return self._data.copy()
    
    def set_parent(self, parent_state: Optional['ContextState']) -> None:
        """
        Set parent state
        
        Args:
            parent_state: New parent state object
        """
        self._parent_state = parent_state
    
    def get_parent(self) -> Optional['ContextState']:
        """
        Get parent state object
        
        Returns:
            Parent state object or None
        """
        return self._parent_state
    
    def has_parent(self) -> bool:
        """
        Check if has parent state
        
        Returns:
            True if has parent state, False otherwise
        """
        return self._parent_state is not None
    
    def __repr__(self) -> str:
        """Return string representation of state"""
        local_count = len(self._data)
        total_count = len(self)
        parent_info = f" (with parent: {total_count - local_count} inherited)" if self._parent_state else ""
        return f"ContextState(local: {local_count}{parent_info})"
    
    def __str__(self) -> str:
        """Return detailed string representation of state"""
        return f"ContextState({self.to_dict()})"
