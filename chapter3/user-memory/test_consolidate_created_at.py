import pytest
from memory_manager import NotesMemoryManager, MemoryNote

def test_consolidate_memories_preserves_earliest_created_at():
    """Verify deduplicating identical memory notes retains the earliest created_at timestamp."""
    mgr = NotesMemoryManager(user_id="test_created_at_user")
    mgr.notes = [
        MemoryNote(
            note_id="note_old",
            content="User prefers Python for AI development",
            session_id="s1",
            created_at="2026-01-01T10:00:00",
            updated_at="2026-01-01T10:00:00",
            tags=["pref"]
        ),
        MemoryNote(
            note_id="note_new",
            content="User prefers Python for AI development",
            session_id="s2",
            created_at="2026-01-10T15:00:00",
            updated_at="2026-01-10T15:00:00",
            tags=["language"]
        )
    ]

    report = mgr.consolidate_memories(resolve_conflicts=False)

    assert len(mgr.notes) == 1
    assert mgr.notes[0].created_at == "2026-01-01T10:00:00"
    assert mgr.notes[0].updated_at == "2026-01-10T15:00:00"
    assert mgr.notes[0].tags == ["language", "pref"]
