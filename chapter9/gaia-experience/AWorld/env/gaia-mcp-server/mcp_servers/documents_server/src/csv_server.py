import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, Union, Literal

import chardet
import pandas as pd
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
)

load_dotenv()
workspace = Path.home()
_media_output_dir = workspace / "extracted_media"
_media_output_dir.mkdir(exist_ok=True, parents=True)

supported_extensions: set = {".csv", ".tsv", ".txt"}


mcp = FastMCP(
    "documents-csv-server",
    instructions="""
MCP service for CSV document content extraction using pandas.

    Supports extraction from CSV files with various encodings and delimiters.
    Provides LLM-friendly text output with structured metadata and data analysis.
""",
)


@mcp.tool(
    description="""
Extract content from CSV documents using pandas.

        This tool provides comprehensive CSV document content extraction with support for:
        - CSV, TSV, and delimited text files
        - Automatic encoding and delimiter detection
        - Statistical analysis and data profiling
        - Multiple output formats (Markdown)
        - Optional data visualizations
        - Memory-efficient processing for large files
"""
)
async def extract_csv_content(
    file_path: str = Field(
        description="Path to the CSV document file to extract content from"
    ),
    output_format: Literal["markdown"] = Field(
        default="markdown", description="Output format: 'markdown'"
    ),
    # output_format: Literal["markdown", "json", "html", "text"] = Field(
    #     default="markdown", description="Output format: 'markdown', 'json', 'html', or 'text'"
    # ),
    max_rows: int | None = Field(
        default=None, description="Maximum number of rows to read (None for all rows)"
    ),
    include_statistics: bool = Field(
        default=True, description="Whether to include statistical summary in output"
    ),
    generate_visualizations: bool = Field(
        default=False, description="Whether to generate and save data visualizations"
    ),
    encoding: str | None = Field(
        default=None, description="File encoding (auto-detected if None)"
    ),
    delimiter: str | None = Field(
        default=None, description="CSV delimiter (auto-detected if None)"
    ),
) -> Union[str, TextContent]:
    try:
        # Handle FieldInfo objects from pydantic
        if isinstance(file_path, FieldInfo):
            file_path = file_path.default
        if isinstance(output_format, FieldInfo):
            output_format = output_format.default
        if isinstance(max_rows, FieldInfo):
            max_rows = max_rows.default
        if isinstance(include_statistics, FieldInfo):
            include_statistics = include_statistics.default
        if isinstance(generate_visualizations, FieldInfo):
            generate_visualizations = generate_visualizations.default
        if isinstance(encoding, FieldInfo):
            encoding = encoding.default
        if isinstance(delimiter, FieldInfo):
            delimiter = delimiter.default

        # Validate input file
        file_path: Path = _validate_file_path(file_path)
        logging.info(f"Processing CSV file: {file_path.name}")

        # Extract CSV content
        extraction_result = _extract_csv_content(
            file_path, max_rows=max_rows, encoding=encoding, delimiter=delimiter
        )

        df: pd.DataFrame = extraction_result["dataframe"]

        # Format content for LLM consumption
        formatted_content = _format_content_for_llm(
            df, output_format, include_stats=include_statistics
        )

        # Prepare metadata
        file_stats = file_path.stat()
        document_metadata = DocumentMetadata(
            file_name=file_path.name,
            file_size=file_stats.st_size,
            file_type=file_path.suffix.lower(),
            absolute_path=str(file_path.absolute()),
            page_count=None,  # Not applicable for CSV
            processing_time=extraction_result["processing_time"],
            extracted_images=[],  # CSV files don't contain images
            extracted_media=[],  # CSV files don't contain media files
            output_format=output_format,
            llm_enhanced=False,
            ocr_applied=False,
        )

        # Add CSV-specific metadata
        csv_metadata = {
            "total_rows": extraction_result["total_rows"],
            "total_columns": extraction_result["total_columns"],
            "rows_processed": len(df),
            "columns_processed": len(df.columns),
            "column_names": extraction_result["columns"],
            "data_types": {
                k: str(v) for k, v in extraction_result["data_types"].items()
            },
            "encoding": extraction_result["encoding"],
            "delimiter": extraction_result["delimiter"],
            "memory_usage_bytes": int(extraction_result["memory_usage"]),
        }

        # Merge metadata
        final_metadata = {**document_metadata.model_dump(), **csv_metadata}

        logging.info(
            f"Successfully extracted CSV content from {file_path.name}-({extraction_result['total_rows']} rows, {extraction_result['total_columns']} columns "
        )

        action_response = ActionResponse(
            success=True, message=formatted_content, metadata=final_metadata
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
        logging.error(f"File not found: {str(e)}")
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
        logging.error(f"Invalid input: {str(e)}")
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
        logging.error(f"CSV extraction failed: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"CSV extraction failed: {str(e)}",
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
List all supported CSV formats for extraction.
"""
)
async def list_supported_formats() -> Union[str, TextContent]:
    supported_formats = {
        "CSV": "Comma-Separated Values files (.csv)",
        "TSV": "Tab-Separated Values files (.tsv)",
        "TXT": "Delimited text files (.txt)",
    }

    format_list = "\n".join(
        [
            f"**{format_name}**: {description}"
            for format_name, description in supported_formats.items()
        ]
    )

    action_response = ActionResponse(
        success=True,
        message=f"Supported CSV formats:\n\n{format_list}",
        metadata={
            "supported_formats": list(supported_formats.keys()),
            "total_formats": len(supported_formats),
        },
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": {
            "supported_formats": list(supported_formats.keys()),
            "total_formats": len(supported_formats),
        }
    }
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )


def _detect_encoding(file_path: Path) -> str:
    """Detect file encoding using chardet.

    Args:
        file_path: Path to the CSV file

    Returns:
        Detected encoding string
    """
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            result = chardet.detect(raw_data)
            encoding = result.get("encoding", "utf-8")
            confidence = result.get("confidence", 0)

            logging.info(
                f"Detected encoding: {encoding} (confidence: {confidence:.2f})"
            )
            return encoding if confidence > 0.7 else "utf-8"
    except Exception as e:
        logging.warning(f"Encoding detection failed: {e}, using utf-8")
        return "utf-8"


def _detect_delimiter(file_path: Path, encoding: str) -> str:
    """Detect CSV delimiter by analyzing the first few lines.

    Args:
        file_path: Path to the CSV file
        encoding: File encoding

    Returns:
        Detected delimiter character
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            sample = f.read(1024)  # Read first 1KB

        # Common delimiters to test
        delimiters = [",", ";", "\t", "|", ":"]
        delimiter_counts = {}

        for delimiter in delimiters:
            count = sample.count(delimiter)
            if count > 0:
                delimiter_counts[delimiter] = count

        if delimiter_counts:
            detected_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            logging.info(f"Detected delimiter: '{detected_delimiter}'")
            return detected_delimiter
        else:
            return ","
    except Exception as e:
        logging.warning(f"Delimiter detection failed: {e}, using comma")
        return ","


def _extract_csv_content(
    file_path: Path,
    max_rows: int | None = None,
    encoding: str | None = None,
    delimiter: str | None = None,
) -> dict[str, Any]:
    """Extract content from CSV file using pandas.

    Args:
        file_path: Path to the CSV file
        max_rows: Maximum number of rows to read
        encoding: File encoding (auto-detected if None)
        delimiter: CSV delimiter (auto-detected if None)

    Returns:
        Dictionary containing extracted content and metadata
    """
    start_time = time.time()

    # Auto-detect encoding and delimiter if not provided
    if encoding is None:
        encoding = _detect_encoding(file_path)
    if delimiter is None:
        delimiter = _detect_delimiter(file_path, encoding)

    try:
        # Read CSV with pandas
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            delimiter=delimiter,
            nrows=max_rows,
            low_memory=False,
        )

        # Get full file info for metadata
        full_df_info = pd.read_csv(
            file_path,
            encoding=encoding,
            delimiter=delimiter,
            nrows=0,  # Just get headers and shape info
        )

        # Count total rows efficiently
        total_rows = (
            sum(1 for _ in open(file_path, "r", encoding=encoding)) - 1
        )  # Subtract header

        processing_time = time.time() - start_time

        return {
            "dataframe": df,
            "total_rows": total_rows,
            "total_columns": len(full_df_info.columns),
            "columns": list(df.columns),
            "encoding": encoding,
            "delimiter": delimiter,
            "processing_time": processing_time,
            "data_types": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
        }

    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        raise


def _format_content_for_llm(
    df: pd.DataFrame, output_format: str, include_stats: bool = True
) -> str:
    """Format extracted CSV content to be LLM-friendly.

    Args:
        df: Pandas DataFrame with CSV data
        output_format: Desired output format
        include_stats: Whether to include statistical summary

    Returns:
        Formatted content string
    """
    if output_format.lower() == "markdown":
        # Convert to markdown table
        content = df.to_markdown(index=False, tablefmt="github")

        if include_stats:
            # Add statistical summary
            stats_content = "\n\n## Data Summary\n\n"
            stats_content += f"- **Rows**: {len(df)}\n"
            stats_content += f"- **Columns**: {len(df.columns)}\n"
            stats_content += f"- **Column Names**: {', '.join(df.columns)}\n\n"

            # Add data types info
            stats_content += "### Column Data Types\n\n"
            for col, dtype in df.dtypes.items():
                stats_content += f"- **{col}**: {dtype}\n"

            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                stats_content += "\n### Numeric Column Statistics\n\n"
                stats_df = df[numeric_cols].describe()
                stats_content += stats_df.to_markdown(tablefmt="github")

            content += stats_content

    elif output_format.lower() == "json":
        # Convert to JSON with metadata
        data_dict = {
            "data": df.to_dict(orient="records"),
            "metadata": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            },
        }
        if include_stats:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                data_dict["statistics"] = df[numeric_cols].describe().to_dict()

        content = json.dumps(data_dict, indent=2, default=str)

    elif output_format.lower() == "html":
        # Convert to HTML table
        content = df.to_html(index=False, classes="table table-striped")

    else:
        # Plain text format
        content = df.to_string(index=False)

    return content


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting documents-csv-server MCP server!")
    mcp.run(transport="stdio")
