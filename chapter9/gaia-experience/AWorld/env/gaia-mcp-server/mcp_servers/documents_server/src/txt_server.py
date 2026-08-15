import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, Union, Literal

import chardet
from dotenv import load_dotenv
from pydantic.fields import FieldInfo

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field

from base import (
    ActionResponse,
    _validate_file_path,
    get_file_from_source,
    DocumentMetadata,
    get_mime_type,
)

load_dotenv()

workspace = Path.home()
_media_output_dir = workspace / "extracted_media"
_media_output_dir.mkdir(exist_ok=True, parents=True)

supported_extensions: set = {
    ".txt",
    ".text",
    ".log",
    ".md",
    ".markdown",
    ".rst",
    ".rtf",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".properties",
    ".sql",
    ".py",
    ".js",
    ".html",
    ".htm",
    ".css",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".php",
    ".rb",
    ".go",
    ".rs",
    ".sh",
    ".bat",
    ".ps1",
    ".r",
    ".m",
    ".swift",
    ".kt",
    ".scala",
    ".pl",
    ".lua",
    ".vim",
    ".tex",
    ".bib",
}


mcp = FastMCP(
    "documents-txt-server",
    instructions="""
MCP service for text document content extraction.

    Supports extraction from TXT and other raw text format files.
    Provides LLM-friendly text output with structured metadata and encoding detection.
    Handles various text encodings and provides comprehensive file analysis.
""",
)


