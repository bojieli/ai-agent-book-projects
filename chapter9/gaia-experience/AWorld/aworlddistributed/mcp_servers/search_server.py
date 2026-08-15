"""
Search MCP Server

This module provides MCP server functionality for performing web searches using various search engines.
It supports structured queries and returns formatted search results.

Key features:
- Perform web searches using Exa, Google, and DuckDuckGo
- Filter and format search results
- Validate and process search queries

Main functions:
- mcpsearchexa: Searches the web using Exa
- mcpsearchgoogle: Searches the web using Google
- mcpsearchduckduckgo: Searches the web using DuckDuckGo
"""

import os
import sys
import traceback
from typing import List, Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from aworld.logs.util import logger

# Initialize MCP server
mcp = FastMCP("search-server")


# Base search result model that all providers will use
class SearchResult(BaseModel):
    """Base search result model with common fields"""

    id: str
    title: str
    url: str
    snippet: str
    source: str  # Which search engine provided this result


class GoogleSearchResult(SearchResult):
    """Google-specific search result model"""

    displayLink: str = ""
    formattedUrl: str = ""
    htmlSnippet: str = ""
    htmlTitle: str = ""
    kind: str = ""
    link: str = ""


class SearchResponse(BaseModel):
    """Unified search response model"""

    query: str
    results: List[SearchResult]
    count: int
    source: str
    error: Optional[str] = None


@mcp.tool(description="Search the web using Google Custom Search API.")
def mcpsearchgoogle(
    query: str = Field(..., description="The search query string."),
    num_results: int = Field(
        10, description="Number of search results to return (default 10)."
    ),
    safe_search: bool = Field(
        True, description="Whether to enable safe search filtering."
    ),
    language: str = Field("en", description="Language code for search results."),
    country: str = Field("us", description="Country code for search results."),
) -> str:
    """
    Search the web using Google Custom Search API.

    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables to be set.
    """
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        cse_id = os.environ.get("GOOGLE_CSE_ID")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        if not cse_id:
            raise ValueError("GOOGLE_CSE_ID environment variable not set")

        # Ensure num_results is within valid range
        num_results = max(1, num_results)

        # Build the Google Custom Search API URL
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": num_results,
            "safe": "active" if safe_search else "off",
            "hl": language,
            "gl": country,
        }

        logger.info(f"Google search starts for query: {query}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        search_results = []

        if "items" in data:
            for i, item in enumerate(data["items"]):
                result = GoogleSearchResult(
                    id=f"google-{i}",
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="google",
                    displayLink=item.get("displayLink", ""),
                    formattedUrl=item.get("formattedUrl", ""),
                    htmlSnippet=item.get("htmlSnippet", ""),
                    htmlTitle=item.get("htmlTitle", ""),
                    kind=item.get("kind", ""),
                    link=item.get("link", ""),
                )
                search_results.append(result)

        return SearchResponse(
            query=query,
            results=search_results,
            count=len(search_results),
            source="google",
        ).model_dump_json()

    except Exception as e:
        logger.error(f"Google search error: {traceback.format_exc()}")
        return SearchResponse(
            query=query, results=[], count=0, source="google", error=str(e)
        ).model_dump_json()


def main():
    load_dotenv()

    print("Starting Search MCP Server...", file=sys.stderr)
    mcp.run(transport="stdio")


# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    main()


sys.modules[__name__].__call__ = __call__

# Run the server when the script is executed directly
if __name__ == "__main__":
    main()
