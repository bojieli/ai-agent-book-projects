"""head_limit=0 must return zero results (like `head -0`), not unlimited."""


def test_head_limit_zero_files_with_matches(system_state, sample_files):
    from tools.grep_tool import GrepTool

    result = GrepTool(system_state).execute(
        {
            "pattern": "ERROR",
            "path": str(sample_files["text_file1"].parent),
            "head_limit": 0,
            "output_mode": "files_with_matches",
        }
    )
    assert result.data["matches"] == 0
    assert result.data["output"] == "No matches found."


def test_head_limit_one_still_caps(system_state, sample_files):
    from tools.grep_tool import GrepTool

    result = GrepTool(system_state).execute(
        {
            "pattern": "ERROR",
            "path": str(sample_files["text_file1"].parent),
            "head_limit": 1,
            "output_mode": "files_with_matches",
        }
    )
    assert result.data["matches"] == 1


def test_omitted_head_limit_still_unlimited(system_state, sample_files):
    from tools.grep_tool import GrepTool

    result = GrepTool(system_state).execute(
        {
            "pattern": "test",
            "path": str(sample_files["text_file1"].parent),
            "output_mode": "files_with_matches",
        }
    )
    assert result.data["matches"] >= 1
