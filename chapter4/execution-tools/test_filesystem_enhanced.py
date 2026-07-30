"""
Real tests for enhanced filesystem tools.
These tests perform actual file operations to verify functionality.
"""
import asyncio
import json
import pytest
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from filesystem_enhanced import FilesystemEnhanced


@pytest.fixture(scope="function")
def fs(tmp_path, monkeypatch):
    """Create filesystem instance with temp workspace."""
    monkeypatch.setattr(Config, "WORKSPACE_DIR", tmp_path)
    return FilesystemEnhanced()


@pytest.fixture(scope="function")
def test_files(fs):
    """Create test files for testing."""
    # Create some test files
    try:
        (Config.WORKSPACE_DIR / "test1.txt").write_text("Hello World")
        (Config.WORKSPACE_DIR / "test2.txt").write_text("Python Testing\nLine 2\nLine 3")
        (Config.WORKSPACE_DIR / "data.json").write_text('{"key": "value"}')
        (Config.WORKSPACE_DIR / "subdir").mkdir()
        (Config.WORKSPACE_DIR / "subdir" / "nested.txt").write_text("Nested file")
    except Exception as e:
        print(f"Error creating test files: {e}")
    return fs


class TestReadOperations:
    """Tests for file reading operations."""
    
    @pytest.mark.asyncio
    async def test_read_text_file(self, test_files):
        """Test reading a text file."""
        result = await test_files.read_text_file("test1.txt")
        
        assert result["success"] is True
        assert result["content"] == "Hello World"
        assert result["file_size"] > 0
        assert result["lines"] == 1
        
        print("✅ Read text file successfully")
        print(f"   Content: {result['content']}")
    
    @pytest.mark.asyncio
    async def test_read_multiline_file(self, test_files):
        """Test reading multiline file."""
        result = await test_files.read_text_file("test2.txt")
        
        assert result["success"] is True
        assert result["lines"] == 3
        assert "Python Testing" in result["content"]
        
        print("✅ Read multiline file")
        print(f"   Lines: {result['lines']}")
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, fs):
        """Test reading non-existent file."""
        result = await fs.read_text_file("nonexistent.txt")
        
        assert result["success"] is False
        assert "does not exist" in result["error"]
        
        print("✅ Correctly handled nonexistent file")
    
    @pytest.mark.asyncio
    async def test_read_multiple_files(self, test_files):
        """Test reading multiple files at once."""
        result = await test_files.read_multiple_files([
            "test1.txt",
            "test2.txt",
            "data.json"
        ])
        
        assert result["success"] is True
        assert result["files_read"] == 3
        assert result["files_failed"] == 0
        assert "test1.txt" in result["results"]
        assert "test2.txt" in result["results"]
        
        print(f"✅ Read {result['files_read']} files")
        print(f"   Files: {', '.join(result['results'].keys())}")
    
    @pytest.mark.asyncio
    async def test_read_multiple_files_with_errors(self, test_files):
        """Test reading multiple files with some missing."""
        result = await test_files.read_multiple_files([
            "test1.txt",
            "nonexistent.txt",
            "test2.txt"
        ])
        
        assert result["success"] is True  # At least some succeeded
        assert result["files_read"] == 2
        assert result["files_failed"] == 1
        assert len(result["errors"]) == 1
        
        print(f"✅ Read {result['files_read']} files, {result['files_failed']} failed")


class TestListOperations:
    """Tests for directory listing operations."""
    
    @pytest.mark.asyncio
    async def test_list_directory_with_sizes(self, test_files):
        """Test listing directory with file sizes."""
        result = await test_files.list_directory_with_sizes(".")
        
        assert result["success"] is True
        assert result["total_items"] >= 4  # At least 3 files + 1 dir
        assert result["total_size"] > 0
        assert len(result["contents"]) >= 4
        
        # Check structure
        item = result["contents"][0]
        assert "name" in item
        assert "type" in item
        assert "size" in item
        assert "size_human" in item
        
        print(f"✅ Listed {result['total_items']} items")
        print(f"   Total size: {result['total_size_human']}")
    
    @pytest.mark.asyncio
    async def test_directory_tree(self, test_files):
        """Test generating directory tree."""
        result = await test_files.directory_tree(".", max_depth=3)
        
        assert result["success"] is True
        assert "tree" in result
        assert result["tree"]["type"] == "directory"
        assert "children" in result["tree"]
        assert len(result["tree"]["children"]) >= 4
        
        print(f"✅ Generated directory tree")
        print(f"   Root: {result['root']}")
        print(f"   Items: {result['tree']['count']}")
    
    @pytest.mark.asyncio
    async def test_directory_tree_depth_limit(self, test_files):
        """Test directory tree with depth limit."""
        # Create deeper structure
        (Config.WORKSPACE_DIR / "deep" / "level2" / "level3").mkdir(parents=True)
        
        result = await test_files.directory_tree(".", max_depth=2)
        
        assert result["success"] is True
        assert result["max_depth"] == 2
        
        print("✅ Directory tree respects depth limit")


class TestSearchOperations:
    """Tests for file search operations."""
    
    @pytest.mark.asyncio
    async def test_search_files_pattern(self, test_files):
        """Test searching files by pattern."""
        result = await test_files.search_files("*.txt", ".", recursive=True)
        
        assert result["success"] is True
        assert result["matches"] >= 3  # test1.txt, test2.txt, nested.txt
        assert result["pattern"] == "*.txt"
        
        # Check results structure
        if len(result["files"]) > 0:
            file_info = result["files"][0]
            assert "path" in file_info
            assert "size" in file_info
            assert "size_human" in file_info
        
        print(f"✅ Found {result['matches']} files matching *.txt")
    
    @pytest.mark.asyncio
    async def test_search_files_nonrecursive(self, test_files):
        """Test non-recursive search."""
        result = await test_files.search_files("*.txt", ".", recursive=False)
        
        assert result["success"] is True
        assert result["recursive"] is False
        # Should not find nested.txt
        paths = [f["path"] for f in result["files"]]
        assert not any("subdir" in p for p in paths)
        
        print(f"✅ Non-recursive search: {result['matches']} files")
    
    @pytest.mark.asyncio
    async def test_search_files_json(self, test_files):
        """Test searching for specific file type."""
        result = await test_files.search_files("*.json", ".", recursive=True)
        
        assert result["success"] is True
        assert result["matches"] >= 1
        
        print(f"✅ Found {result['matches']} JSON files")


