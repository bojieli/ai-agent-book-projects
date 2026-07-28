"""
Read tool - File reading with support for text, images, PDFs, and notebooks
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseTool


class ReadTool(BaseTool):
    """Reads files from the local filesystem"""
    
    @property
    def name(self) -> str:
        return "Read"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read file contents
        
        - The file_path parameter must be an absolute path
        - By default, reads up to 2000 lines from the beginning
        - Can specify offset and limit for large files
        - Lines longer than 2000 characters are truncated
        - Results returned in cat -n format with line numbers starting at 1
        - Supports images, PDFs, Jupyter notebooks
        """
        file_path = Path(params["file_path"]).expanduser().resolve()
        offset = params.get("offset")
        if offset is None:
            offset = 0
        limit = params.get("limit")
        if limit is None:
            limit = 2000
        
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not file_path.is_file():
            return {"error": f"Not a file: {file_path}"}
        
        # Check file type
        suffix = file_path.suffix.lower()
        
        # Handle special file types
        if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            return self._read_image(file_path)
        elif suffix == '.pdf':
            return self._read_pdf(file_path)
        elif suffix == '.ipynb':
            return self._read_notebook(file_path)
        else:
            return self._read_text(file_path, offset, limit)
    
    def _read_text(self, file_path: Path, offset: int, limit: int) -> Dict[str, Any]:
        """Read text file"""
        try:
            # Sniff for binary content first: NUL bytes never appear in text,
            # and control bytes like \x00-\x05 are valid UTF-8, so a decode
            # error alone is not a reliable binary signal.
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
            if b'\x00' in sample:
                return {"error": "File appears to be binary. Cannot read as text."}

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply offset and limit
            total_lines = len(lines)
            if offset < 0:
                offset = 0
            if limit < 0:
                selected_lines = lines[offset:]
            else:
                selected_lines = lines[offset:offset + limit] if offset or limit < total_lines else lines
            
            # Format with line numbers (1-indexed)
            formatted_lines = []
            for i, line in enumerate(selected_lines, start=offset + 1):
                # Truncate long lines
                line_content = line.rstrip()
                if len(line_content) > 2000:
                    line_content = line_content[:2000] + "... (line truncated)"
                formatted_lines.append(f"{i:6d}|{line_content}")
            
            content = "\n".join(formatted_lines)

            # tools.json: empty-file warning only when the file has no contents.
            if total_lines == 0:
                content = "File is empty."
            elif not selected_lines:
                content = "No lines in selected range."

            return {
                "file_path": str(file_path),
                "total_lines": total_lines,
                "showing_lines": f"{offset + 1}-{offset + len(selected_lines)}",
                "content": content
            }
            
        except UnicodeDecodeError:
            return {"error": "File appears to be binary. Cannot read as text."}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}
    
    def _read_image(self, file_path: Path) -> Dict[str, Any]:
        """Read image file"""
        # For now, just return metadata since we can't display images in text
        try:
            size = file_path.stat().st_size
            return {
                "file_path": str(file_path),
                "file_type": "image",
                "format": file_path.suffix[1:].upper(),
                "size_bytes": size,
                "note": "Image file detected. Full visual analysis requires multimodal LLM support."
            }
        except Exception as e:
            return {"error": f"Error reading image: {str(e)}"}
    
    def _read_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Read PDF file"""
        # For now, return basic info
        # Full PDF support would require PyPDF2 or similar
        try:
            size = file_path.stat().st_size
            return {
                "file_path": str(file_path),
                "file_type": "pdf",
                "size_bytes": size,
                "note": "PDF file detected. Full text extraction requires PyPDF2 library. Install with: pip install PyPDF2"
            }
        except Exception as e:
            return {"error": f"Error reading PDF: {str(e)}"}
    
    def _read_notebook(self, file_path: Path) -> Dict[str, Any]:
        """Read Jupyter notebook"""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            # Extract cells
            cells = notebook.get('cells', [])
            
            # Format output
            output_lines = []
            output_lines.append(f"Jupyter Notebook: {file_path.name}")
            output_lines.append("=" * 60)
            
            for i, cell in enumerate(cells):
                cell_type = cell.get('cell_type', 'unknown')
                source = cell.get('source', [])
                
                # Convert source to string
                if isinstance(source, list):
                    source_text = ''.join(source)
                else:
                    source_text = source
                
                output_lines.append(f"\n[Cell {i + 1}] Type: {cell_type}")
                output_lines.append("-" * 60)
                output_lines.append(source_text)
                
                # Show outputs for code cells
                if cell_type == 'code':
                    outputs = cell.get('outputs', [])
                    if outputs:
                        output_lines.append("\nOutput:")
                        for output in outputs:
                            output_type = output.get('output_type', '')
                            if output_type == 'stream':
                                text = ''.join(output.get('text', []))
                                output_lines.append(text)
                            elif output_type == 'execute_result' or output_type == 'display_data':
                                data = output.get('data', {})
                                if 'text/plain' in data:
                                    text = ''.join(data['text/plain'])
                                    output_lines.append(text)
            
            content = '\n'.join(output_lines)
            
            return {
                "file_path": str(file_path),
                "file_type": "jupyter_notebook",
                "total_cells": len(cells),
                "content": content
            }
            
        except json.JSONDecodeError:
            return {"error": "Invalid Jupyter notebook format"}
        except Exception as e:
            return {"error": f"Error reading notebook: {str(e)}"}

