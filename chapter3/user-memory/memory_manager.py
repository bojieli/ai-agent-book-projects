"""
Memory Manager module for handling different memory mechanisms
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
import logging
from config import Config, MemoryMode

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize text for duplicate detection: lowercase and collapse whitespace.

    Used by the offline consolidation/dedup logic so that notes that differ only
    in casing or spacing are recognised as the same fact.
    """
    return " ".join(str(text or "").lower().split())


@dataclass
class MemoryNote:
    """Represents a single memory note"""
    note_id: str
    content: str
    session_id: str
    created_at: str
    updated_at: str
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryNote':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class MemoryCard:
    """Represents a memory card in JSON structure"""
    category: str
    subcategory: str
    key: str
    value: Any
    session_id: str
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryCard':
        """Create from dictionary"""
        return cls(**data)


class BaseMemoryManager(ABC):
    """Base class for memory managers"""
    
    def __init__(self, user_id: str, verbose: bool = False):
        """
        Initialize memory manager
        
        Args:
            user_id: Unique identifier for the user
            verbose: Whether to print detailed operations
        """
        self.user_id = user_id
        self.verbose = verbose
        self.memory_file = os.path.join(Config.MEMORY_STORAGE_DIR, f"{user_id}_memory.json")
        self.load_memory()
    
    @abstractmethod
    def load_memory(self):
        """Load memory from storage"""
        pass
    
    @abstractmethod
    def save_memory(self):
        """Save memory to storage"""
        pass
    
    @abstractmethod
    def add_memory(self, content: Any, session_id: str, **kwargs):
        """Add a new memory item"""
        pass
    
    @abstractmethod
    def update_memory(self, memory_id: str, content: Any, session_id: str, **kwargs):
        """Update an existing memory item"""
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str):
        """Delete a memory item"""
        pass
    
    @abstractmethod
    def get_context_string(self) -> str:
        """Get memory as a formatted string for LLM context"""
        pass
    
    @abstractmethod
    def search_memories(self, query: str) -> List[Any]:
        """Search memories by query"""
        pass


