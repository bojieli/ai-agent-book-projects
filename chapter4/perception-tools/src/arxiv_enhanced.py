"""
Enhanced ArXiv tools with download and details.
Based on AWorld parxiv-server complete implementation.
"""
import hashlib
import json
import logging
import os
import re
import traceback
from typing import Union

import arxiv
import httpx
from dotenv import load_dotenv
from mcp.types import TextContent

from base import ActionResponse


load_dotenv()


async def get_paper_details(
    paper_id: str
) -> Union[str, TextContent]:
    """
    Get detailed information about an ArXiv paper.
    
    Args:
        paper_id: ArXiv paper ID (e.g., '2301.07041')
        
    Returns:
        TextContent with paper details
    """
    try:
        clean_id = re.sub(r"^arxiv:", "", paper_id, flags=re.IGNORECASE).strip()
        
        logging.info(f"📄 Getting paper details: {clean_id}")
        
        search = arxiv.Search(id_list=[clean_id])
        paper = next(arxiv.Client().results(search), None)
        
        if not paper:
            raise ValueError(f"Paper not found: {clean_id}")
        
        result = {
            "entry_id": paper.entry_id,
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "published": paper.published.isoformat(),
            "updated": paper.updated.isoformat() if paper.updated else None,
            "categories": paper.categories,
            "primary_category": paper.primary_category,
            "pdf_url": paper.pdf_url,
            "doi": paper.doi,
            "journal_ref": paper.journal_ref
        }
        
        logging.info(f"✅ Retrieved paper: {paper.title}")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"paper_id": clean_id}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Failed to get paper details: {str(e)}"
        logging.error(f"ArXiv error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "arxiv_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def download_paper(
    paper_id: str,
    download_dir: str = "."
) -> Union[str, TextContent]:
    """
    Download ArXiv paper PDF.
    
    Args:
        paper_id: ArXiv paper ID
        download_dir: Directory to save PDF
        
    Returns:
        TextContent with download result
    """
    try:
        from pathlib import Path
        
        clean_id = re.sub(r"^arxiv:", "", paper_id, flags=re.IGNORECASE).strip()
        
        logging.info(f"📥 Downloading paper: {clean_id}")
        
        if not re.fullmatch(
            r"(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7}|\d{4}\.\d{4,5})(?:v\d+)?",
            clean_id,
            flags=re.IGNORECASE,
        ):
            raise ValueError(f"Invalid arXiv paper ID: {clean_id}")

        # Fetch the canonical PDF directly. Re-querying the Atom metadata API
        # for every ID introduces an unrelated failure point and triggers its
        # batch-query backoff during the three-paper experiment.
        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)
        filename = f"{clean_id.replace('/', '_')}.pdf"
        file_path = download_path / filename
        temporary_path = download_path / f".{filename}.part"
        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        async with httpx.AsyncClient(
            timeout=180,
            follow_redirects=True,
            headers={"User-Agent": "ai-agent-book-experiment/4.6"},
        ) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            content = response.content
        if len(content) <= 1000 or not content.startswith(b"%PDF-"):
            raise ValueError("arXiv response was not a substantive PDF")
        temporary_path.write_bytes(content)
        os.replace(temporary_path, file_path)

        result = {
            "paper_id": clean_id,
            "file_path": str(file_path),
            "file_size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "pdf_url": pdf_url,
            "content_type": response.headers.get("content-type"),
        }

        logging.info(f"✅ Downloaded: {len(content)} bytes")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"paper_id": clean_id}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        action_response = ActionResponse(
            success=False,
            message=f"Download failed: {str(e)}",
            metadata={"error_type": "download_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def get_arxiv_categories() -> Union[str, TextContent]:
    """
    Get list of ArXiv subject categories.
    
    Returns:
        TextContent with categories
    """
    categories = {
        "cs": "Computer Science",
        "math": "Mathematics",
        "physics": "Physics",
        "astro-ph": "Astrophysics",
        "cond-mat": "Condensed Matter",
        "q-bio": "Quantitative Biology",
        "q-fin": "Quantitative Finance",
        "stat": "Statistics",
        "econ": "Economics",
        "eess": "Electrical Engineering"
    }
    
    result = {
        "categories": categories,
        "count": len(categories)
    }
    
    action_response = ActionResponse(
        success=True,
        message=result,
        metadata={"total_categories": len(categories)}
    )
    
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump())
    )
