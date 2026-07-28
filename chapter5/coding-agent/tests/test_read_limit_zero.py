"""limit=0 on a nonempty file must not claim the file is empty."""


def test_limit_zero_on_nonempty_file(system_state, temp_dir):
    from tools.read_tool import ReadTool

    path = temp_dir / "lines.txt"
    path.write_text("a\nb\nc\n", encoding="utf-8")
    result = ReadTool(system_state).execute(
        {"file_path": str(path), "limit": 0}
    )
    data = result.data
    assert data["total_lines"] == 3
    assert data["content"] != "File is empty."
    assert "No lines in selected range" in data["content"]
    assert data["showing_lines"] == "1-0"


def test_truly_empty_file_still_warns(system_state, temp_dir):
    from tools.read_tool import ReadTool

    path = temp_dir / "empty.txt"
    path.write_text("", encoding="utf-8")
    result = ReadTool(system_state).execute({"file_path": str(path)})
    assert result.data["content"] == "File is empty."
    assert result.data["total_lines"] == 0


def test_positive_limit_still_returns_lines(system_state, temp_dir):
    from tools.read_tool import ReadTool

    path = temp_dir / "lines.txt"
    path.write_text("a\nb\nc\n", encoding="utf-8")
    result = ReadTool(system_state).execute(
        {"file_path": str(path), "limit": 1}
    )
    assert "     1|a" in result.data["content"]
    assert result.data["total_lines"] == 3
