"""
Grep tool - Pure Python implementation without rg/grep dependencies
Implements full regex search across files with all features from tools.json
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import fnmatch
from .base import BaseTool


class GrepTool(BaseTool):
    """Pure Python grep implementation"""
    
    @property
    def name(self) -> str:
        return "Grep"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for patterns in files using pure Python regex
        
        Supports:
        - Full regex syntax
        - Case insensitive search (-i)
        - Context lines (-A, -B, -C)
        - Line numbers (-n)
        - Multiline mode
        - Glob filtering
        - File type filtering
        - Output modes: content, files_with_matches, count
        - Head limit
        """
        pattern = params["pattern"]
        path = params.get("path", ".")
        if path is None:
            path = "."
        glob_pattern = params.get("glob")
        output_mode = params.get("output_mode", "files_with_matches")
        case_insensitive = params.get("-i", False)
        context_before = params.get("-B")
        if context_before is None:
            context_before = 0
        context_after = params.get("-A")
        if context_after is None:
            context_after = 0
        context_around = params.get("-C")
        if context_around is None:
            context_around = 0
        show_line_numbers = params.get("-n", False)
        multiline = params.get("multiline", False)
        head_limit = params.get("head_limit")
        if head_limit is not None and head_limit < 0:
            head_limit = None
        # head_limit=0 means zero results (like `head -0`), not unlimited.
        if head_limit == 0:
            return {
                "pattern": pattern,
                "output": "No matches found.",
                "matches": 0,
            }
        file_type = params.get("type")
        
        # Determine context
        if context_around:
            context_before = context_around
            context_after = context_around
        context_before = max(0, int(context_before))
        context_after = max(0, int(context_after))
        
        # Compile regex
        regex_flags = re.MULTILINE if multiline else 0
        if case_insensitive:
            regex_flags |= re.IGNORECASE
        if multiline:
            regex_flags |= re.DOTALL
        
        try:
            regex = re.compile(pattern, regex_flags)
        except re.error as e:
            return {"error": f"Invalid regex pattern: {str(e)}"}
        
        # Resolve search path
        search_path = Path(path).expanduser().resolve()
        if not search_path.exists():
            return {"error": f"Path not found: {search_path}"}
        
        # Get files to search
        files_to_search = self._get_files_to_search(
            search_path, glob_pattern, file_type
        )
        
        if not files_to_search:
            return {
                "pattern": pattern,
                "output": "No files found matching criteria.",
                "matches": 0
            }
        
        # Search files
        if output_mode == "files_with_matches":
            results = self._search_files_with_matches(files_to_search, regex, head_limit)
        elif output_mode == "count":
            results = self._search_count(files_to_search, regex, head_limit)
        else:  # content
            results = self._search_content(
                files_to_search, regex,
                context_before, context_after,
                show_line_numbers, head_limit
            )
        
        return {
            "pattern": pattern,
            "output": results["output"],
            "matches": results["matches"]
        }
    
    def _get_files_to_search(
        self, search_path: Path, glob_pattern: Optional[str], file_type: Optional[str]
    ) -> List[Path]:
        """Get list of files to search"""
        files = []
        
        # Define file type extensions
        type_extensions = {
            "py": ["*.py"],
            "python": ["*.py"],
            "js": ["*.js", "*.jsx"],
            "javascript": ["*.js", "*.jsx"],
            "ts": ["*.ts", "*.tsx"],
            "typescript": ["*.ts", "*.tsx"],
            "java": ["*.java"],
            "go": ["*.go"],
            "rust": ["*.rs"],
            "cpp": ["*.cpp", "*.cc", "*.cxx", "*.h", "*.hpp"],
            "c": ["*.c", "*.h"],
            "ruby": ["*.rb"],
            "php": ["*.php"],
            "html": ["*.html", "*.htm"],
            "css": ["*.css"],
            "json": ["*.json"],
            "yaml": ["*.yaml", "*.yml"],
            "md": ["*.md"],
            "markdown": ["*.md"],
            "txt": ["*.txt"],
        }
        
        if search_path.is_file():
            # Single file
            files = [search_path]
        else:
            # Directory - walk recursively
            for root, dirs, filenames in os.walk(search_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    # Skip hidden files
                    if filename.startswith('.'):
                        continue
                    
                    file_path = Path(root) / filename
                    
                    # Check file type filter
                    if file_type:
                        extensions = type_extensions.get(file_type, [])
                        if not any(fnmatch.fnmatch(filename, ext) for ext in extensions):
                            continue
                    
                    # Check glob filter
                    if glob_pattern:
                        # Convert glob to relative path for matching
                        try:
                            rel_path = file_path.relative_to(search_path)
                            if not fnmatch.fnmatch(str(rel_path), glob_pattern):
                                continue
                        except ValueError:
                            continue
                    
                    files.append(file_path)
        
        return files
    
    def _search_files_with_matches(
        self, files: List[Path], regex: re.Pattern, head_limit: Optional[int]
    ) -> Dict[str, Any]:
        """Search and return files that have matches"""
        matching_files = []
        
        for file_path in files:
            try:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for match
                if regex.search(content):
                    matching_files.append(str(file_path))
                    
                    # Check head limit (0 means zero results; do not treat as unlimited)
                    if head_limit is not None and len(matching_files) >= head_limit:
                        break
                        
            except (IOError, OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue
        
        if not matching_files:
            output = "No matches found."
        else:
            output = "\n".join(matching_files)
        
        return {
            "output": output,
            "matches": len(matching_files)
        }
    
    def _search_count(
        self, files: List[Path], regex: re.Pattern, head_limit: Optional[int]
    ) -> Dict[str, Any]:
        """Count matches per file"""
        results = []
        total_matches = 0
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count matches
                matches = len(regex.findall(content))
                if matches > 0:
                    results.append(f"{file_path}:{matches}")
                    total_matches += matches
                    
                    if head_limit is not None and len(results) >= head_limit:
                        break
                        
            except (IOError, OSError, UnicodeDecodeError):
                continue
        
        if not results:
            output = "No matches found."
        else:
            output = "\n".join(results)
        
        return {
            "output": output,
            "matches": total_matches
        }
    
    def _search_content(
        self, files: List[Path], regex: re.Pattern,
        context_before: int, context_after: int,
        show_line_numbers: bool, head_limit: Optional[int]
    ) -> Dict[str, Any]:
        """Search and return matching lines with context"""
        output_lines = []
        total_matches = 0
        lines_added = 0
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Find matching lines
                matching_line_numbers = []
                for i, line in enumerate(lines):
                    if regex.search(line):
                        matching_line_numbers.append(i)
                
                if not matching_line_numbers:
                    continue
                
                # Add file header
                output_lines.append(f"\n{file_path}")
                lines_added += 1
                
                # Process each match with context
                lines_to_show = set()
                for line_num in matching_line_numbers:
                    # Add context lines
                    start = max(0, line_num - context_before)
                    end = min(len(lines), line_num + context_after + 1)
                    lines_to_show.update(range(start, end))
                
                # Output lines in order
                prev_line = -2
                for line_num in sorted(lines_to_show):
                    # Add separator for gaps
                    if line_num > prev_line + 1:
                        output_lines.append("--")
                        lines_added += 1
                    
                    line = lines[line_num].rstrip()
                    is_match = line_num in matching_line_numbers
                    
                    # Format line
                    if show_line_numbers:
                        prefix = f"{line_num + 1}:"
                    else:
                        prefix = ""
                    
                    # Use : for match lines, - for context
                    separator = ":" if is_match else "-"
                    formatted = f"{prefix}{separator}{line}" if prefix else f"{separator}{line}"
                    
                    output_lines.append(formatted)
                    lines_added += 1
                    
                    if is_match:
                        total_matches += 1
                    
                    prev_line = line_num
                    
                    # Check head limit (0 means zero results; do not treat as unlimited)
                    if head_limit is not None and lines_added >= head_limit:
                        break
                
                if head_limit is not None and lines_added >= head_limit:
                    break
                    
            except (IOError, OSError, UnicodeDecodeError):
                continue
        
        if not output_lines:
            output = "No matches found."
        else:
            output = "\n".join(output_lines)
        
        return {
            "output": output,
            "matches": total_matches
        }

