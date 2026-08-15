import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from pydantic import BaseModel

from aworld.core.memory import MemoryStore
from aworld.memory.models import (
    MemoryItem, MemoryAIMessage, MemoryHumanMessage, MemorySummary,
    MemorySystemMessage, MemoryToolMessage, MessageMetadata,
    UserProfile, AgentExperience, ConversationSummary
)
from aworld.models.model_response import ToolCall


class SQLiteMemoryStore(MemoryStore):
    """
    SQLite implementation of the memory store.
    
    This class provides a SQLite-based storage backend for the memory system,
    implementing all required methods from the MemoryStore interface.
    """
    
    def __init__(self, db_path: str = "./data/aworld_memory.db"):
        """
        Initialize SQLite memory store.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS aworld_memory_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    memory_meta TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    deleted BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS aworld_memory_histories (
                    memory_id TEXT NOT NULL,
                    history_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (memory_id, history_id),
                    FOREIGN KEY (memory_id) REFERENCES aworld_memory_items (id),
                    FOREIGN KEY (history_id) REFERENCES aworld_memory_items (id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_type ON aworld_memory_items (memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_created ON aworld_memory_items (created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_deleted ON aworld_memory_items (deleted)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_meta_user_id ON aworld_memory_items (json_extract(memory_meta, '$.user_id'))")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_meta_agent_id ON aworld_memory_items (json_extract(memory_meta, '$.agent_id'))")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_meta_session_id ON aworld_memory_items (json_extract(memory_meta, '$.session_id'))")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_meta_task_id ON aworld_memory_items (json_extract(memory_meta, '$.task_id'))")
            
            conn.commit()
    
    def _serialize_content(self, content: Any) -> str:
        """Serialize content to JSON string."""
        if content is None:
            return ""
        if isinstance(content, (dict, list, str, int, float, bool)):
            return json.dumps(content, ensure_ascii=False)
        if isinstance(content, BaseModel):
            return content.model_dump_json()
        return json.dumps(content, ensure_ascii=False, default=str)
    
    def _deserialize_content(self, content_str: str) -> Any:
        """Deserialize content from JSON string."""
        if not content_str:
            return None
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            return content_str
    
    def _serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """Serialize metadata to JSON string."""
        if not metadata:
            return "{}"
        return json.dumps(metadata, ensure_ascii=False)
    
    def _deserialize_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Deserialize metadata from JSON string."""
        if not metadata_str:
            return {}
        try:
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {}
    
    def _serialize_tags(self, tags: List[str]) -> str:
        """Serialize tags list to JSON string."""
        if not tags:
            return "[]"
        return json.dumps(tags, ensure_ascii=False)
    
    def _deserialize_tags(self, tags_str: str) -> List[str]:
        """Deserialize tags from JSON string."""
        if not tags_str:
            return []
        try:
            return json.loads(tags_str)
        except json.JSONDecodeError:
            return []
    
    def _memory_item_to_row(self, item: MemoryItem) -> tuple:
        """Convert MemoryItem to database row tuple."""
        content = self._serialize_content(item.content)
        metadata = self._serialize_metadata(item.metadata)
        tags = self._serialize_tags(item.tags)
        
        return (
            item.id,
            content,
            item.created_at or datetime.now().isoformat(),
            item.updated_at or datetime.now().isoformat(),
            metadata,
            tags,
            item.memory_type,
            item.version,
            item.deleted
        )
    
    def _row_to_memory_item(self, row: tuple) -> Optional[MemoryItem]:
        """Convert database row to MemoryItem."""
        if not row:
            return None
            
        (id_, content, created_at, updated_at, metadata, tags, memory_type, version, deleted) = row
        
        memory_meta = self._deserialize_metadata(metadata)
        role = memory_meta.get('role')
        
        base_data = {
            'id': id_,
            'created_at': created_at,
            'updated_at': updated_at,
            'tags': self._deserialize_tags(tags),
            'version': version,
            'deleted': bool(deleted)
        }
        
        # Handle different message types
        if role == 'system':
            return MemorySystemMessage(
                content=self._deserialize_content(content),
                metadata=MessageMetadata(**memory_meta),
                **base_data
            )
        elif role == 'user':
            return MemoryHumanMessage(
                metadata=MessageMetadata(**memory_meta),
                content=self._deserialize_content(content),
                **base_data
            )
        elif role == 'assistant':
            tool_calls_jsons = memory_meta.get('tool_calls', [])
            tool_calls = []
            for tool_call_json in tool_calls_jsons:
                tool_call = ToolCall.from_dict(tool_call_json)
                tool_calls.append(tool_call)
            return MemoryAIMessage(
                content=self._deserialize_content(content),
                tool_calls=tool_calls,
                metadata=MessageMetadata(**memory_meta),
                **base_data
            )
        elif role == 'tool':
            return MemoryToolMessage(
                tool_call_id=memory_meta.get('tool_call_id'),
                content=self._deserialize_content(content),
                status=memory_meta.get('status', 'success'),
                metadata=MessageMetadata(**memory_meta),
                **base_data
            )
        elif memory_type == 'user_profile':
            content_data = self._deserialize_content(content)
            if not content_data or not isinstance(content_data, dict):
                return None
            return UserProfile(
                key=content_data.get('key'),
                value=content_data.get('value'),
                user_id=memory_meta.get('user_id'),
                metadata=memory_meta,
                **base_data
            )
        elif memory_type == 'agent_experience':
            content_data = self._deserialize_content(content)
            if not content_data or not isinstance(content_data, dict):
                return None
            return AgentExperience(
                skill=content_data.get('skill'),
                actions=content_data.get('actions'),
                agent_id=memory_meta.get('agent_id'),
                metadata=memory_meta,
                **base_data
            )
        elif memory_type == 'summary':
            content_data = self._deserialize_content(content)
            if not content_data or not isinstance(content_data, str):
                return None
            item_ids = memory_meta.get('item_ids', [])
            summary_metadata = MessageMetadata(
                agent_id=memory_meta.get('agent_id'),
                agent_name=memory_meta.get('agent_name'),
                session_id=memory_meta.get('session_id'),
                task_id=memory_meta.get('task_id'),
                user_id=memory_meta.get('user_id')
            )
            return MemorySummary(
                item_ids=item_ids,
                summary=content_data,
                metadata=summary_metadata,
                **base_data
            )
        elif memory_type == 'conversation_summary':
            content_data = self._deserialize_content(content)
            if not content_data or not isinstance(content_data, str):
                return None
            # Preserve all custom metadata attributes
            conversation_summary_metadata = MessageMetadata(**memory_meta)
            return ConversationSummary(
                user_id=memory_meta.get('user_id'),
                session_id=memory_meta.get('session_id'),
                summary=content_data,
                metadata=conversation_summary_metadata,
                **base_data
            )
        else:
            return MemoryItem(
                content=self._deserialize_content(content),
                metadata=memory_meta,
                memory_type=memory_type,
                **base_data
            )
    
    def _build_filters(self, filters: Dict[str, Any] = None) -> tuple[str, tuple]:
        """Build SQL WHERE clause and parameters from filters."""
        if not filters:
            return "WHERE deleted = FALSE", ()
        
        conditions = ["deleted = FALSE"]
        params = []
        
        for key, value in filters.items():
            if value is not None:
                if key in ['user_id', 'agent_id', 'session_id', 'task_id', 'agent_name', 'tool_call_id']:
                    conditions.append(f"json_extract(memory_meta, '$.{key}') = ?")
                    params.append(value)
                elif key == 'memory_type':
                    if isinstance(value, list):
                        placeholders = ','.join(['?' for _ in value])
                        conditions.append(f"memory_type IN ({placeholders})")
                        params.extend(value)
                    else:
                        conditions.append("memory_type = ?")
                        params.append(value)
        
        where_clause = "WHERE " + " AND ".join(conditions)
        return where_clause, tuple(params)
    
    def add(self, memory_item: MemoryItem) -> None:
        """Add a new memory item to the store."""
        with sqlite3.connect(self.db_path) as conn:
            row = self._memory_item_to_row(memory_item)
            conn.execute("""
                INSERT INTO aworld_memory_items 
                (id, content, created_at, updated_at, memory_meta, tags, memory_type, version, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            conn.commit()
    
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, content, created_at, updated_at, memory_meta, tags, memory_type, version, deleted
                FROM aworld_memory_items 
                WHERE id = ? AND deleted = FALSE
            """, (memory_id,))
            row = cursor.fetchone()
            return self._row_to_memory_item(row)
    
    def get_first(self, filters: Dict[str, Any] = None) -> Optional[MemoryItem]:
        """Get the first memory item matching the filters."""
        with sqlite3.connect(self.db_path) as conn:
            where_clause, params = self._build_filters(filters)
            cursor = conn.execute(f"""
                SELECT id, content, created_at, updated_at, memory_meta, tags, memory_type, version, deleted
                FROM aworld_memory_items 
                {where_clause}
                ORDER BY created_at ASC
                LIMIT 1
            """, params)
            row = cursor.fetchone()
            return self._row_to_memory_item(row)
    
    def total_rounds(self, filters: Dict[str, Any] = None) -> int:
        """Get total number of memory rounds matching the filters."""
        with sqlite3.connect(self.db_path) as conn:
            where_clause, params = self._build_filters(filters)
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM aworld_memory_items {where_clause}
            """, params)
            return cursor.fetchone()[0]
    
    def get_all(self, filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """Get all memory items matching the filters."""
        with sqlite3.connect(self.db_path) as conn:
            where_clause, params = self._build_filters(filters)
            cursor = conn.execute(f"""
                SELECT id, content, created_at, updated_at, memory_meta, tags, memory_type, version, deleted
                FROM aworld_memory_items 
                {where_clause}
                ORDER BY created_at ASC
            """, params)
            rows = cursor.fetchall()
            return [self._row_to_memory_item(row) for row in rows if row]
    
    def get_last_n(self, last_rounds: int, filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """Get the last N memory rounds matching the filters."""
        with sqlite3.connect(self.db_path) as conn:
            where_clause, params = self._build_filters(filters)
            cursor = conn.execute(f"""
                SELECT id, content, created_at, updated_at, memory_meta, tags, memory_type, version, deleted
                FROM aworld_memory_items 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params + (last_rounds,))
            rows = cursor.fetchall()
            # Reverse to maintain chronological order
            return [self._row_to_memory_item(row) for row in reversed(rows) if row]
    
    def update(self, memory_item: MemoryItem) -> None:
        """Update a memory item."""
        with sqlite3.connect(self.db_path) as conn:
            row = self._memory_item_to_row(memory_item)
            conn.execute("""
                UPDATE aworld_memory_items 
                SET content = ?, created_at = ?, updated_at = ?, memory_meta = ?, 
                    tags = ?, memory_type = ?, version = ?, deleted = ?
                WHERE id = ?
            """, row[1:] + (memory_item.id,))
            conn.commit()
    
    def delete(self, memory_id: str) -> None:
        """Soft delete a memory item."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE aworld_memory_items 
                SET deleted = TRUE, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), memory_id))
            conn.commit()
    
    def delete_items(self, message_types: List[str], session_id: str, task_id: str, filters: Dict[str, Any] = None) -> None:
        """Delete multiple memory items by message types, session_id, and task_id."""
        filters = filters or {}
        filters['memory_type'] = message_types
        filters['session_id'] = session_id
        filters['task_id'] = task_id
        
        with sqlite3.connect(self.db_path) as conn:
            where_clause, params = self._build_filters(filters)
            # Remove the "WHERE" keyword and convert to proper WHERE clause for UPDATE
            where_conditions = where_clause.replace('WHERE ', '')
            conn.execute(f"""
                UPDATE aworld_memory_items 
                SET deleted = TRUE, updated_at = ?
                WHERE {where_conditions}
            """, (datetime.now().isoformat(),) + params)
            conn.commit()
    
    def history(self, memory_id: str) -> Optional[List[MemoryItem]]:
        """Get the history of a memory item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT m.id, m.content, m.created_at, m.updated_at, m.memory_meta, 
                       m.tags, m.memory_type, m.version, m.deleted
                FROM aworld_memory_items m
                JOIN aworld_memory_histories h ON h.history_id = m.id
                WHERE h.memory_id = ? AND m.deleted = FALSE
                ORDER BY m.created_at ASC
            """, (memory_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            return [self._row_to_memory_item(row) for row in rows if row]
    
    def close(self) -> None:
        """Close database connections."""
        # SQLite connections are automatically closed when exiting context managers
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 