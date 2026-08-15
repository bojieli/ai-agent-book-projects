import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Union

import arxiv
from dotenv import load_dotenv
from pydantic.fields import FieldInfo
from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field, BaseModel

from base import ActionResponse


load_dotenv()
workspace = Path.home()
supported_extensions = {".pdf"}

# ArXiv client configuration
client = arxiv.Client(
    page_size=100,
    delay_seconds=3.0,  # Be respectful to ArXiv servers
    num_retries=3,
)

# Create downloads directory
_downloads_dir = workspace / "arxiv_downloads"
_downloads_dir.mkdir(exist_ok=True)

# ArXiv subject categories mapping
subject_categories = {
    "cs": "Computer Science",
    "math": "Mathematics",
    "physics": "Physics",
    "astro-ph": "Astrophysics",
    "cond-mat": "Condensed Matter",
    "gr-qc": "General Relativity and Quantum Cosmology",
    "hep-ex": "High Energy Physics - Experiment",
    "hep-lat": "High Energy Physics - Lattice",
    "hep-ph": "High Energy Physics - Phenomenology",
    "hep-th": "High Energy Physics - Theory",
    "math-ph": "Mathematical Physics",
    "nlin": "Nonlinear Sciences",
    "nucl-ex": "Nuclear Experiment",
    "nucl-th": "Nuclear Theory",
    "quant-ph": "Quantum Physics",
    "q-bio": "Quantitative Biology",
    "q-fin": "Quantitative Finance",
    "stat": "Statistics",
    "econ": "Economics",
    "eess": "Electrical Engineering and Systems Science",
}


class PaperResult(BaseModel):
    """Individual paper search result with structured data."""

    entry_id: str
    title: str
    authors: list[str]
    summary: str
    published: str
    updated: str | None = None
    categories: list[str]
    primary_category: str
    pdf_url: str | None = None
    doi: str | None = None
    journal_ref: str | None = None
    comment: str | None = None


class ArxivMetadata(BaseModel):
    """Metadata for ArXiv operation results."""

    operation: str
    query: str | None = None
    max_results: int | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    total_results: int | None = None
    execution_time: float | None = None
    error_type: str | None = None
    paper_id: str | None = None
    download_path: str | None = None
    file_size: int | None = None


mcp = FastMCP(
    "parxiv-server",
    instructions="""
ArXiv MCP Server

This module provides MCP server functionality for ArXiv academic paper operations.
It supports paper search, metadata extraction, and content retrieval with LLM-friendly formatting.

Key features:
- Search ArXiv papers by query, author, category, or ID
- Extract paper metadata (title, authors, abstract, etc.)
- Download and process paper PDFs
- LLM-optimized content formatting
- Comprehensive error handling and logging

Main functions:
- mcp_search_papers: Search ArXiv papers with flexible criteria
- mcp_get_paper_details: Get detailed information about specific papers
- mcp_download_paper: Download paper PDF and extract text content
- mcp_get_categories: Get available ArXiv subject categories
- mcp_get_arxiv_capabilities: Get service capabilities and configuration
""",
)


