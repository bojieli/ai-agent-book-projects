"""
Search MCP Server

This module provides MCP server functionality for performing web searches using various search engines.
It supports structured queries and returns LLM-friendly formatted search results.

Key features:
- Perform web searches using Google Custom Search API
- Filter and format search results for LLM consumption
- Validate and process search queries with metadata tracking

Main functions:
- mcp_search_google: Searches the web using Google Custom Search API
- mcp_get_search_capabilities: Returns information about search service capabilities
"""

import json
import os
import time
import traceback

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from aworld.logs.util import Color
from examples.gaia.mcp_collections.base import ActionArguments, ActionCollection, ActionResponse


class SearchResult(BaseModel):
    """Individual search result with structured data."""

    id: str
    title: str
    url: str
    snippet: str
    source: str
    display_link: str | None = None
    formatted_url: str | None = None


class SearchMetadata(BaseModel):
    """Metadata for search operation results."""

    query: str
    search_engine: str
    total_results: int
    search_time: float | None = None
    language: str = "en"
    country: str = "us"
    safe_search: bool = True
    error_type: str | None = None
    api_quota_used: bool = False


class SearchCollection(ActionCollection):
    """MCP service for web search operations using various search engines.

    Provides comprehensive web search capabilities including:
    - Google Custom Search API integration
    - LLM-friendly result formatting
    - Search result filtering and validation
    - Metadata tracking for search operations
    - Error handling and quota management
    """

    def __init__(self, arguments: ActionArguments) -> None:
        super().__init__(arguments)

        # Load environment variables
        load_dotenv()

        # Validate required API credentials
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")

        # Log initialization status
        self._color_log("Search service initialized", Color.green, "debug")

        if self.google_api_key and self.google_cse_id:
            self._color_log("Google Search API credentials found", Color.blue, "debug")
        else:
            self._color_log("Google Search API credentials missing - some features may be unavailable", Color.yellow)

    def _format_search_results_for_llm(self, results: list[SearchResult], query: str) -> str:
        """Format search results to be LLM-friendly.

        Args:
            results: List of search results
            query: Original search query

        Returns:
            Formatted string suitable for LLM consumption
        """
        if not results:
            return f"No search results found for query: '{query}'"

        formatted_parts = [f"# Search Results for: '{query}'", f"Found {len(results)} results:\n"]

        for i, result in enumerate(results, 1):
            result_section = [
                f"## Result {i}: {result.title}",
                f"**URL:** {result.url}",
                f"**Source:** {result.source}",
            ]

            if result.display_link:
                result_section.append(f"**Domain:** {result.display_link}")

            result_section.append(f"**Summary:** {result.snippet}")
            result_section.append("")  # Empty line for spacing

            formatted_parts.append("\n".join(result_section))

        return "\n".join(formatted_parts)

    def _validate_search_parameters(self, query: str, num_results: int) -> tuple[str, int]:
        """Validate and normalize search parameters.

        Args:
            query: Search query string
            num_results: Number of results requested

        Returns:
            Tuple of (validated_query, validated_num_results)

        Raises:
            ValueError: If parameters are invalid
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        # Normalize query
        validated_query = query.strip()

        # Validate and clamp num_results
        validated_num_results = max(1, min(num_results, 10))  # Google CSE limit is 10

        return validated_query, validated_num_results

    def mcp_search_google(
        self,
        query: str = Field(description="The search query string to search for"),
        num_results: int = Field(default=5, description="Number of search results to return (1-10, default: 5)"),
        safe_search: bool = Field(default=True, description="Whether to enable safe search filtering"),
        language: str = Field(default="en", description="Language code for search results (e.g., 'en', 'es', 'fr')"),
        country: str = Field(default="us", description="Country code for search results (e.g., 'us', 'uk', 'ca')"),
        output_format: str = Field(default="json", description="Output format: 'markdown', 'json', or 'text'"),
    ) -> ActionResponse:
        """Search the web using Google Custom Search API.

        This tool provides comprehensive web search capabilities with:
        - Google Custom Search API integration
        - Configurable result count and filtering
        - Safe search and localization options
        - LLM-optimized result formatting
        - Detailed metadata tracking

        Args:
            query: The search query string
            num_results: Number of results to return (1-10)
            safe_search: Enable safe search filtering
            language: Language code for results
            country: Country code for results
            output_format: Format for the response

        Returns:
            ActionResponse with formatted search results and metadata
        """
        if isinstance(query, FieldInfo):
            query = query.default
        if isinstance(num_results, FieldInfo):
            num_results = num_results.default
        if isinstance(safe_search, FieldInfo):
            safe_search = safe_search.default
        if isinstance(language, FieldInfo):
            language = language.default
        if isinstance(country, FieldInfo):
            country = country.default
        if isinstance(output_format, FieldInfo):
            output_format = output_format.default

        try:
            # Validate API credentials
            if not self.google_api_key or not self.google_cse_id:
                return ActionResponse(
                    success=False,
                    message=(
                        "Google Search API credentials not configured. "
                        "Please set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."
                    ),
                    metadata={"error_type": "missing_credentials"},
                )

            # Validate parameters
            validated_query, validated_num_results = self._validate_search_parameters(query, num_results)

            self._color_log(f"🔍 Searching Google for: '{validated_query}'", Color.cyan)

            # Prepare API request
            start_time = time.time()

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": validated_query,
                "num": validated_num_results,
                "safe": "active" if safe_search else "off",
                "hl": language,
                "gl": country,
            }

            # Make API request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            search_time = time.time() - start_time
            data = response.json()

            # Parse search results
            search_results = []
            if "items" in data:
                for i, item in enumerate(data["items"]):
                    result = SearchResult(
                        id=f"google-{i}",
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="google",
                        display_link=item.get("displayLink", ""),
                        formatted_url=item.get("formattedUrl", ""),
                    )
                    search_results.append(result)

            # Format results based on requested format
            if "json" == "json":
                formatted_content = {
                    "query": validated_query,
                    "results": [result.model_dump() for result in search_results],
                    "count": len(search_results),
                }

                message_content = formatted_content
            elif output_format.lower() == "text":
                if search_results:
                    result_lines = []
                    for i, result in enumerate(search_results, 1):
                        result_lines.append(f"{i}. {result.title}")
                        result_lines.append(f"   URL: {result.url}")
                        result_lines.append(f"   Summary: {result.snippet}")
                        result_lines.append("")  # Empty line
                    message_content = "\n".join(result_lines)
                else:
                    message_content = f"No results found for: {validated_query}"
            else:  # markdown (default)
                message_content = self._format_search_results_for_llm(search_results, validated_query)

            # Prepare metadata
            metadata = SearchMetadata(
                query=validated_query,
                search_engine="google",
                total_results=len(search_results),
                search_time=search_time,
                language=language,
                country=country,
                safe_search=safe_search,
                api_quota_used=True,
            )

            self._color_log(f"✅ Found {len(search_results)} results in {search_time:.2f}s", Color.green)

            return ActionResponse(success=True, message=message_content, metadata=metadata.model_dump())

        except requests.exceptions.RequestException as e:
            error_msg = f"Google Search API request failed: {str(e)}"
            self.logger.error(f"Search API error: {traceback.format_exc()}")

            metadata = SearchMetadata(
                query=query, search_engine="google", total_results=0, error_type="api_request_failed"
            )

            self._color_log(f"❌ {error_msg}", Color.red)

            return ActionResponse(success=False, message=error_msg, metadata=metadata.model_dump())

        except ValueError as e:
            error_msg = f"Invalid search parameters: {str(e)}"

            metadata = SearchMetadata(
                query=query, search_engine="google", total_results=0, error_type="invalid_parameters"
            )

            self._color_log(f"❌ {error_msg}", Color.red)

            return ActionResponse(success=False, message=error_msg, metadata=metadata.model_dump())

        except Exception as e:
            error_msg = f"Search operation failed: {str(e)}"
            error_trace = traceback.format_exc()

            self.logger.error(f"Unexpected search error: {error_trace}")

            metadata = SearchMetadata(
                query=query, search_engine="google", total_results=0, error_type="unexpected_error"
            )

            self._color_log(f"❌ {error_msg}", Color.red)

            return ActionResponse(
                success=False, message=f"{error_msg}\n\nError details: {error_trace}", metadata=metadata.model_dump()
            )

    def mcp_get_search_capabilities(self) -> ActionResponse:
        """Get information about search service capabilities and configuration.

        Returns:
            ActionResponse with search service capabilities and current configuration
        """
        capabilities = {
            "search_engines": ["Google Custom Search API"],
            "supported_features": [
                "Web search with customizable result count",
                "Safe search filtering",
                "Language and country localization",
                "Multiple output formats (markdown, json, text)",
                "LLM-optimized result formatting",
                "Detailed metadata tracking",
            ],
            "supported_formats": ["markdown", "json", "text"],
            "configuration": {
                "google_api_configured": bool(self.google_api_key and self.google_cse_id),
                "max_results_per_query": 10,
                "default_language": "en",
                "default_country": "us",
                "safe_search_default": True,
            },
            "limitations": [
                "Google CSE has daily quota limits",
                "Maximum 10 results per query",
                "Requires valid API credentials",
            ],
        }

        formatted_info = f"""# Search Service Capabilities

        ## Available Search Engines
        {chr(10).join(f"- {engine}" for engine in capabilities["search_engines"])}

        ## Features
        {chr(10).join(f"- {feature}" for feature in capabilities["supported_features"])}

        ## Supported Output Formats
        {chr(10).join(f"- {fmt}" for fmt in capabilities["supported_formats"])}

        ## Current Configuration
        - **Google API Configured:** {capabilities["configuration"]["google_api_configured"]}
        - **Max Results Per Query:** {capabilities["configuration"]["max_results_per_query"]}
        - **Default Language:** {capabilities["configuration"]["default_language"]}
        - **Default Country:** {capabilities["configuration"]["default_country"]}
        - **Safe Search Default:** {capabilities["configuration"]["safe_search_default"]}

        ## Limitations
        {chr(10).join(f"- {limitation}" for limitation in capabilities["limitations"])}
        """

        return ActionResponse(success=True, message=formatted_info, metadata=capabilities)


# Example usage and entry point
if __name__ == "__main__":
    load_dotenv()

    # Default arguments for testing
    args = ActionArguments(
        name="search_service",
        transport="stdio",
        workspace=os.getenv("AWORLD_WORKSPACE", "~"),
    )

    # Initialize and run the search service
    try:
        service = SearchCollection(args)
        service.run()
    except Exception as e:
        print(f"An error occurred: {e}: {traceback.format_exc()}")
