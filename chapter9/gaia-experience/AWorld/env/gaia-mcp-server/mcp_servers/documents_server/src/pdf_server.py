import asyncio
import json
import logging
import os
import sys
import traceback

import filetype
from pathlib import Path
from typing import Literal, Union, Any

import requests
from datalab_sdk.models import ConversionResult, ConvertOptions, OCROptions
from dotenv import load_dotenv
from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field, BaseModel
from pydantic.fields import FieldInfo
from requests import Response




class ActionResponse(BaseModel):
    r"""Protocol: MCP Action Response"""

    success: bool = Field(default=False, description="Whether the action is successfully executed")
    message: Any = Field(default=None, description="The execution result of the action")
    metadata: dict[str, Any] = Field(default={}, description="The metadata of the action")

# 设置Python路径，确保子进程能找到core模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)





load_dotenv()
_models_loaded = False
_marker_models = None
workspace = Path.home()
_extracted_texts_dir = workspace / "processed_documents"
_extracted_texts_dir.mkdir(exist_ok=True, parents=True)
DATALAB_URL = "https://www.datalab.to/api/v1"

supported_extensions = {".pdf"}

class DocumentResult(BaseModel):
    file_path: str = Field(..., description="Path to the processed document")
    conversion_result: ConversionResult | None = (
        Field(None, description="Conversion result"),
    )
    errors: list[str] | None = Field(
        None, description="Error messages if processing failed"
    )


class DocumentEntity(BaseModel):
    """Represents a document entity with its metadata and content."""

    file_name: str = Field(..., description="Name of the document file")
    file_path: str | Path = Field(..., description="Absolute path to the document file")
    file_types: Literal[
        # pdf
        "application/pdf",
        # spreadsheet
        "application/vnd.ms-excel",  # xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.oasis.opendocument.spreadsheet",  # ods
        # word
        "application/msword",  # doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.oasis.opendocument.text",  # odt
        # presentation
        "application/vnd.ms-powerpoint",  # ppt
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
        "application/vnd.oasis.opendocument.presentation",  # odp
        # html
        "text/html",
        # image
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/tiff",
        "image/webp",
        # epub
        "application/epub+zip",
    ] = Field(..., description="MIME type of the document file")


mcp = FastMCP("documents-pdf-server", instructions="""
MCP service for PDF document content extraction using marker package.

    Supports extraction from PDF files only.
    Provides LLM-friendly text output with structured metadata and media file handling.
""")

@mcp.tool(
    description=(
        "Convert PDF document to markdown foramt. "
    )
)
async def convert_document_to_markdown(
    file_path: str = Field(..., description="Path to the document file"),
    paginate: bool = Field(False, description="Add page delimiters to the output"),
) -> Union[str, TextContent]:
        #-> DocumentResult:
    """
    Process document using Datalab SDK with advanced OCR capabilities.

    Convert document to markdown foramt. "
    Support PDFs, DOCX, XLSX, PPTX, HTML, and images.

    Returns DocumentResult with conversion results.
    """
    if isinstance(file_path, FieldInfo):
        file_path: str = file_path.default
    if isinstance(paginate, FieldInfo):
        paginate: bool = paginate.default

    result: DocumentResult = DocumentResult(file_path=file_path)
    try:
        file_entity: DocumentEntity = _prepare_file_entity(file_path)
        session: dict = await _establish_document_session(
            file_entity,
            options=ConvertOptions(
                output_format="markdown",
                paginate=paginate,
                use_llm=True,
                max_pages=None,
            ),
        )
        conversion_result: ConversionResult = await _poll_result(
            session["request_check_url"]
        )
        result.conversion_result = conversion_result
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(result.model_dump()),
        }
        action_response = ActionResponse(
            success=True,
            message=json.dumps(result.model_dump()),
            metadata=output_dict,
        )
    except Exception as e:
        result.errors = [traceback.format_exc(), str(e)]
        action_response = ActionResponse(
            success=False,
            message=json.dumps(result.model_dump()),
            metadata={},
        )

    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": {}}  # Pass as additional fields
    )

async def _poll_result(
    check_url: str,
    max_polls: int = 300,
    poll_interval: int = 2,
) -> ConversionResult:
    """
    Poll the Datalab API for the result of the document processing.
    """
    try:
        for _ in range(max_polls):
            await asyncio.sleep(poll_interval)
            response: Response = requests.get(
                check_url,
                headers={"X-Api-Key": os.getenv("DATALAB_API_KEY")},
                timeout=5,
            )
            result_data: dict = response.json()
            if result_data["status"] == "complete":
                return ConversionResult(
                    success=result_data.get("success", False),
                    output_format="markdown",
                    markdown=result_data.get("markdown"),
                    html=result_data.get("html"),
                    json=result_data.get("json"),
                    #images=result_data.get("images"),
                    metadata=result_data.get("metadata"),
                    error=result_data.get("error"),
                    page_count=result_data.get("page_count"),
                    status=result_data.get("status", "complete"),
                )
        raise TimeoutError("Document processing timed out.")
    except Exception as e:
        raise RuntimeError(
            f"Failed to poll document result: {traceback.format_exc()}"
        ) from e

def _prepare_file_entity(file_path: [str | Path]) -> DocumentEntity:
    """
    Prepare a DocumentEntity from the given file path.
    """
    file_path: Path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return DocumentEntity(
        file_name=file_path.resolve().name,
        file_path=file_path.resolve(),
        file_types=filetype.guess(file_path).mime or "application/pdf",
    )

async def _establish_document_session(
    file_entity: DocumentEntity,
    options: [ConvertOptions | OCROptions],
    endpoint: str = "/marker",
) -> dict:
    """
    Establish a session for document processing with Datalab API.
    """
    if not os.getenv("DATALAB_API_KEY"):
        raise ValueError("DATALAB_API_KEY environment variable is not set.")

    try:
        response: Response = requests.post(
            url=DATALAB_URL + endpoint,
            files={
                "file": (
                    file_entity.file_name,
                    open(file_entity.file_path, "rb"),
                    file_entity.file_types,
                ),
                "force_ocr": (None, False),
                "paginate": (
                    None,
                    options.paginate if isinstance(options, ConvertOptions) else False,
                ),
                "output_format": (None, "markdown"),
                "use_llm": (
                    None,
                    options.use_llm if isinstance(options, ConvertOptions) else False,
                ),
                "strip_existing_ocr": (None, False),
                "disable_image_extraction": (None, False),
            },
            headers={"X-Api-Key": os.getenv("DATALAB_API_KEY")},
            timeout=120,
        )
        return response.json()
    except Exception as e:
        raise RuntimeError(
            f"Failed to establish document session: {traceback.format_exc()}"
        ) from e

if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting documents-pdf-server MCP server!")
    mcp.run(transport="stdio")