class NotesMemoryManager(BaseMemoryManager):
    """Memory manager using notes list approach"""
    
    def __init__(self, user_id: str, verbose: bool = False):
        self.notes: List[MemoryNote] = []
        super().__init__(user_id, verbose)
    
    def load_memory(self):
        """Load notes from storage"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notes = [MemoryNote.from_dict(note) for note in data.get('notes', [])]
                logger.info(f"Loaded {len(self.notes)} notes for user {self.user_id}")
            except Exception as e:
                logger.error(f"Error loading notes: {e}")
                self.notes = []
        else:
            self.notes = []
            logger.info(f"No existing memory file for user {self.user_id}")
    
    def save_memory(self):
        """Save notes to storage"""
        try:
            os.makedirs(os.path.dirname(self.memory_file) or ".", exist_ok=True)
            # Write to a temp file then atomically replace: a crash mid-dump
            # must not truncate the only copy of the persisted data.
            tmp_file = self.memory_file + '.tmp'
            with open(tmp_file, 'w', encoding='utf-8') as f:
                data = {
                    'user_id': self.user_id,
                    'type': 'notes',
                    'updated_at': datetime.now().isoformat(),
                    'notes': [note.to_dict() for note in self.notes]
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, self.memory_file)
            logger.info(f"Saved {len(self.notes)} notes for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving notes: {e}")
    
    def add_memory(self, content: str, session_id: str, tags: List[str] = None):
        """Add a new note"""
        note = MemoryNote(
            note_id=str(uuid.uuid4()),
            content=content,
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags=tags or []
        )
        self.notes.append(note)
        
        if self.verbose:
            print(f"  ➕ Added memory note (ID: {note.note_id[:8]}...):")
            print(f"     Content: {content[:100]}..." if len(content) > 100 else f"     Content: {content}")
            if tags:
                print(f"     Tags: {', '.join(tags)}")
        
        # Keep only the most recent notes if limit exceeded
        if len(self.notes) > Config.MAX_MEMORY_ITEMS:
            # Sort by updated_at and keep the most recent
            old_count = len(self.notes)
            self.notes.sort(key=lambda n: n.updated_at, reverse=True)
            self.notes = self.notes[:Config.MAX_MEMORY_ITEMS]
            if self.verbose:
                removed_count = old_count - len(self.notes)
                print(f"  🗑️  Removed {removed_count} oldest memory notes (limit: {Config.MAX_MEMORY_ITEMS})")
        
        self.save_memory()
        return note.note_id
    
    def update_memory(self, memory_id: str, content: str, session_id: str, tags: List[str] = None):
        """Update an existing note"""
        for note in self.notes:
            if note.note_id == memory_id:
                old_content = note.content
                note.content = content
                note.session_id = session_id
                note.updated_at = datetime.now().isoformat()
                if tags is not None:
                    note.tags = tags
                
                if self.verbose:
                    print(f"  📝 Updated memory note (ID: {memory_id[:8]}...):")
                    print(f"     Old: {old_content[:100]}..." if len(old_content) > 100 else f"     Old: {old_content}")
                    print(f"     New: {content[:100]}..." if len(content) > 100 else f"     New: {content}")
                    if tags:
                        print(f"     Tags: {', '.join(tags)}")
                
                self.save_memory()
                return True
        
        if self.verbose:
            print(f"  ⚠️  Memory note not found for update (ID: {memory_id[:8]}...)")
        return False
    
    def delete_memory(self, memory_id: str):
        """Delete a note"""
        original_count = len(self.notes)
        deleted_note = None
        for note in self.notes:
            if note.note_id == memory_id:
                deleted_note = note
                break
        
        self.notes = [note for note in self.notes if note.note_id != memory_id]
        
        if self.verbose:
            if deleted_note:
                print(f"  🗑️  Deleted memory note (ID: {memory_id[:8]}...):")
                print(f"     Content: {deleted_note.content[:100]}..." if len(deleted_note.content) > 100 else f"     Content: {deleted_note.content}")
            elif original_count == len(self.notes):
                print(f"  ⚠️  Memory note not found for deletion (ID: {memory_id[:8]}...)")
        
        self.save_memory()
    
    def clear_all_memories(self):
        """Clear all memories for this user - useful for testing"""
        self.notes = []
        self.save_memory()
        logger.info(f"Cleared all memories for user {self.user_id}")
        print(f"  🧹 Cleared all memories for user {self.user_id}")
    
    def get_context_string(self) -> str:
        """Get notes as formatted string for LLM context"""
        if not self.notes:
            return "No previous memory notes available."
        
        context = "User Memory Notes:\n\n"
        for i, note in enumerate(self.notes, 1):
            context += f"Note {i} (ID: {note.note_id}, Session: {note.session_id}):\n"
            context += f"  Content: {note.content}\n"
            if note.tags:
                context += f"  Tags: {', '.join(note.tags)}\n"
            context += f"  Updated: {note.updated_at}\n\n"
        
        return context
    
    def search_memories(self, query: str) -> List[MemoryNote]:
        """Search notes by query (simple text search)"""
        query_lower = query.lower()
        results = []
        for note in self.notes:
            if query_lower in note.content.lower() or any(query_lower in tag.lower() for tag in note.tags):
                results.append(note)
        return results

    def consolidate_memories(self, resolve_conflicts: bool = True) -> Dict[str, Any]:
        """Deterministically deduplicate and (optionally) conflict-resolve notes.

        This is the offline counterpart to the LLM-driven memory maintenance in
        the background processor. It runs without any API call so the storage /
        dedup / versioned-conflict logic can be exercised and inspected directly.

        Two passes:
          1. Dedup - notes whose normalized content is identical are merged into
             one (the most recently updated is kept, tags are unioned).
          2. Conflict resolution - remaining notes are grouped by their
             "attribute key" (the first tag, e.g. "home_address"). If notes in a
             group carry different content they describe conflicting versions of
             the same attribute; the most recently updated one wins and the older
             versions are superseded. This is version-based conflict detection.

        Args:
            resolve_conflicts: When False only the dedup pass runs.

        Returns:
            A report dict describing what was merged / superseded and the final
            note count. Nothing is written unless something actually changed.
        """
        report: Dict[str, Any] = {
            "duplicates_removed": 0,
            "merged_notes": [],
            "conflicts_resolved": [],
            "initial_count": len(self.notes),
            "final_count": len(self.notes),
        }

        # --- Pass 1: deduplicate identical content ---------------------------
        by_content: Dict[str, MemoryNote] = {}
        deduped: List[MemoryNote] = []
        for note in self.notes:
            norm = _normalize_text(note.content)
            existing = by_content.get(norm)
            if existing is None:
                by_content[norm] = note
                deduped.append(note)
                continue
            # Duplicate found - keep whichever is newer, union the tags.
            keeper, dropped = (existing, note) if existing.updated_at >= note.updated_at else (note, existing)
            keeper.tags = sorted(set(keeper.tags) | set(dropped.tags))
            keeper.updated_at = max(existing.updated_at, note.updated_at)
            if keeper is note:  # replace the reference we already stored
                idx = deduped.index(existing)
                deduped[idx] = note
                by_content[norm] = note
            report["duplicates_removed"] += 1
            report["merged_notes"].append(keeper.content)

        # --- Pass 2: resolve conflicting versions of the same attribute ------
        if resolve_conflicts:
            groups: Dict[str, List[MemoryNote]] = {}
            singletons: List[MemoryNote] = []
            for note in deduped:
                attr = note.tags[0] if note.tags else None
                if attr is None:
                    singletons.append(note)
                else:
                    groups.setdefault(attr, []).append(note)

            kept: List[MemoryNote] = list(singletons)
            for attr, members in groups.items():
                distinct = {_normalize_text(m.content) for m in members}
                if len(members) == 1 or len(distinct) == 1:
                    # No conflict: single note, or identical content under one attr.
                    kept.extend(members)
                    continue
                winner = max(members, key=lambda m: m.updated_at)
                superseded = [m for m in members if m is not winner]
                kept.append(winner)
                report["conflicts_resolved"].append({
                    "attribute": attr,
                    "kept": winner.content,
                    "superseded": [m.content for m in superseded],
                })
            deduped = kept

        changed = len(deduped) != len(self.notes)
        self.notes = deduped
        report["final_count"] = len(self.notes)

        if self.verbose and (report["duplicates_removed"] or report["conflicts_resolved"]):
            print(f"  🧹 Consolidated memories: {report['initial_count']} → {report['final_count']} notes")
            for c in report["conflicts_resolved"]:
                print(f"     ⚔️  Conflict on '{c['attribute']}': kept \"{c['kept']}\", "
                      f"superseded {c['superseded']}")

        if changed:
            self.save_memory()
        return report


class JSONMemoryManager(BaseMemoryManager):
    """Memory manager using hierarchical JSON cards approach"""
    
    def __init__(self, user_id: str, verbose: bool = False):
        self.memory_cards: Dict[str, Dict[str, Dict[str, Any]]] = {}
        super().__init__(user_id, verbose)
    
    def load_memory(self):
        """Load JSON memory cards from storage"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory_cards = data.get('memory_cards', {})
                logger.info(f"Loaded memory cards for user {self.user_id}")
            except Exception as e:
                logger.error(f"Error loading memory cards: {e}")
                self.memory_cards = {}
        else:
            self.memory_cards = {}
            logger.info(f"No existing memory file for user {self.user_id}")
    
    def save_memory(self):
        """Save JSON memory cards to storage"""
        try:
            os.makedirs(os.path.dirname(self.memory_file) or ".", exist_ok=True)
            # Write to a temp file then atomically replace: a crash mid-dump
            # must not truncate the only copy of the persisted data.
            tmp_file = self.memory_file + '.tmp'
            with open(tmp_file, 'w', encoding='utf-8') as f:
                data = {
                    'user_id': self.user_id,
                    'type': 'json_cards',
                    'updated_at': datetime.now().isoformat(),
                    'memory_cards': self.memory_cards
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, self.memory_file)
            logger.info(f"Saved memory cards for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving memory cards: {e}")
    
    def add_memory(self, content: Dict[str, Any], session_id: str, **kwargs):
        """
        Add a new memory card
        
        Args:
            content: Dictionary with 'category', 'subcategory', 'key', and 'value'
            session_id: Session identifier
        """
        category = content.get('category', 'general')
        subcategory = content.get('subcategory', 'info')
        key = content.get('key', str(uuid.uuid4()))
        value = content.get('value')
        
        if category not in self.memory_cards:
            self.memory_cards[category] = {}
        
        if subcategory not in self.memory_cards[category]:
            self.memory_cards[category][subcategory] = {}
        
        self.memory_cards[category][subcategory][key] = {
            'value': value,
            'source': session_id,
            'updated_at': datetime.now().isoformat()
        }
        
        if self.verbose:
            print(f"  ➕ Added JSON memory card: {category}.{subcategory}.{key}")
            value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            print(f"     Value: {value_str}")
        
        self.save_memory()
        return f"{category}.{subcategory}.{key}"
    
    def update_memory(self, memory_id: str, content: Dict[str, Any], session_id: str, **kwargs):
        """Update an existing memory card"""
        parts = memory_id.split('.')
        if len(parts) != 3:
            return False
        
        category, subcategory, key = parts
        
        if (category in self.memory_cards and 
            subcategory in self.memory_cards[category] and 
            key in self.memory_cards[category][subcategory]):
            
            old_value = self.memory_cards[category][subcategory][key]['value']
            value = content.get('value')
            self.memory_cards[category][subcategory][key] = {
                'value': value,
                'source': session_id,
                'updated_at': datetime.now().isoformat()
            }
            
            if self.verbose:
                print(f"  📝 Updated JSON memory card: {category}.{subcategory}.{key}")
                old_str = str(old_value)[:100] + "..." if len(str(old_value)) > 100 else str(old_value)
                new_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                print(f"     Old: {old_str}")
                print(f"     New: {new_str}")
            
            self.save_memory()
            return True
        
        if self.verbose:
            print(f"  ⚠️  JSON memory card not found for update: {memory_id}")
        return False
    
    def delete_memory(self, memory_id: str):
        """Delete a memory card"""
        parts = memory_id.split('.')
        if len(parts) != 3:
            if self.verbose:
                print(f"  ⚠️  Invalid memory ID format for deletion: {memory_id}")
            return
        
        category, subcategory, key = parts
        
        if (category in self.memory_cards and 
            subcategory in self.memory_cards[category] and 
            key in self.memory_cards[category][subcategory]):
            
            deleted_value = self.memory_cards[category][subcategory][key]['value']
            del self.memory_cards[category][subcategory][key]
            
            if self.verbose:
                print(f"  🗑️  Deleted JSON memory card: {category}.{subcategory}.{key}")
                value_str = str(deleted_value)[:100] + "..." if len(str(deleted_value)) > 100 else str(deleted_value)
                print(f"     Value: {value_str}")
            
            # Clean up empty subcategories and categories
            if not self.memory_cards[category][subcategory]:
                del self.memory_cards[category][subcategory]
            if not self.memory_cards[category]:
                del self.memory_cards[category]
            
            self.save_memory()
        else:
            if self.verbose:
                print(f"  ⚠️  JSON memory card not found for deletion: {memory_id}")
    
    def clear_all_memories(self):
        """Clear all memories for this user - useful for testing"""
        self.memory_cards = {}
        self.save_memory()
        logger.info(f"Cleared all memories for user {self.user_id}")
        print(f"  🧹 Cleared all memories for user {self.user_id}")
    
    def get_context_string(self) -> str:
        """Get memory cards as formatted string for LLM context"""
        if not self.memory_cards:
            return "No previous memory cards available."
        
        context = "User Memory Cards (Hierarchical JSON):\n\n"
        context += json.dumps(self.memory_cards, indent=2, ensure_ascii=False)
        return context
    
    def search_memories(self, query: str) -> List[Tuple[str, Any]]:
        """Search memory cards by query"""
        query_lower = query.lower()
        results = []
        
        for category, subcategories in self.memory_cards.items():
            for subcategory, items in subcategories.items():
                for key, data in items.items():
                    memory_path = f"{category}.{subcategory}.{key}"
                    value_str = str(data.get('value', '')).lower()
                    
                    if (query_lower in category.lower() or 
                        query_lower in subcategory.lower() or 
                        query_lower in key.lower() or 
                        query_lower in value_str):
                        
                        results.append((memory_path, data))
        
        return results