@mcp.tool(
    description="""
Search ArXiv papers with flexible criteria.

        This tool provides comprehensive ArXiv paper search with:
        - Keyword, title, and author search capabilities
        - Category filtering for specific subject areas
        - Flexible sorting options (relevance, date)
        - Configurable result limits
        - LLM-optimized result formatting
"""
)
async def search_papers(
    query: str = Field(description="Search query (keywords, title, author, etc.)"),
    sort_by: str = Field(
        default="relevance",
        description="Sort by: 'relevance', 'lastUpdatedDate', 'submittedDate'",
    ),
    sort_order: str = Field(
        default="descending", description="Sort order: 'ascending' or 'descending'"
    ),
    category: str | None = Field(
        default=None, description="Filter by ArXiv category (e.g., 'cs.AI', 'math.CO')"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(query, FieldInfo):
        query = query.default
    if isinstance(sort_by, FieldInfo):
        sort_by = sort_by.default
    if isinstance(sort_order, FieldInfo):
        sort_order = sort_order.default
    if isinstance(category, FieldInfo):
        category = category.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        logging.info(f"🔍 Searching ArXiv for: {query}")

        start_time = datetime.now()

        # Build search query
        search_query = query
        if category:
            search_query = f"cat:{category} AND ({query})"

        # Configure sort criteria
        sort_criterion = arxiv.SortCriterion.Relevance
        if sort_by == "lastUpdatedDate":
            sort_criterion = arxiv.SortCriterion.LastUpdatedDate
        elif sort_by == "submittedDate":
            sort_criterion = arxiv.SortCriterion.SubmittedDate

        sort_order_enum = arxiv.SortOrder.Descending
        if sort_order == "ascending":
            sort_order_enum = arxiv.SortOrder.Ascending

        # Perform search
        search = arxiv.Search(
            query=search_query,
            max_results=300000,
            sort_by=sort_criterion,
            sort_order=sort_order_enum,
        )

        # Execute search and collect results
        results = []
        for paper in client.results(search):
            results.append(_format_paper_result(paper))

        execution_time = (datetime.now() - start_time).total_seconds()

        # Format output
        formatted_output = _format_search_results(results, output_format)

        # Create metadata
        metadata = ArxivMetadata(
            operation="search_papers",
            query=query,
            sort_by=sort_by,
            sort_order=sort_order,
            total_results=len(results),
            execution_time=execution_time,
        )

        logging.info(f"✅ Found {len(results)} papers in {execution_time:.2f}s")

        action_response = ActionResponse(
            success=True, message=formatted_output, metadata=metadata.model_dump()
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to search ArXiv papers: {str(e)}"
        logging.error(f"ArXiv search error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=ArxivMetadata(
                operation="search_papers", query=query, error_type="search_error"
            ).model_dump(),
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
Get detailed information about a specific ArXiv paper.
"""
)
async def get_paper_details(
    paper_id: str = Field(
        description="ArXiv paper ID (e.g., '2301.07041' or 'arxiv:2301.07041')"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(paper_id, FieldInfo):
        paper_id = paper_id.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Clean paper ID
        clean_id = paper_id.replace("arxiv:", "").strip()

        logging.info(f"📄 Getting details for paper: {clean_id}")

        start_time = datetime.now()

        # Search for the specific paper
        search = arxiv.Search(id_list=[clean_id])

        paper = next(client.results(search), None)
        if not paper:
            action_response = ActionResponse(
                success=False,
                message=f"Paper not found: {clean_id}",
                metadata=ArxivMetadata(
                    operation="get_paper_details",
                    paper_id=clean_id,
                    error_type="paper_not_found",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Format paper details
        paper_result = _format_paper_result(paper)
        formatted_output = _format_paper_details(paper_result, output_format)

        # Create metadata
        metadata = ArxivMetadata(
            operation="get_paper_details",
            paper_id=clean_id,
            execution_time=execution_time,
        )

        logging.info(f"✅ Retrieved paper details in {execution_time:.2f}s")

        action_response = ActionResponse(
            success=True, message=formatted_output, metadata=metadata.model_dump()
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to get paper details: {str(e)}"
        logging.error(f"Paper details error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=ArxivMetadata(
                operation="get_paper_details",
                paper_id=paper_id,
                error_type="retrieval_error",
            ).model_dump(),
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
Download ArXiv paper PDF and optionally extract text content.
"""
)
async def download_paper(
    paper_id: str = Field(
        description="ArXiv paper ID (e.g., '2301.07041' or 'arxiv:2301.07041')"
    ),
    extract_text: bool = Field(
        default=True, description="Whether to extract text content from PDF"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(paper_id, FieldInfo):
        paper_id = paper_id.default
    if isinstance(extract_text, FieldInfo):
        extract_text = extract_text.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Clean paper ID
        clean_id = paper_id.replace("arxiv:", "").strip()

        logging.info(f"📥 Downloading paper: {clean_id}")

        start_time = datetime.now()

        # Search for the paper
        search = arxiv.Search(id_list=[clean_id])
        paper = next(client.results(search), None)

        if not paper:
            action_response = ActionResponse(
                success=False,
                message=f"Paper not found: {clean_id}",
                metadata=ArxivMetadata(
                    operation="download_paper",
                    paper_id=clean_id,
                    error_type="paper_not_found",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        # Download PDF
        filename = f"{clean_id.replace('/', '_')}.pdf"
        download_path = _downloads_dir / filename

        paper.download_pdf(dirpath=str(_downloads_dir), filename=filename)

        execution_time = (datetime.now() - start_time).total_seconds()
        file_size = download_path.stat().st_size if download_path.exists() else 0

        # Prepare response message
        if output_format == "json":
            response_data = {
                "paper_id": clean_id,
                "title": paper.title,
                "download_path": str(download_path),
                "file_size": file_size,
                "download_time": execution_time,
            }

            if extract_text:
                try:
                    # Basic text extraction (would need additional libraries like PyPDF2 or pdfplumber)
                    response_data["text_extraction"] = (
                        "Text extraction requires additional PDF processing libraries"
                    )
                except Exception:
                    response_data["text_extraction"] = "Text extraction failed"

            formatted_output = json.dumps(response_data, indent=2)

        elif output_format == "text":
            output_parts = [
                "Paper Downloaded Successfully",
                f"Paper ID: {clean_id}",
                f"Title: {paper.title}",
                f"Download Path: {download_path}",
                f"File Size: {file_size:,} bytes",
                f"Download Time: {execution_time:.2f} seconds",
            ]

            if extract_text:
                output_parts.append(
                    "\nNote: Text extraction requires additional PDF processing libraries"
                )

            formatted_output = "\n".join(output_parts)

        else:  # markdown (default)
            output_parts = [
                "# 📥 Paper Download Complete",
                "",
                f"**Paper ID:** `{clean_id}`",
                f"**Title:** {paper.title}",
                f"**Download Path:** `{download_path}`",
                f"**File Size:** {file_size:,} bytes",
                f"**Download Time:** {execution_time:.2f} seconds",
            ]

            if extract_text:
                output_parts.extend(
                    [
                        "",
                        "## 📄 Text Extraction",
                        (
                            "*Note: Text extraction requires additional "
                            "PDF processing libraries like PyPDF2 or pdfplumber*"
                        ),
                    ]
                )

            formatted_output = "\n".join(output_parts)

        # Create metadata
        metadata = ArxivMetadata(
            operation="download_paper",
            paper_id=clean_id,
            download_path=str(download_path),
            file_size=file_size,
            execution_time=execution_time,
        )

        logging.info(
            f"✅ Downloaded paper in {execution_time:.2f}s ({file_size:,} bytes)"
        )

        action_response = ActionResponse(
            success=True, message=formatted_output, metadata=metadata.model_dump()
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to download paper: {str(e)}"
        logging.error(f"Paper download error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=ArxivMetadata(
                operation="download_paper",
                paper_id=paper_id,
                error_type="download_error",
            ).model_dump(),
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
Get information about ArXiv service capabilities and configuration.
"""
)
async def get_arxiv_capabilities() -> Union[str, TextContent]:
    capabilities = {
        "supported_operations": [
            "Paper search with flexible criteria",
            "Detailed paper metadata retrieval",
            "PDF download and storage",
            "Subject category filtering",
            "Multiple output formats (markdown, json, text)",
            "LLM-optimized result formatting",
        ],
        "search_capabilities": [
            "Keyword and phrase search",
            "Author name search",
            "Title search",
            "Category filtering",
            "Date-based sorting",
            "Relevance-based sorting",
        ],
        "supported_formats": ["markdown", "json", "text"],
        "configuration": {
            "downloads_directory": str(_downloads_dir),
            "client_page_size": 100,
            "client_delay_seconds": 3.0,
            "client_num_retries": 3,
            "supported_categories_count": len(subject_categories),
        },
        "rate_limiting": {
            "delay_between_requests": "3.0 seconds",
            "retry_attempts": 3,
            "respectful_usage": "Configured for ArXiv server guidelines",
        },
    }

    formatted_info = f"""# ArXiv Service Capabilities

            ## Supported Operations
            {chr(10).join(f"- {op}" for op in capabilities["supported_operations"])}

            ## Search Capabilities  
            {chr(10).join(f"- {cap}" for cap in capabilities["search_capabilities"])}

            ## Supported Output Formats
            {chr(10).join(f"- {fmt}" for fmt in capabilities["supported_formats"])}

            ## Current Configuration
            - **Downloads Directory:** {capabilities["configuration"]["downloads_directory"]}
            - **Client Page Size:** {capabilities["configuration"]["client_page_size"]}
            - **Request Delay:** {capabilities["configuration"]["client_delay_seconds"]} seconds
            - **Retry Attempts:** {capabilities["configuration"]["client_num_retries"]}
            - **Available Categories:** {capabilities["configuration"]["supported_categories_count"]}

            ## Rate Limiting & Ethics
            - **Delay Between Requests:** {capabilities["rate_limiting"]["delay_between_requests"]}
            - **Retry Policy:** {capabilities["rate_limiting"]["retry_attempts"]} attempts
            - **Server Respect:** {capabilities["rate_limiting"]["respectful_usage"]}
            """

    action_response = ActionResponse(
        success=True, message=formatted_info, metadata=capabilities
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": json.dumps(
            action_response.model_dump()
        )
    }
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )


@mcp.tool(
    description="""
Get available ArXiv subject categories.
"""
)
async def get_categories(
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        if output_format == "json":
            formatted_output = json.dumps(subject_categories, indent=2)

        elif output_format == "text":
            output_parts = ["ArXiv Subject Categories:\n"]
            for code, name in subject_categories.items():
                output_parts.append(f"{code}: {name}")
            formatted_output = "\n".join(output_parts)

        else:  # markdown (default)
            output_parts = [
                "# ArXiv Subject Categories",
                "",
                "Available categories for filtering search results:",
                "",
            ]

            for code, name in subject_categories.items():
                output_parts.append(f"- **`{code}`**: {name}")

            output_parts.extend(
                [
                    "",
                    "## Usage Examples",
                    "- `cs.AI` - Artificial Intelligence",
                    "- `cs.LG` - Machine Learning",
                    "- `math.CO` - Combinatorics",
                    "- `physics.gen-ph` - General Physics",
                ]
            )

            formatted_output = "\n".join(output_parts)

        metadata = ArxivMetadata(
            operation="get_categories", total_results=len(subject_categories)
        )

        action_response = ActionResponse(
            success=True, message=formatted_output, metadata=metadata.model_dump()
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to get categories: {str(e)}"
        logging.error(f"Categories error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=ArxivMetadata(
                operation="get_categories", error_type="internal_error"
            ).model_dump(),
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )


def _format_paper_result(paper: arxiv.Result) -> PaperResult:
    """Convert arxiv.Result to structured PaperResult.

    Args:
        paper: ArXiv paper result object

    Returns:
        Structured PaperResult object
    """
    return PaperResult(
        entry_id=paper.entry_id,
        title=paper.title.strip(),
        authors=[author.name for author in paper.authors],
        summary=paper.summary.strip(),
        published=paper.published.isoformat(),
        updated=paper.updated.isoformat() if paper.updated else None,
        categories=paper.categories,
        primary_category=paper.primary_category,
        pdf_url=paper.pdf_url,
        doi=paper.doi,
        journal_ref=paper.journal_ref,
        comment=paper.comment,
    )


def _format_search_results(
    results: list[PaperResult], output_format: str = "markdown"
) -> str:
    """Format paper search results for LLM consumption.

    Args:
        results: List of paper results
        output_format: Format type ('markdown', 'json', 'text')

    Returns:
        Formatted string suitable for LLM consumption
    """
    if not results:
        return "No papers found matching the search criteria."

    if output_format == "json":
        return json.dumps([result.model_dump() for result in results], indent=2)

    elif output_format == "text":
        output_parts = [f"Found {len(results)} papers:\n"]

        for i, paper in enumerate(results, 1):
            authors_str = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                authors_str += f" et al. ({len(paper.authors)} total)"

            output_parts.extend(
                [
                    f"{i}. {paper.title}",
                    f"   Authors: {authors_str}",
                    f"   Published: {paper.published[:10]}",
                    f"   Categories: {', '.join(paper.categories)}",
                    f"   ArXiv ID: {paper.entry_id.split('/')[-1]}",
                    f"   Abstract: {paper.summary[:200]}...",
                    "",
                ]
            )

        return "\n".join(output_parts)

    else:  # markdown (default)
        output_parts = [f"# ArXiv Search Results\n\nFound **{len(results)}** papers:\n"]

        for i, paper in enumerate(results, 1):
            authors_str = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                authors_str += f" *et al.* ({len(paper.authors)} total)"

            arxiv_id = paper.entry_id.split("/")[-1]

            output_parts.extend(
                [
                    f"## {i}. {paper.title}",
                    f"**Authors:** {authors_str}",
                    f"**Published:** {paper.published[:10]}",
                    f"**Categories:** {', '.join(paper.categories)}",
                    f"**ArXiv ID:** `{arxiv_id}`",
                    f"**PDF:** [Download]({paper.pdf_url})" if paper.pdf_url else "",
                    "",
                    f"**Abstract:** {paper.summary}",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(output_parts)


def _format_paper_details(paper: PaperResult, output_format: str = "markdown") -> str:
    """Format detailed paper information for LLM consumption.

    Args:
        paper: Paper result object
        output_format: Format type ('markdown', 'json', 'text')

    Returns:
        Formatted string with detailed paper information
    """
    if output_format == "json":
        return json.dumps(paper.model_dump(), indent=2)

    elif output_format == "text":
        output_parts = [
            f"Title: {paper.title}",
            f"Authors: {', '.join(paper.authors)}",
            f"Published: {paper.published}",
            f"Updated: {paper.updated or 'N/A'}",
            f"Primary Category: {paper.primary_category}",
            f"All Categories: {', '.join(paper.categories)}",
            f"ArXiv ID: {paper.entry_id.split('/')[-1]}",
            f"PDF URL: {paper.pdf_url or 'N/A'}",
            f"DOI: {paper.doi or 'N/A'}",
            f"Journal Reference: {paper.journal_ref or 'N/A'}",
            f"Comment: {paper.comment or 'N/A'}",
            "",
            "Abstract:",
            paper.summary,
        ]

        return "\n".join(output_parts)

    else:  # markdown (default)
        arxiv_id = paper.entry_id.split("/")[-1]

        output_parts = [
            f"# {paper.title}",
            "",
            f"**Authors:** {', '.join(paper.authors)}",
            f"**Published:** {paper.published[:10]}",
            f"**Updated:** {paper.updated[:10] if paper.updated else 'N/A'}",
            f"**Primary Category:** {paper.primary_category}",
            f"**All Categories:** {', '.join(paper.categories)}",
            f"**ArXiv ID:** `{arxiv_id}`",
            (
                f"**PDF:** [Download]({paper.pdf_url})"
                if paper.pdf_url
                else "**PDF:** N/A"
            ),
            f"**DOI:** {paper.doi}" if paper.doi else "**DOI:** N/A",
            (
                f"**Journal Reference:** {paper.journal_ref}"
                if paper.journal_ref
                else "**Journal Reference:** N/A"
            ),
            f"**Comment:** {paper.comment}" if paper.comment else "**Comment:** N/A",
            "",
            "## Abstract",
            "",
            paper.summary,
        ]

        return "\n".join(output_parts)


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting parxiv-server MCP server!")
    mcp.run(transport="stdio")
