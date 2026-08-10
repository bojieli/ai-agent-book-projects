"""
Enhanced filesystem tools based on AWorld filesystem-server.
Provides comprehensive file and directory operations with safety checks.
"""
import json
import os
import shutil
import traceback
from pathlib import Path
from typing import Dict, Any, List

from config import Config


class FilesystemEnhanced:
    """Enhanced filesystem operations with safety and validation."""
    
    def __init__(self):
        self.workspace_dir = Path(Config.WORKSPACE_DIR).resolve()
        self.allowed_directories = [self.workspace_dir]
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace."""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.workspace_dir / path_obj
        return path_obj.resolve()
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        try:
            resolved = path.resolve()
            for allowed in self.allowed_directories:
                try:
                    resolved.relative_to(allowed.resolve())
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    async def read_text_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
        max_size_mb: int = 10
    ) -> Dict[str, Any]:
        """
        Read a text file with size limits.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {file_path} is outside allowed directories"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            # Check file size
            file_size = resolved_path.stat().st_size
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                return {
                    "success": False,
                    "error": f"File too large: {file_size / (1024*1024):.2f}MB (max: {max_size_mb}MB)"
                }
            
            # Read file
            content = resolved_path.read_text(encoding=encoding)
            
            return {
                "success": True,
                "content": content,
                "file_path": str(resolved_path),
                "file_size": file_size,
                "encoding": encoding,
                "lines": len(content.splitlines())
            }
            
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"File is not a valid text file with encoding {encoding}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }
    
    async def read_multiple_files(
        self,
        file_paths: List[str],
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Read multiple files at once.
        
        Args:
            file_paths: List of file paths
            encoding: File encoding
            
        Returns:
            Dictionary with all file contents
        """
        results = {}
        errors = []
        
        for file_path in file_paths:
            result = await self.read_text_file(file_path, encoding)
            
            if result["success"]:
                results[file_path] = {
                    "content": result["content"],
                    "size": result["file_size"],
                    "lines": result["lines"]
                }
            else:
                errors.append({
                    "file": file_path,
                    "error": result["error"]
                })
        
        return {
            "success": len(results) > 0,
            "files_read": len(results),
            "files_failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    async def list_directory_with_sizes(
        self,
        directory_path: str = "."
    ) -> Dict[str, Any]:
        """
        List directory contents with file sizes.
        
        Args:
            directory_path: Path to directory
            
        Returns:
            Dictionary with directory contents and sizes
        """
        try:
            resolved_path = self._resolve_path(directory_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {directory_path} is outside allowed directories"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"Directory {directory_path} does not exist"
                }
            
            if not resolved_path.is_dir():
                return {
                    "success": False,
                    "error": f"{directory_path} is not a directory"
                }
            
            # List contents with sizes
            contents = []
            total_size = 0
            
            for item in sorted(resolved_path.iterdir()):
                try:
                    is_dir = item.is_dir()
                    size = 0 if is_dir else item.stat().st_size
                    total_size += size
                    
                    contents.append({
                        "name": item.name,
                        "type": "directory" if is_dir else "file",
                        "size": size,
                        "size_human": self._format_size(size),
                        "modified": item.stat().st_mtime
                    })
                except Exception as e:
                    contents.append({
                        "name": item.name,
                        "type": "unknown",
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "directory": str(resolved_path),
                "total_items": len(contents),
                "total_size": total_size,
                "total_size_human": self._format_size(total_size),
                "contents": contents
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list directory: {str(e)}"
            }
    
    async def directory_tree(
        self,
        directory_path: str = ".",
        max_depth: int = 3,
        show_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a tree structure of directory contents.
        
        Args:
            directory_path: Path to directory
            max_depth: Maximum depth to traverse
            show_hidden: Whether to show hidden files
            
        Returns:
            Dictionary with directory tree structure
        """
        try:
            resolved_path = self._resolve_path(directory_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {directory_path} is outside allowed directories"
                }
            
            def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
                """Recursively build tree structure."""
                if current_depth >= max_depth:
                    return {"name": path.name, "type": "directory", "truncated": True}
                
                if not path.is_dir():
                    return {
                        "name": path.name,
                        "type": "file",
                        "size": path.stat().st_size
                    }
                
                children = []
                try:
                    for item in sorted(path.iterdir()):
                        # Skip hidden files if needed
                        if not show_hidden and item.name.startswith('.'):
                            continue
                        
                        children.append(build_tree(item, current_depth + 1))
                except PermissionError:
                    return {
                        "name": path.name,
                        "type": "directory",
                        "error": "Permission denied"
                    }
                
                return {
                    "name": path.name,
                    "type": "directory",
                    "children": children,
                    "count": len(children)
                }
            
            tree = build_tree(resolved_path)
            
            return {
                "success": True,
                "root": str(resolved_path),
                "tree": tree,
                "max_depth": max_depth
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate directory tree: {str(e)}"
            }
    
    async def search_files(
        self,
        pattern: str,
        directory_path: str = ".",
        recursive: bool = True,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Search for files matching a pattern.
        
        Args:
            pattern: Glob pattern (e.g., "*.py", "test_*.txt")
            directory_path: Directory to search in
            recursive: Search recursively
            case_sensitive: Case-sensitive matching
            
        Returns:
            Dictionary with matching files
        """
        try:
            resolved_path = self._resolve_path(directory_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {directory_path} is outside allowed directories"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"Directory {directory_path} does not exist"
                }
            
            # Search for files
            if recursive:
                matches = list(resolved_path.rglob(pattern))
            else:
                matches = list(resolved_path.glob(pattern))
            
            # Filter to files only
            files = [m for m in matches if m.is_file()]
            
            results = []
            for file_path in sorted(files):
                try:
                    stat = file_path.stat()
                    results.append({
                        "path": str(file_path.relative_to(resolved_path)),
                        "absolute_path": str(file_path),
                        "size": stat.st_size,
                        "size_human": self._format_size(stat.st_size),
                        "modified": stat.st_mtime
                    })
                except Exception:
                    pass
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": str(resolved_path),
                "recursive": recursive,
                "matches": len(results),
                "files": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to search files: {str(e)}"
            }
    
    async def get_file_info(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {file_path} is outside allowed directories"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            stat = resolved_path.stat()
            
            info = {
                "path": str(resolved_path),
                "name": resolved_path.name,
                "extension": resolved_path.suffix,
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "is_file": resolved_path.is_file(),
                "is_directory": resolved_path.is_dir(),
                "is_symlink": resolved_path.is_symlink(),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            # Add parent directory info
            info["parent"] = str(resolved_path.parent)
            
            # For text files, add line count
            if resolved_path.is_file() and resolved_path.suffix in ['.txt', '.py', '.md', '.json', '.yaml', '.yml']:
                try:
                    content = resolved_path.read_text(encoding="utf-8")
                    info["lines"] = len(content.splitlines())
                    info["characters"] = len(content)
                except Exception:
                    pass
            
            return {
                "success": True,
                "file_info": info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get file info: {str(e)}"
            }
    
    async def move_file(
        self,
        source: str,
        destination: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Move or rename a file/directory.
        
        Args:
            source: Source path
            destination: Destination path
            overwrite: Whether to overwrite existing destination
            
        Returns:
            Dictionary with operation result
        """
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)
            
            if not self._is_safe_path(source_path) or not self._is_safe_path(dest_path):
                return {
                    "success": False,
                    "error": "Paths must be within allowed directories"
                }
            
            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Source {source} does not exist"
                }
            
            if dest_path.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"Destination {destination} already exists. Use overwrite=True to replace."
                }
            
            # Perform move
            if dest_path.exists():
                if dest_path.is_dir():
                    shutil.rmtree(dest_path)
                else:
                    dest_path.unlink()
            
            shutil.move(str(source_path), str(dest_path))
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path),
                "message": f"Moved {source} to {destination}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to move file: {str(e)}"
            }
    
    async def copy_file(
        self,
        source: str,
        destination: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Copy a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
            overwrite: Whether to overwrite existing destination
            
        Returns:
            Dictionary with operation result
        """
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)
            
            if not self._is_safe_path(source_path) or not self._is_safe_path(dest_path):
                return {
                    "success": False,
                    "error": "Paths must be within allowed directories"
                }
            
            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Source {source} does not exist"
                }
            
            if dest_path.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"Destination {destination} already exists"
                }
            
            # Perform copy
            if source_path.is_dir():
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(source_path, dest_path)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path),
                "message": f"Copied {source} to {destination}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to copy file: {str(e)}"
            }
    
    async def delete_file(
        self,
        file_path: str,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Args:
            file_path: Path to delete
            recursive: For directories, delete recursively
            
        Returns:
            Dictionary with operation result
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {file_path} is outside allowed directories"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"Path {file_path} does not exist"
                }
            
            # Delete
            if resolved_path.is_dir():
                if not recursive:
                    return {
                        "success": False,
                        "error": "Cannot delete directory without recursive=True"
                    }
                shutil.rmtree(resolved_path)
            else:
                resolved_path.unlink()
            
            return {
                "success": True,
                "deleted": str(resolved_path),
                "message": f"Deleted {file_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete: {str(e)}"
            }
    
    async def create_directory(
        self,
        directory_path: str,
        parents: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new directory.
        
        Args:
            directory_path: Path for new directory
            parents: Create parent directories if needed
            
        Returns:
            Dictionary with operation result
        """
        try:
            resolved_path = self._resolve_path(directory_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"Path {directory_path} is outside allowed directories"
                }
            
            if resolved_path.exists():
                return {
                    "success": False,
                    "error": f"Directory {directory_path} already exists"
                }
            
            # Create directory
            resolved_path.mkdir(parents=parents, exist_ok=False)
            
            return {
                "success": True,
                "directory": str(resolved_path),
                "message": f"Created directory {directory_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create directory: {str(e)}"
            }
    
    async def list_allowed_directories(self) -> Dict[str, Any]:
        """
        List directories that are accessible.
        
        Returns:
            Dictionary with allowed directories
        """
        return {
            "success": True,
            "allowed_directories": [str(d) for d in self.allowed_directories],
            "count": len(self.allowed_directories)
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