class TestFileInfo:
    """Tests for file information retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_file_info(self, test_files):
        """Test getting file information."""
        result = await test_files.get_file_info("test2.txt")
        
        assert result["success"] is True
        info = result["file_info"]
        
        assert info["name"] == "test2.txt"
        assert info["extension"] == ".txt"
        assert info["is_file"] is True
        assert info["is_directory"] is False
        assert info["lines"] == 3
        assert info["size"] > 0
        
        print("✅ File info retrieved")
        print(f"   Name: {info['name']}")
        print(f"   Size: {info['size_human']}")
        print(f"   Lines: {info['lines']}")
    
    @pytest.mark.asyncio
    async def test_get_directory_info(self, test_files):
        """Test getting directory information."""
        result = await test_files.get_file_info("subdir")
        
        assert result["success"] is True
        info = result["file_info"]
        
        assert info["is_directory"] is True
        assert info["is_file"] is False
        
        print("✅ Directory info retrieved")


class TestMoveOperations:
    """Tests for move and copy operations."""
    
    @pytest.mark.asyncio
    async def test_move_file(self, test_files):
        """Test moving a file."""
        result = await test_files.move_file("test1.txt", "moved.txt")
        
        assert result["success"] is True
        assert Path(Config.WORKSPACE_DIR / "moved.txt").exists()
        assert not Path(Config.WORKSPACE_DIR / "test1.txt").exists()
        
        print("✅ File moved successfully")
        print(f"   From: test1.txt")
        print(f"   To: moved.txt")
    
    @pytest.mark.asyncio
    async def test_move_file_no_overwrite(self, test_files):
        """Test move without overwrite."""
        result = await test_files.move_file("test1.txt", "test2.txt", overwrite=False)
        
        assert result["success"] is False
        assert "already exists" in result["error"]
        
        print("✅ Correctly prevented overwrite")
    
    @pytest.mark.asyncio
    async def test_copy_file(self, test_files):
        """Test copying a file."""
        result = await test_files.copy_file("test1.txt", "copied.txt")
        
        assert result["success"] is True
        assert Path(Config.WORKSPACE_DIR / "copied.txt").exists()
        assert Path(Config.WORKSPACE_DIR / "test1.txt").exists()  # Original still exists
        
        print("✅ File copied successfully")
    
    @pytest.mark.asyncio
    async def test_copy_directory(self, test_files):
        """Test copying a directory."""
        result = await test_files.copy_file("subdir", "subdir_copy")
        
        assert result["success"] is True
        assert Path(Config.WORKSPACE_DIR / "subdir_copy").exists()
        assert Path(Config.WORKSPACE_DIR / "subdir_copy" / "nested.txt").exists()
        
        print("✅ Directory copied recursively")


class TestDeleteOperations:
    """Tests for delete operations."""
    
    @pytest.mark.asyncio
    async def test_delete_file(self, test_files):
        """Test deleting a file."""
        result = await test_files.delete_file("test1.txt")
        
        assert result["success"] is True
        assert not Path(Config.WORKSPACE_DIR / "test1.txt").exists()
        
        print("✅ File deleted")
    
    @pytest.mark.asyncio
    async def test_delete_directory_recursive(self, test_files):
        """Test deleting directory recursively."""
        result = await test_files.delete_file("subdir", recursive=True)
        
        assert result["success"] is True
        assert not Path(Config.WORKSPACE_DIR / "subdir").exists()
        
        print("✅ Directory deleted recursively")
    
    @pytest.mark.asyncio
    async def test_delete_directory_without_recursive(self, test_files):
        """Test that directory delete requires recursive flag."""
        result = await test_files.delete_file("subdir", recursive=False)
        
        assert result["success"] is False
        assert "recursive" in result["error"].lower()
        
        print("✅ Correctly required recursive flag")


class TestCreateOperations:
    """Tests for create operations."""
    
    @pytest.mark.asyncio
    async def test_create_directory(self, fs):
        """Test creating a directory."""
        result = await fs.create_directory("newdir")
        
        assert result["success"] is True
        assert Path(Config.WORKSPACE_DIR / "newdir").exists()
        
        print("✅ Directory created")
    
    @pytest.mark.asyncio
    async def test_create_nested_directory(self, fs):
        """Test creating nested directories."""
        result = await fs.create_directory("parent/child/grandchild", parents=True)
        
        assert result["success"] is True
        assert Path(Config.WORKSPACE_DIR / "parent" / "child" / "grandchild").exists()
        
        print("✅ Nested directories created")
    
    @pytest.mark.asyncio
    async def test_list_allowed_directories(self, fs):
        """Test listing allowed directories."""
        result = await fs.list_allowed_directories()
        
        assert result["success"] is True
        assert result["count"] >= 1
        assert len(result["allowed_directories"]) >= 1
        
        print(f"✅ Listed {result['count']} allowed directories")


# Run tests
if __name__ == "__main__":
    print("=" * 70)
    print("Running Enhanced Filesystem Tools Tests")
    print("=" * 70)
    print()
    
    pytest.main([__file__, "-v", "-s"])