@mcp.tool(
    description="""
Extract content from text documents with encoding detection and analysis.

        This tool provides comprehensive text document content extraction with support for:
        - Various text file formats (TXT, MD, CSV, JSON, XML, source code, etc.)
        - Automatic encoding detection with fallback options
        - Content type detection and analysis
        - Comprehensive text statistics
        - LLM-optimized output formatting
        - Binary file detection and handling
"""
)
async def extract_text_content(
    file_path: str = Field(
        description="Path to the text document file to extract content from"
    ),
    output_format: Literal["markdown", "json", "html", "text"] = Field(
        default="markdown", description="Output format: 'markdown'"
    ),
    encoding: str | None = Field(
        default=None, description="Specific encoding to use (None for auto-detection)"
    ),
    max_content_length: int | None = Field(
        default=None,
        description="Maximum length of content to include in output (None for no limit)",
    ),
) -> Union[str, TextContent]:
    try:
        # Handle FieldInfo objects
        if isinstance(file_path, FieldInfo):
            file_path = file_path.default
        if isinstance(output_format, FieldInfo):
            output_format = output_format.default
        if isinstance(encoding, FieldInfo):
            encoding = encoding.default
        if isinstance(max_content_length, FieldInfo):
            max_content_length = max_content_length.default

        # Validate input file
        file_path: Path = _validate_file_path(file_path)
        logging.info(f"Processing text document: {file_path.name}")

        # Extract content from text file
        extraction_result = _extract_text_content(file_path, encoding)

        # Check if file appears to be binary
        if extraction_result["encoding_info"]["is_binary"]:
            logging.info("Warning: File appears to contain binary data")

        # Format content for LLM consumption
        formatted_content = _format_content_for_llm(
            extraction_result, output_format, max_content_length
        )

        # Prepare metadata
        file_stats = file_path.stat()

        # Create text-specific metadata
        text_metadata = {
            "content_type": extraction_result["content_type"],
            "encoding_info": extraction_result["encoding_info"],
            "text_statistics": extraction_result["statistics"],
            "used_encoding": extraction_result["used_encoding"],
            "encoding_fallback": extraction_result.get("encoding_fallback", False),
            "content_truncated": max_content_length
            and len(extraction_result["content"]) > max_content_length,
            "original_content_length": extraction_result["statistics"][
                "character_count"
            ],
        }

        document_metadata = DocumentMetadata(
            file_name=file_path.name,
            file_size=file_stats.st_size,
            file_type=file_path.suffix.lower() or ".txt",
            absolute_path=str(file_path.absolute()),
            page_count=extraction_result["statistics"][
                "line_count"
            ],  # Use line count as "page" count
            processing_time=extraction_result["processing_time"],
            extracted_images=[],  # Text files don't contain images
            extracted_media=[],  # Text files don't contain media
            output_format=output_format,
            llm_enhanced=False,
            ocr_applied=False,
        )

        # Combine standard and text-specific metadata
        combined_metadata = document_metadata.model_dump()
        combined_metadata.update(text_metadata)

        logging.info(
            f"Successfully extracted content from {file_path.name} -({extraction_result['statistics']['character_count']:,} characters,{extraction_result['statistics']['line_count']:,} lines,encoding: {extraction_result['used_encoding']})"
        )

        action_response = ActionResponse(
            success=True, message=formatted_content, metadata=combined_metadata
        )
        output_dict = {"artifact_type": "MARKDOWN", "artifact_data": formatted_content}
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"File not found: {str(e)}",
            metadata={"error_type": "file_not_found"},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )
    except ValueError as e:
        logging.error(f"Invalid input: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"Invalid input: {str(e)}",
            metadata={"error_type": "invalid_input"},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )
    except Exception as e:
        logging.error(f"Text extraction failed: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"Text extraction failed: {str(e)}",
            metadata={"error_type": "extraction_error"},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
List all supported text formats for extraction.
"""
)
async def list_supported_formats() -> Union[str, TextContent]:
    supported_formats = {
        "TXT": "Plain text files (.txt, .text)",
        "Markdown": "Markdown documents (.md, .markdown)",
        "CSV/TSV": "Comma/Tab separated values (.csv, .tsv)",
        "JSON": "JSON data files (.json)",
        "XML": "XML documents (.xml)",
        "YAML": "YAML configuration files (.yaml, .yml)",
        "Source Code": "Programming language files (.py, .js, .html, .css, etc.)",
        "Configuration": "Config files (.ini, .cfg, .conf, .properties)",
        "Logs": "Log files (.log)",
        "Documentation": "Documentation files (.rst, .rtf)",
        "Scripts": "Script files (.sh, .bat, .ps1)",
        "Other Text": "Any file with text MIME type or detectable text content",
    }

    format_list = "\n".join(
        [
            f"**{format_name}**: {description}"
            for format_name, description in supported_formats.items()
        ]
    )

    action_response = ActionResponse(
        success=True,
        message=f"Supported text formats:\n\n{format_list}\n\n"
        "**Note:** The service automatically detects encoding and "
        "can handle files without standard extensions if they contain readable text.",
        metadata={
            "supported_formats": list(supported_formats.keys()),
            "total_formats": len(supported_formats),
            "encoding_detection": True,
            "binary_detection": True,
        },
    )
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": {}},  # Pass as additional fields
    )


def _validate_file_path(file_path: str) -> Path:
    """Validate and resolve file path.

    Args:
        file_path: Path to the text document file

    Returns:
        Resolved Path object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file type is not supported
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = path.expanduser().resolve()
        #path = workspace / path

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Also check MIME type for files without extensions or unknown extensions
    mime_type = get_mime_type(str(path), default_mime="text/plain")
    is_text_mime = mime_type and mime_type.startswith("text/")

    if path.suffix.lower() not in supported_extensions and not is_text_mime:
        # Try to detect if it's a text file by reading a small sample
        try:
            with open(path, "rb") as f:
                sample = f.read(1024)
                # Check if the sample contains mostly printable characters
                if _is_likely_text(sample):
                    logging.info(
                        f"Detected text file without standard extension: {path.suffix}"
                    )
                else:
                    raise ValueError(
                        f"Unsupported file type: {path.suffix}. "
                        f"Supported types: {', '.join(sorted(supported_extensions))} or text MIME types"
                    )
        except Exception as e:
            raise ValueError(
                f"Cannot determine if file is text: {str(e)}. "
                f"Supported types: {', '.join(sorted(supported_extensions))}"
            ) from e

    return path


def _is_likely_text(data: bytes) -> bool:
    """Check if binary data is likely to be text.

    Args:
        data: Binary data sample

    Returns:
        True if data appears to be text
    """
    if not data:
        return True

    # Check for null bytes (common in binary files)
    if b"\x00" in data:
        return False

    # Try to decode as text
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        pass

    # Check if most bytes are printable ASCII
    printable_count = sum(
        1 for byte in data if 32 <= byte <= 126 or byte in [9, 10, 13]
    )
    return printable_count / len(data) > 0.7


def _detect_encoding(file_path: Path) -> dict[str, Any]:
    """Detect file encoding and other characteristics.

    Args:
        file_path: Path to the text file

    Returns:
        Dictionary containing encoding information
    """
    encoding_info = {
        "detected_encoding": None,
        "confidence": 0.0,
        "bom_detected": False,
        "line_endings": None,
        "is_binary": False,
    }

    try:
        # Read file in binary mode for encoding detection
        with open(file_path, "rb") as f:
            raw_data = f.read()

        if not raw_data:
            encoding_info["detected_encoding"] = "utf-8"
            encoding_info["confidence"] = 1.0
            return encoding_info

        # Check for BOM (Byte Order Mark)
        if raw_data.startswith(b"\xef\xbb\xbf"):
            encoding_info["bom_detected"] = True
            encoding_info["detected_encoding"] = "utf-8-sig"
            encoding_info["confidence"] = 1.0
        elif raw_data.startswith(b"\xff\xfe"):
            encoding_info["bom_detected"] = True
            encoding_info["detected_encoding"] = "utf-16-le"
            encoding_info["confidence"] = 1.0
        elif raw_data.startswith(b"\xfe\xff"):
            encoding_info["bom_detected"] = True
            encoding_info["detected_encoding"] = "utf-16-be"
            encoding_info["confidence"] = 1.0
        else:
            # Use chardet for encoding detection
            detection_result = chardet.detect(raw_data)
            encoding_info["detected_encoding"] = detection_result.get(
                "encoding", "utf-8"
            )
            encoding_info["confidence"] = detection_result.get("confidence", 0.0)

        # Detect line endings
        if b"\r\n" in raw_data:
            encoding_info["line_endings"] = "CRLF (Windows)"
        elif b"\n" in raw_data:
            encoding_info["line_endings"] = "LF (Unix/Linux/Mac)"
        elif b"\r" in raw_data:
            encoding_info["line_endings"] = "CR (Classic Mac)"
        else:
            encoding_info["line_endings"] = "None detected"

        # Check if file appears to be binary
        encoding_info["is_binary"] = not _is_likely_text(raw_data[:1024])

    except Exception as e:
        logging.warning(f"Failed to detect encoding: {str(e)}")
        encoding_info["detected_encoding"] = "utf-8"
        encoding_info["confidence"] = 0.0

    return encoding_info


def _extract_text_content(
    file_path: Path, encoding: str | None = None
) -> dict[str, Any]:
    """Extract content from text files.

    Args:
        file_path: Path to the text file
        encoding: Specific encoding to use (None for auto-detection)

    Returns:
        Dictionary containing extracted content and metadata
    """
    start_time = time.time()

    # Detect encoding if not specified
    encoding_info = _detect_encoding(file_path)

    if encoding:
        # Use specified encoding
        target_encoding = encoding
        logging.info(f"Using specified encoding: {encoding}")
    else:
        # Use detected encoding
        target_encoding = encoding_info["detected_encoding"]
        logging.info(
            f"Detected encoding: {target_encoding} (confidence: {encoding_info['confidence']:.2f})"
        )

    try:
        # Read file content
        with open(file_path, "r", encoding=target_encoding, errors="replace") as f:
            content = f.read()

        # Analyze content
        lines = content.splitlines()

        # Calculate statistics
        char_count = len(content)
        line_count = len(lines)
        word_count = len(content.split()) if content.strip() else 0

        # Find longest and shortest lines
        line_lengths = [len(line) for line in lines]
        max_line_length = max(line_lengths) if line_lengths else 0
        min_line_length = min(line_lengths) if line_lengths else 0
        avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0

        # Count empty lines
        empty_lines = sum(1 for line in lines if not line.strip())

        # Detect file type based on content patterns
        content_type = _detect_content_type(content, file_path)

        processing_time = time.time() - start_time

        return {
            "content": content,
            "encoding_info": encoding_info,
            "statistics": {
                "character_count": char_count,
                "line_count": line_count,
                "word_count": word_count,
                "empty_lines": empty_lines,
                "max_line_length": max_line_length,
                "min_line_length": min_line_length,
                "avg_line_length": round(avg_line_length, 2),
            },
            "content_type": content_type,
            "processing_time": processing_time,
            "used_encoding": target_encoding,
        }

    except UnicodeDecodeError as e:
        logging.error(
            f"Failed to decode file with encoding {target_encoding}: {str(e)}"
        )
        # Try with fallback encodings
        fallback_encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

        for fallback_encoding in fallback_encodings:
            if fallback_encoding != target_encoding:
                try:
                    with open(
                        file_path, "r", encoding=fallback_encoding, errors="replace"
                    ) as f:
                        content = f.read()

                    logging.info(
                        f"Successfully read with fallback encoding: {fallback_encoding}"
                    )

                    # Recalculate with fallback encoding
                    lines = content.splitlines()
                    char_count = len(content)
                    line_count = len(lines)
                    word_count = len(content.split()) if content.strip() else 0

                    processing_time = time.time() - start_time

                    return {
                        "content": content,
                        "encoding_info": encoding_info,
                        "statistics": {
                            "character_count": char_count,
                            "line_count": line_count,
                            "word_count": word_count,
                            "empty_lines": sum(1 for line in lines if not line.strip()),
                            "max_line_length": (
                                max(len(line) for line in lines) if lines else 0
                            ),
                            "min_line_length": (
                                min(len(line) for line in lines) if lines else 0
                            ),
                            "avg_line_length": (
                                round(sum(len(line) for line in lines) / len(lines), 2)
                                if lines
                                else 0
                            ),
                        },
                        "content_type": _detect_content_type(content, file_path),
                        "processing_time": processing_time,
                        "used_encoding": fallback_encoding,
                        "encoding_fallback": True,
                    }
                except Exception:
                    continue

        raise ValueError("Unable to decode file with any supported encoding") from e


def _detect_content_type(content: str, file_path: Path) -> str:
    """Detect the type of content based on file extension and content patterns.

    Args:
        content: File content
        file_path: Path to the file

    Returns:
        Detected content type
    """
    extension = file_path.suffix.lower()

    # Map extensions to content types
    extension_map = {
        ".py": "Python source code",
        ".js": "JavaScript source code",
        ".html": "HTML document",
        ".htm": "HTML document",
        ".css": "CSS stylesheet",
        ".json": "JSON data",
        ".xml": "XML document",
        ".yaml": "YAML configuration",
        ".yml": "YAML configuration",
        ".md": "Markdown document",
        ".markdown": "Markdown document",
        ".rst": "reStructuredText document",
        ".csv": "CSV data",
        ".tsv": "TSV data",
        ".sql": "SQL script",
        ".log": "Log file",
        ".ini": "Configuration file",
        ".cfg": "Configuration file",
        ".conf": "Configuration file",
    }

    if extension in extension_map:
        return extension_map[extension]

    # Content-based detection
    content_lower = content.lower().strip()

    if content_lower.startswith("<?xml"):
        return "XML document"
    elif content_lower.startswith("{") and content_lower.endswith("}"):
        return "JSON-like data"
    elif content_lower.startswith("[") and content_lower.endswith("]"):
        return "JSON array or configuration"
    elif "#!/" in content[:50]:
        return "Script file"
    elif content.count(",") > content.count("\n") * 2:
        return "CSV-like data"
    else:
        return "Plain text"


def _format_content_for_llm(
    extraction_result: dict[str, Any], output_format: str, max_length: int | None = None
) -> str:
    """Format extracted text content to be LLM-friendly.

    Args:
        extraction_result: Result from _extract_text_content
        output_format: Desired output format
        max_length: Maximum length of content to include (None for no limit)

    Returns:
        Formatted content string
    """
    content = extraction_result["content"]
    stats = extraction_result["statistics"]
    content_type = extraction_result["content_type"]

    # Truncate content if needed
    if max_length and len(content) > max_length:
        content = (
            content[:max_length]
            + f"\n\n[Content truncated - showing first {max_length} characters of {stats['character_count']} total]"
        )

    if output_format.lower() == "markdown":
        formatted_parts = []
        formatted_parts.append("# Text Document Content\n")
        formatted_parts.append(f"**File Type:** {content_type}\n")
        formatted_parts.append(f"**Encoding:** {extraction_result['used_encoding']}\n")
        formatted_parts.append("**Statistics:**\n")
        formatted_parts.append(f"- Characters: {stats['character_count']:,}\n")
        formatted_parts.append(f"- Lines: {stats['line_count']:,}\n")
        formatted_parts.append(f"- Words: {stats['word_count']:,}\n")
        formatted_parts.append(f"- Empty lines: {stats['empty_lines']:,}\n")
        formatted_parts.append(
            f"- Average line length: {stats['avg_line_length']} characters\n\n"
        )

        formatted_parts.append(f"## Content\n\n```\n{content}\n```")

        return "".join(formatted_parts)

    elif output_format.lower() == "json":
        json_data = {
            "document_info": {
                "content_type": content_type,
                "encoding": extraction_result["used_encoding"],
                "statistics": stats,
            },
            "content": content,
        }

        return json.dumps(json_data, indent=2, ensure_ascii=False)

    elif output_format.lower() == "html":
        html_parts = []
        html_parts.append("<html><head><meta charset='utf-8'></head><body>")
        html_parts.append("<h1>Text Document Content</h1>")
        html_parts.append(f"<p><strong>File Type:</strong> {content_type}</p>")
        html_parts.append(
            f"<p><strong>Encoding:</strong> {extraction_result['used_encoding']}</p>"
        )
        html_parts.append("<h2>Statistics</h2>")
        html_parts.append("<ul>")
        html_parts.append(f"<li>Characters: {stats['character_count']:,}</li>")
        html_parts.append(f"<li>Lines: {stats['line_count']:,}</li>")
        html_parts.append(f"<li>Words: {stats['word_count']:,}</li>")
        html_parts.append(f"<li>Empty lines: {stats['empty_lines']:,}</li>")
        html_parts.append(
            f"<li>Average line length: {stats['avg_line_length']} characters</li>"
        )
        html_parts.append("</ul>")
        html_parts.append("<h2>Content</h2>")
        html_parts.append(f"<pre><code>{content}</code></pre>")
        html_parts.append("</body></html>")

        return "".join(html_parts)

    else:  # text format
        text_parts = []
        text_parts.append(f"Text Document Content\n{'=' * 50}\n")
        text_parts.append(f"File Type: {content_type}\n")
        text_parts.append(f"Encoding: {extraction_result['used_encoding']}\n")
        text_parts.append("\nStatistics:\n")
        text_parts.append(f"  Characters: {stats['character_count']:,}\n")
        text_parts.append(f"  Lines: {stats['line_count']:,}\n")
        text_parts.append(f"  Words: {stats['word_count']:,}\n")
        text_parts.append(f"  Empty lines: {stats['empty_lines']:,}\n")
        text_parts.append(
            f"  Average line length: {stats['avg_line_length']} characters\n"
        )
        text_parts.append(f"\nContent:\n{'-' * 30}\n{content}")

        return "".join(text_parts)


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting documents-txt-server MCP server!")
    mcp.run(transport="stdio")
