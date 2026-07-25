"""
Terminal Controller with integrated file operations.
Based on AWorld terminal-controller implementation.
Provides command execution with directory navigation and file editing.
"""
import os
import subprocess
import traceback
from pathlib import Path
from typing import Dict, Any

from config import Config


class TerminalController:
    """Terminal controller with directory navigation and file operations."""
    
    def __init__(self):
        self.workspace_dir = Path(Config.WORKSPACE_DIR).resolve()
        self.current_directory = self.workspace_dir
        self.command_history = []
        self.max_history = 100
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within workspace."""
        try:
            path.resolve().relative_to(self.workspace_dir)
            return True
        except ValueError:
            return False
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to current directory."""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.current_directory / path_obj
        return path_obj.resolve()
    
    async def execute_command(
        self,
        command: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a shell command in current directory.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with command output
        """
        try:
            # Add to history
            self.command_history.append(command)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.current_directory)
            )
            
            return {
                "success": result.returncode == 0,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "cwd": str(self.current_directory)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "command": command
            }
    
    async def get_current_directory(self) -> Dict[str, Any]:
        """
        Get the current working directory.
        
        Returns:
            Dictionary with current directory path
        """
        return {
            "success": True,
            "current_directory": str(self.current_directory),
            "workspace": str(self.workspace_dir)
        }
    
    async def change_directory(
        self,
        directory: str
    ) -> Dict[str, Any]:
        """
        Change the current working directory.
        
        Args:
            directory: Directory to change to
            
        Returns:
            Dictionary with new directory
        """
        try:
            new_dir = self._resolve_path(directory)
            
            if not self._is_safe_path(new_dir):
                return {
                    "success": False,
                    "error": f"Directory {directory} is outside workspace"
                }
            
            if not new_dir.exists():
                return {
                    "success": False,
                    "error": f"Directory {directory} does not exist"
                }
            
            if not new_dir.is_dir():
                return {
                    "success": False,
                    "error": f"{directory} is not a directory"
                }
            
            self.current_directory = new_dir
            
            return {
                "success": True,
                "current_directory": str(self.current_directory),
                "message": f"Changed to {directory}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to change directory: {str(e)}"
            }
    
    async def list_directory(
        self,
        directory: str = "."
    ) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            directory: Directory to list (relative to current)
            
        Returns:
            Dictionary with directory contents
        """
        try:
            dir_path = self._resolve_path(directory)
            
            if not self._is_safe_path(dir_path):
                return {
                    "success": False,
                    "error": f"Directory {directory} is outside workspace"
                }
            
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory {directory} does not exist"
                }
            
            contents = []
            for item in sorted(dir_path.iterdir()):
                contents.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": 0 if item.is_dir() else item.stat().st_size
                })
            
            return {
                "success": True,
                "directory": str(dir_path),
                "contents": contents,
                "count": len(contents)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list directory: {str(e)}"
            }
    
    async def read_file(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Read a file from current directory.
        
        Args:
            file_path: File path relative to current directory
            encoding: File encoding
            
        Returns:
            Dictionary with file content
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"File {file_path} is outside workspace"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            content = resolved_path.read_text(encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(resolved_path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }
    
    async def write_file(
        self,
        file_path: str,
        content: str,
        mode: str = "w"
    ) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            file_path: File path relative to current directory
            content: Content to write
            mode: Write mode ('w' for write, 'a' for append)
            
        Returns:
            Dictionary with write result
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"File {file_path} is outside workspace"
                }
            
            # Create parent directories if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            if mode == "a":
                with open(resolved_path, 'a', encoding='utf-8') as f:
                    f.write(content)
            else:
                resolved_path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "file_path": str(resolved_path),
                "bytes_written": len(content),
                "mode": mode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file: {str(e)}"
            }
    
    async def insert_file_content(
        self,
        file_path: str,
        content: str,
        line_number: int
    ) -> Dict[str, Any]:
        """
        Insert content at specific line in file.
        
        Args:
            file_path: File path
            content: Content to insert
            line_number: Line number to insert at (1-indexed)
            
        Returns:
            Dictionary with operation result
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"File {file_path} is outside workspace"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            # Read current content
            lines = resolved_path.read_text().splitlines()
            
            # Insert content
            if line_number < 1 or line_number > len(lines) + 1:
                return {
                    "success": False,
                    "error": f"Line number {line_number} out of range (1-{len(lines)+1})"
                }
            
            lines.insert(line_number - 1, content)
            
            # Write back
            resolved_path.write_text('\n'.join(lines) + '\n')
            
            return {
                "success": True,
                "file_path": str(resolved_path),
                "line_number": line_number,
                "total_lines": len(lines)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to insert content: {str(e)}"
            }
    
    async def delete_file_content(
        self,
        file_path: str,
        start_line: int,
        end_line: int
    ) -> Dict[str, Any]:
        """
        Delete lines from file.
        
        Args:
            file_path: File path
            start_line: Start line number (1-indexed, inclusive)
            end_line: End line number (1-indexed, inclusive)
            
        Returns:
            Dictionary with operation result
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"File {file_path} is outside workspace"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            # Read lines
            lines = resolved_path.read_text().splitlines()
            
            # Validate range
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return {
                    "success": False,
                    "error": f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)"
                }
            
            # Delete lines
            del lines[start_line - 1:end_line]
            
            # Write back
            resolved_path.write_text('\n'.join(lines) + '\n' if lines else '')
            
            return {
                "success": True,
                "file_path": str(resolved_path),
                "deleted_lines": end_line - start_line + 1,
                "remaining_lines": len(lines)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete content: {str(e)}"
            }
    
    async def update_file_content(
        self,
        file_path: str,
        line_number: int,
        new_content: str
    ) -> Dict[str, Any]:
        """
        Update a specific line in file.
        
        Args:
            file_path: File path
            line_number: Line number to update (1-indexed)
            new_content: New content for the line
            
        Returns:
            Dictionary with operation result
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not self._is_safe_path(resolved_path):
                return {
                    "success": False,
                    "error": f"File {file_path} is outside workspace"
                }
            
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            # Read lines
            lines = resolved_path.read_text().splitlines()
            
            if line_number < 1 or line_number > len(lines):
                return {
                    "success": False,
                    "error": f"Line number {line_number} out of range (1-{len(lines)})"
                }
            
            # Update line
            old_content = lines[line_number - 1]
            lines[line_number - 1] = new_content
            
            # Write back
            resolved_path.write_text('\n'.join(lines) + '\n')
            
            return {
                "success": True,
                "file_path": str(resolved_path),
                "line_number": line_number,
                "old_content": old_content,
                "new_content": new_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update content: {str(e)}"
            }
    
    async def get_command_history(
        self,
        count: int = 10
    ) -> Dict[str, Any]:
        """
        Get recent command history.
        
        Args:
            count: Number of recent commands
            
        Returns:
            Dictionary with command history
        """
        # count<=0 → []; history[-0:] would return the full list.
        if count <= 0 or not self.command_history:
            recent = []
        else:
            recent = self.command_history[-count:]
        
        return {
            "success": True,
            "history": recent,
            "count": len(recent),
            "total": len(self.command_history)
        }
