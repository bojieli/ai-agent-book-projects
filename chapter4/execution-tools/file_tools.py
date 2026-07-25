"""File system tools with safety mechanisms."""

import itertools
import os
from pathlib import Path
from typing import Dict, Any
from llm_helper import LLMHelper
from config import Config


class FileTools:
    """File system tools with verification and safety checks."""
    
    def __init__(self, llm_helper: LLMHelper):
        """Initialize file tools with LLM helper."""
        self.llm_helper = llm_helper
        self.workspace_dir = Config.WORKSPACE_DIR
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace."""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.workspace_dir / path_obj
        return path_obj.resolve()
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within workspace."""
        try:
            path.resolve().relative_to(self.workspace_dir.resolve())
            return True
        except ValueError:
            return False
    
    async def write_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Write content to a file with safety checks.
        
        Args:
            path: File path (relative to workspace or absolute)
            content: Content to write
            overwrite: Whether to overwrite existing files
            
        Returns:
            Result dictionary with status and details
        """
        resolved_path = self._resolve_path(path)
        
        # Safety check: ensure path is within workspace
        if not self._is_safe_path(resolved_path):
            return {
                "success": False,
                "error": f"Path {path} is outside workspace directory"
            }
        
        # Check if file exists and overwrite is not allowed
        if resolved_path.exists() and not overwrite:
            # Request approval for overwriting
            if Config.REQUIRE_APPROVAL_FOR_DANGEROUS_OPS:
                approved, reason = self.llm_helper.request_approval(
                    "file_overwrite",
                    {
                        "path": str(resolved_path),
                        "existing_size": resolved_path.stat().st_size,
                        "new_content_size": len(content)
                    }
                )
                
                if not approved:
                    return {
                        "success": False,
                        "error": f"Overwrite not approved: {reason}"
                    }
        
        # Verify code syntax if it's a code file
        if Config.AUTO_VERIFY_CODE and resolved_path.suffix in ['.py', '.js', '.ts']:
            language = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript'}[resolved_path.suffix]
            is_valid, error_msg = self.llm_helper.verify_code_syntax(content, language)
            
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Syntax validation failed: {error_msg}",
                    "verification": "failed"
                }
        
        # Write the file
        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path.write_text(content)
            
            return {
                "success": True,
                "path": str(resolved_path),
                "bytes_written": len(content),
                "verification": "passed" if Config.AUTO_VERIFY_CODE else "skipped"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file: {str(e)}"
            }
    
    async def edit_file(
        self,
        path: str,
        search: str,
        replace: str
    ) -> Dict[str, Any]:
        """
        Edit a file by searching and replacing content.
        
        Args:
            path: File path
            search: Text to search for
            replace: Replacement text
            
        Returns:
            Result dictionary with status and details
        """
        resolved_path = self._resolve_path(path)
        
        # Safety check
        if not self._is_safe_path(resolved_path):
            return {
                "success": False,
                "error": f"Path {path} is outside workspace directory"
            }
        
        # Check if file exists
        if not resolved_path.exists():
            return {
                "success": False,
                "error": f"File {path} does not exist"
            }
        
        # Read current content
        try:
            current_content = resolved_path.read_text()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }

        # Empty search matches everywhere; reject instead of inserting at start.
        if search == "":
            return {
                "success": False,
                "error": "Search text cannot be empty"
            }
        
        # Check if search text exists
        if search not in current_content:
            return {
                "success": False,
                "error": f"Search text not found in file"
            }
        
        # Perform replacement
        new_content = current_content.replace(search, replace, 1)
        
        # Generate diff preview
        diff_preview = self._generate_diff(current_content, new_content)
        
        # Verify new content if it's code
        if Config.AUTO_VERIFY_CODE and resolved_path.suffix in ['.py', '.js', '.ts']:
            language = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript'}[resolved_path.suffix]
            is_valid, error_msg = self.llm_helper.verify_code_syntax(new_content, language)
            
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Syntax validation failed after edit: {error_msg}",
                    "diff_preview": diff_preview
                }
        
        # Write the modified content
        try:
            resolved_path.write_text(new_content)
            
            return {
                "success": True,
                "path": str(resolved_path),
                "diff_preview": diff_preview,
                "verification": "passed" if Config.AUTO_VERIFY_CODE else "skipped"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file: {str(e)}"
            }
    
    def _generate_diff(self, old_content: str, new_content: str) -> str:
        """Generate a simple diff preview."""
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        diff_lines = []
        for i, (old, new) in enumerate(itertools.zip_longest(old_lines, new_lines, fillvalue=''), 1):
            if old != new:
                diff_lines.append(f"Line {i}:")
                diff_lines.append(f"  - {old}")
                diff_lines.append(f"  + {new}")
        
        return '\n'.join(diff_lines[:20])  # Limit to 20 lines