class AdvancedJSONMemoryManager(BaseMemoryManager):
    """
    Advanced JSON memory manager with complete memory card objects
    Structure: categories -> memory_card_key -> memory card (arbitrary JSON)
    """
    
    def __init__(self, user_id: str, verbose: bool = False):
        self.categories: Dict[str, Dict[str, Dict[str, Any]]] = {}
        super().__init__(user_id, verbose)
    
    def load_memory(self):
        """Load advanced JSON memory cards from storage"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories = data.get('categories', {})
                logger.info(f"Loaded advanced memory cards for user {self.user_id}")
            except Exception as e:
                logger.error(f"Error loading advanced memory cards: {e}")
                self.categories = {}
        else:
            self.categories = {}
            logger.info(f"No existing memory file for user {self.user_id}")
    
    def save_memory(self):
        """Save advanced JSON memory cards to storage"""
        try:
            os.makedirs(os.path.dirname(self.memory_file) or ".", exist_ok=True)
            # Write to a temp file then atomically replace: a crash mid-dump
            # must not truncate the only copy of the persisted data.
            tmp_file = self.memory_file + '.tmp'
            with open(tmp_file, 'w', encoding='utf-8') as f:
                data = {
                    'user_id': self.user_id,
                    'type': 'advanced_json_cards',
                    'updated_at': datetime.now().isoformat(),
                    'categories': self.categories
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, self.memory_file)
            logger.info(f"Saved advanced memory cards for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving advanced memory cards: {e}")
    
    def add_memory(self, content: Dict[str, Any], session_id: str, **kwargs):
        """
        Add a new memory card
        
        Args:
            content: Dictionary with 'category', 'card_key', and 'card' (complete memory card object)
            session_id: Session identifier
        
        Returns:
            Memory ID in format: category.card_key
        """
        category = content.get('category', 'general')
        card_key = content.get('card_key')
        card = content.get('card', {})
        
        if not card_key:
            card_key = str(uuid.uuid4())
        
        if category not in self.categories:
            self.categories[category] = {}
        
        # Add metadata to the card
        card['_metadata'] = {
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'source': session_id
        }
        
        # Ensure required fields
        if 'backstory' not in card:
            card['backstory'] = kwargs.get('backstory', '')
        if 'date_created' not in card:
            card['date_created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'person' not in card:
            card['person'] = kwargs.get('person', 'Unknown')
        if 'relationship' not in card:
            card['relationship'] = kwargs.get('relationship', 'primary account holder')
        
        self.categories[category][card_key] = card
        self.save_memory()
        
        return f"{category}.{card_key}"
    
    def update_memory(self, memory_id: str, content: Dict[str, Any], session_id: str, **kwargs):
        """
        Update an existing memory card
        
        Args:
            memory_id: Memory ID in format category.card_key
            content: Complete new memory card or partial updates
            session_id: Session identifier
        
        Returns:
            True if successful, False otherwise
        """
        parts = memory_id.split('.', 1)
        if len(parts) != 2:
            return False
        
        category, card_key = parts
        
        if category not in self.categories or card_key not in self.categories[category]:
            return False
        
        card = content.get('card', content)
        
        # Preserve existing metadata
        if '_metadata' in self.categories[category][card_key]:
            old_metadata = self.categories[category][card_key]['_metadata']
            card['_metadata'] = {
                'created_at': old_metadata.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat(),
                'source': session_id
            }
        else:
            card['_metadata'] = {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'source': session_id
            }
        
        # Update the card
        self.categories[category][card_key] = card
        self.save_memory()
        
        return True
    
    def delete_memory(self, memory_id: str):
        """Delete a memory card"""
        parts = memory_id.split('.', 1)
        if len(parts) != 2:
            return
        
        category, card_key = parts
        
        if category in self.categories and card_key in self.categories[category]:
            del self.categories[category][card_key]
            
            # Clean up empty categories
            if not self.categories[category]:
                del self.categories[category]
            
            self.save_memory()
    
    def clear_all_memories(self):
        """Clear all memories for this user"""
        self.categories = {}
        self.save_memory()
        logger.info(f"Cleared all memories for user {self.user_id}")
        print(f"  🧹 Cleared all memories for user {self.user_id}")
    
    def get_context_string(self) -> str:
        """Get memory cards as formatted string for LLM context"""
        if not self.categories:
            return "No previous memory cards available."
        
        context = "User Memory Cards (Advanced JSON Structure):\n\n"
        for category, cards in self.categories.items():
            context += f"Category: {category}\n"
            for card_key, card in cards.items():
                # Remove internal metadata from display
                display_card = {k: v for k, v in card.items() if k != '_metadata'}
                context += f"  Card '{card_key}':\n"
                context += f"    {json.dumps(display_card, indent=4, ensure_ascii=False)}\n"
        
        return context
    
    def search_memories(self, query: str) -> List[Tuple[str, Any]]:
        """Search memory cards by query"""
        query_lower = query.lower()
        results = []
        
        for category, cards in self.categories.items():
            for card_key, card in cards.items():
                memory_id = f"{category}.{card_key}"
                
                # Search in category, card_key, and all card fields
                card_str = json.dumps(card, ensure_ascii=False).lower()
                
                if (query_lower in category.lower() or 
                    query_lower in card_key.lower() or 
                    query_lower in card_str):
                    
                    results.append((memory_id, card))
        
        return results


def create_memory_manager(user_id: str, mode: MemoryMode = None) -> BaseMemoryManager:
    """
    Factory function to create appropriate memory manager
    
    Args:
        user_id: User identifier
        mode: Memory mode (defaults to config setting)
    
    Returns:
        Memory manager instance
    """
    mode = mode or Config.MEMORY_MODE
    
    if mode == MemoryMode.NOTES or mode == MemoryMode.ENHANCED_NOTES:
        # Both basic and enhanced notes use the same manager
        # The difference is in the prompts used by the agent
        return NotesMemoryManager(user_id)
    elif mode == MemoryMode.JSON_CARDS:
        return JSONMemoryManager(user_id)
    elif mode == MemoryMode.ADVANCED_JSON_CARDS:
        return AdvancedJSONMemoryManager(user_id)
    else:
        raise ValueError(f"Unknown memory mode: {mode}")


def ensure_memory_cleared(memory_manager: BaseMemoryManager, description: str = "memory") -> bool:
    """
    Ensures that all memory is cleared for a given memory manager.
    Used primarily for testing and evaluation to ensure clean state before each test case.
    
    Args:
        memory_manager: The memory manager to clear
        description: Description for logging (e.g., "agent memory", "processor memory")
        
    Returns:
        True if memory was successfully cleared, False otherwise
    """
    if not memory_manager:
        logger.warning(f"No memory manager provided for {description}")
        return False
    
    try:
        # Clear all memories
        if hasattr(memory_manager, 'clear_all_memories'):
            memory_manager.clear_all_memories()
        else:
            logger.warning(f"Memory manager for {description} doesn't support clear_all_memories()")
            return False
        
        # Verify memory is cleared by checking the context string
        context = memory_manager.get_context_string()
        is_cleared = "No previous memory" in context
        
        if is_cleared:
            logger.info(f"✅ {description} cleared successfully")
        else:
            logger.warning(f"⚠️ {description} may not be fully cleared. Context: {context[:100]}...")
        
        return is_cleared
        
    except Exception as e:
        logger.error(f"Error clearing {description}: {e}")
        return False
