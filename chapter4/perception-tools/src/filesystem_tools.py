"""
File system tools: file reading, grep search, and text summarization.
"""
import json
import logging
import os
import re
import subprocess
import traceback
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
from mcp.types import TextContent

from base import ActionResponse, validate_file_path


load_dotenv()


async def read_file(
    file_path: str,
    encoding: str = "utf-8",
    max_length: int = 50000
) -> Union[str, TextContent]:
    """
    Read a file and return its contents.
    
    Args:
        file_path: Path to the file
        encoding: File encoding (default: utf-8)
        max_length: Maximum number of characters to return
        
    Returns:
        TextContent with file contents
    """
    try:
        path = validate_file_path(file_path)
        
        logging.info(f"📖 Reading file: {path}")
        
        with open(path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        if max_length < 0:
            max_length = len(content)
        truncated = len(content) > max_length
        if truncated:
            content = content[:max_length]
        
        result = {
            "file_path": str(path),
            "content": content,
            "size_bytes": path.stat().st_size,
            "truncated": truncated,
            "encoding": encoding
        }
        
        logging.info(f"✅ Successfully read file ({len(content)} characters)")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"file_path": str(path)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"File reading failed: {str(e)}"
        logging.error(f"File read error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "file_read_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def grep_search(
    pattern: str,
    directory: str,
    file_pattern: str = "*",
    recursive: bool = True,
    case_sensitive: bool = False,
    max_results: int = 100
) -> Union[str, TextContent]:
    """
    Search for a pattern in files using grep-like functionality.
    
    Args:
        pattern: Regular expression pattern to search for
        directory: Directory to search in
        file_pattern: File pattern to match (e.g., "*.py")
        recursive: Whether to search recursively
        case_sensitive: Whether search is case-sensitive
        max_results: Maximum number of results to return
        
    Returns:
        TextContent with search results
    """
    try:
        dir_path = Path(directory).expanduser().resolve()
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        logging.info(f"🔍 Searching for pattern '{pattern}' in {dir_path}")
        
        results = []
        if max_results <= 0:
            action_response = ActionResponse(
                success=True,
                message={
                    "pattern": pattern,
                    "results": results,
                    "total_found": 0,
                    "truncated": False,
                },
                metadata={
                    "directory": str(dir_path),
                    "file_pattern": file_pattern,
                    "recursive": recursive,
                },
            )
            return TextContent(
                type="text",
                text=json.dumps(action_response.model_dump()),
            )

        flags = re.IGNORECASE if not case_sensitive else 0
        regex = re.compile(pattern, flags)

        if recursive:
            files = dir_path.rglob(file_pattern)
        else:
            files = dir_path.glob(file_pattern)

        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                "file": str(file_path.relative_to(dir_path)),
                                "line_number": line_num,
                                "line": line.strip(),
                                "absolute_path": str(file_path)
                            })

                            if len(results) >= max_results:
                                break

                if len(results) >= max_results:
                    break

            except Exception as e:
                logging.warning(f"Error reading {file_path}: {e}")
                continue

        logging.info(f"✅ Found {len(results)} matches")

        action_response = ActionResponse(
            success=True,
            message={
                "pattern": pattern,
                "results": results,
                "total_found": len(results),
                "truncated": len(results) >= max_results
            },

            metadata={
                "directory": str(dir_path),
                "file_pattern": file_pattern,
                "recursive": recursive
            }
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Grep search failed: {str(e)}"
        logging.error(f"Grep error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "grep_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def summarize_text(
    text: str,
    max_length: int = 500,
    use_llm: bool = True
) -> Union[str, TextContent]:
    """
    Summarize long text content.
    
    Args:
        text: Text to summarize
        max_length: Target summary length
        use_llm: Whether to use LLM for summarization (if available)
        
    Returns:
        TextContent with summary
    """
    try:
        logging.info(f"📝 Summarizing text ({len(text)} characters)")
        
        if use_llm:
            # TODO: Integrate with LLM API for better summarization
            # For now, use simple extraction
            summary = "LLM summarization not yet implemented. Using simple extraction."
            method = "placeholder"
        else:
            # Simple extractive summarization: first N sentences
            sentences = re.split(r'[.!?]+', text)
            summary = ""
            for sentence in sentences:
                if len(summary) + len(sentence) > max_length:
                    break
                summary += sentence.strip() + ". "
            method = "extractive"
        
        if not summary or summary == "LLM summarization not yet implemented. Using simple extraction.":
            # Fallback: just truncate
            summary = text[:max_length] + "..." if len(text) > max_length else text
            method = "truncation"
        
        result = {
            "original_length": len(text),
            "summary_length": len(summary),
            "summary": summary,
            "method": method,
            "compression_ratio": len(summary) / len(text) if len(text) > 0 else 0
        }
        
        logging.info(f"✅ Generated summary ({len(summary)} characters)")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"method": method}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Text summarization failed: {str(e)}"
        logging.error(f"Summarization error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "summarization_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
