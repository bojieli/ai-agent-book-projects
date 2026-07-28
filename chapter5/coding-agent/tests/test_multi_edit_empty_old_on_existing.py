"""Empty old_string on an existing file must not wipe contents (match Edit)."""

from tools.edit_tool import EditTool
from tools.multi_edit_tool import MultiEditTool


def test_empty_old_string_on_existing_file_rejected(system_state, temp_dir):
    path = temp_dir / "keep.txt"
    path.write_text("hello world", encoding="utf-8")

    result = MultiEditTool(system_state).execute(
        {
            "file_path": str(path),
            "edits": [{"old_string": "", "new_string": "Y"}],
        }
    )
    assert result.data.get("error") == "old_string cannot be empty"
    assert path.read_text(encoding="utf-8") == "hello world"


def test_empty_old_string_matches_edit_rejection(system_state, temp_dir):
    path = temp_dir / "keep.txt"
    path.write_text("hello world", encoding="utf-8")
    edit = EditTool(system_state).execute(
        {"file_path": str(path), "old_string": "", "new_string": "Y"}
    )
    multi = MultiEditTool(system_state).execute(
        {
            "file_path": str(path),
            "edits": [{"old_string": "", "new_string": "Y"}],
        }
    )
    assert edit.data.get("error") == multi.data.get("error") == "old_string cannot be empty"
    assert path.read_text(encoding="utf-8") == "hello world"


def test_create_new_file_with_empty_old_string_still_works(system_state, temp_dir):
    path = temp_dir / "brand_new.txt"
    assert not path.exists()
    result = MultiEditTool(system_state).execute(
        {
            "file_path": str(path),
            "edits": [{"old_string": "", "new_string": "created"}],
        }
    )
    assert "error" not in result.data
    assert path.read_text(encoding="utf-8") == "created"


def test_empty_old_string_later_edit_rejected(system_state, temp_dir):
    path = temp_dir / "keep.txt"
    path.write_text("hello", encoding="utf-8")
    result = MultiEditTool(system_state).execute(
        {
            "file_path": str(path),
            "edits": [
                {"old_string": "hello", "new_string": "hello"},
                {"old_string": "", "new_string": "X", "replace_all": True},
            ],
        }
    )
    assert result.data.get("error") == "old_string cannot be empty"
    assert path.read_text(encoding="utf-8") == "hello"
