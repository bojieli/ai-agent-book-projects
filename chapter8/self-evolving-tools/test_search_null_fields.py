from tool_manager import ToolLibrary
import tempfile
from pathlib import Path


def test_search_null_name_or_description():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = ToolLibrary(library_dir=Path(tmpdir))
        # Create a tool file manually with null description
        p = Path(tmpdir) / "null_desc.json"
        p.write_text('{"name": "null_desc", "description": null, "parameters": {}, "code": "def run(): pass"}')

        res = lib.search_tools("null")
        assert res["success"] is True
        assert res["count"] == 1
        assert res["tools"][0]["name"] == "null_desc"
def test_get_tool_non_dict_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = ToolLibrary(library_dir=Path(tmpdir))
        p = Path(tmpdir) / "bad_list.json"
        p.write_text('[1, 2, 3]')
        assert lib.get_tool("bad_list") is None
