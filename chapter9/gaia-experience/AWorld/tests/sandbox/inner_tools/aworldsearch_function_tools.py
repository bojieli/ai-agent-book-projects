# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import asyncio
import json
import logging
import os
import pprint
from typing import List, Dict, Any, Optional, Union

import aiohttp
from mcp.types import TextContent
from pydantic import Field

from aworld.tools import FunctionTools

# Create function tools server
function = FunctionTools("aworldsearch_server",
                         description="Search service for AWorld")

async def search_single(query: str, num: int = 5) -> Optional[Dict[str, Any]]:
    """Execute a single search query, returns None on error"""
    try:
        url = os.getenv('AWORLD_SEARCH_URL')
        searchMode = os.getenv('AWORLD_SEARCH_SEARCHMODE')
        source = os.getenv('AWORLD_SEARCH_SOURCE')
        domain = os.getenv('AWORLD_SEARCH_DOMAIN')
        uid = os.getenv('AWORLD_SEARCH_UID')
        if not url or not searchMode or not source or not domain:
            logging.warning(f"Query failed: url, searchMode, source, domain parameters incomplete")
            return None

        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "domain": domain,
            "extParams": {},
            "page": 0,
            "pageSize": num,
            "query": query,
            "searchMode": searchMode,
            "source": source,
            "userId": uid
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        logging.warning(f"Query failed: {query}, status code: {response.status}")
                        return None

                    result = await response.json()
                    return result
            except aiohttp.ClientError:
                logging.warning(f"Request error: {query}")
                return None
    except Exception:
        logging.warning(f"Query exception: {query}")
        return None


def filter_valid_docs(result: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter valid document results, returns empty list if input is None"""
    if result is None:
        return []

    try:
        valid_docs = []

        # Check success field
        if not result.get("success"):
            return valid_docs

        # Check searchDocs field
        search_docs = result.get("searchDocs", [])
        if not search_docs:
            return valid_docs

        # Extract required fields
        required_fields = ["title", "docAbstract", "url", "doc"]

        for doc in search_docs:
            # Check if all required fields exist and are non-empty
            is_valid = True
            for field in required_fields:
                if field not in doc or not doc[field]:
                    is_valid = False
                    break

            if is_valid:
                # Only keep required fields
                filtered_doc = {field: doc[field] for field in required_fields}
                valid_docs.append(filtered_doc)

        return valid_docs
    except Exception:
        return []


@function.tool(description="Search based on the user's input query list")
async def search(
        query_list: List[str] = Field(
            description="List format, queries to search for"
        ),
        num: int = Field(
            5,
            description="Maximum number of results per query, default is 5, please keep the total results within 15"
        )
) -> Union[str, TextContent]:
    """Execute main search function, supports single query or query list"""
    try:
        # Get configuration from environment variables
        env_total_num = os.getenv('AWORLD_SEARCH_TOTAL_NUM')
        if env_total_num and env_total_num.isdigit():
            # Use environment variable to forcibly override the input num parameter
            num = int(env_total_num)

        # If no query is provided, return empty list
        if not query_list:
            # Initialize TextContent with additional parameters
            return TextContent(
                type="text",
                text="",  # Empty string instead of None
                **{"metadata": {}}  # Pass as additional field
            )

        # When query count >=3 or slice_num is set, use the corresponding value
        slice_num = os.getenv('AWORLD_SEARCH_SLICE_NUM')
        if slice_num and slice_num.isdigit():
            actual_num = int(slice_num)
        else:
            actual_num = 2 if len(query_list) >= 3 else num

        # Execute all queries in parallel
        tasks = [search_single(q, actual_num) for q in query_list]
        raw_results = await asyncio.gather(*tasks)

        # Filter and merge results
        all_valid_docs = []
        for result in raw_results:
            valid_docs = filter_valid_docs(result)
            all_valid_docs.extend(valid_docs)

        # If no valid results found, return empty list
        if not all_valid_docs:
            # Initialize TextContent with additional parameters
            return TextContent(
                type="text",
                text="",  # Empty string instead of None
                **{"metadata": {}}  # Pass as additional field
            )

        # Format results as JSON
        result_json = json.dumps(all_valid_docs, ensure_ascii=False)

        # Create dictionary structure directly
        combined_query = ",".join(query_list)

        search_items = []
        # Use dictionary for URL deduplication
        url_dict = {}
        for doc in all_valid_docs:
            url = doc.get("url", "")
            if url not in url_dict:
                url_dict[url] = {
                    "title": doc.get("title", ""),
                    "url": url,
                    "snippet": doc.get("doc", "")[:100] + "..." if len(doc.get("doc", "")) > 100 else doc.get("doc", ""),
                    "content": doc.get("doc", "")  # Map doc field to content
                }
        
        # Convert dictionary values to list
        search_items = list(url_dict.values())
        
        search_output_dict = {
            "artifact_type": "WEB_PAGES",
            "artifact_data": {
                "query": combined_query,
                "results": search_items
            }
        }

        # Log results
        logging.info(f"Completed {len(query_list)} queries, found {len(all_valid_docs)} valid documents")

        # Initialize TextContent with additional parameters
        return TextContent(
            type="text",
            text=result_json,
            **{"metadata": search_output_dict}  # Pass processed data as metadata
        )
    except Exception as e:
        # Handle errors
        logging.error(f"Search error: {e}")
        # Initialize TextContent with additional parameters
        return TextContent(
            type="text",
            text="",  # Empty string instead of None
            **{"metadata": {}}  # Pass as additional field
        )

# Test code
if __name__ == "__main__":
    import pprint
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # List all tools
    print("Tool list:")
    tools = function.list_tools()
    print(tools)
    res = function.call_tool("search", {"query_list": ["Tencent financial report", "Baidu financial report", "Alibaba financial report"],})
    print(res)
    # for tool in tools:
    #     print(f"Tool name: {tool.name}")
    #     print(f"Tool description: {tool.description}")
    #     print(f"Parameter schema: {tool.inputSchema}")
    #     if tool.annotations:
    #         print(f"Annotation information:")
    #         print(f"  - Title: {tool.annotations.title}")
    #     print()