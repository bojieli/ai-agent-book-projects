import asyncio
import json
import logging
import os
import sys

import aiohttp
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from mcp.server import FastMCP
from pydantic import Field

from aworld.logs.util import logger


mcp = FastMCP("picsearch-server")

async def search_single(query: str, num: int = 5) -> Optional[Dict[str, Any]]:
    """Execute a single search query, returns None on error"""
    try:
        url = os.getenv('PIC_SEARCH_URL')
        searchMode = os.getenv('PIC_SEARCH_SEARCHMODE')
        source = os.getenv('PIC_SEARCH_SOURCE')
        domain = os.getenv('PIC_SEARCH_DOMAIN')
        uid = os.getenv('PIC_SEARCH_UID')
        if not url or not searchMode or not source or not domain:
            logger.warning(f"Query failed: url, searchMode, source, domain parameters incomplete")
            return None

        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "domain": domain,
            "extParams": {
                "contentType": "llmWholeImage"
            },
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
                        logger.warning(f"Query failed: {query}, status code: {response.status}")
                        return None
                    
                    result = await response.json()
                    return result
            except aiohttp.ClientError:
                logger.warning(f"Request error: {query}")
                return None
    except Exception:
        logger.warning(f"Query exception: {query}")
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
        search_docs = result.get("searchImages", [])
        if not search_docs:
            return valid_docs
        
        # Extract required fields
        required_fields = ["title", "picUrl"]

        for doc in search_docs:
            # Check if all required fields exist and are not empty
            is_valid = True
            for field in required_fields:
                if field not in doc or not doc[field]:
                    is_valid = False
                    break
            
            if is_valid:
                # Keep only required fields
                filtered_doc = {field: doc[field] for field in required_fields}
                valid_docs.append(filtered_doc)
        
        return valid_docs
    except Exception:
        return []

@mcp.tool(description="Search Picture based on the user's input query")
async def search(
    query: str = Field(
            description="The query to search for picture"
        ),
    num: int = Field(
    5,
        description="Maximum number of results to return, default is 5"
    )
) -> Any:
    """Execute search function for a single query"""
    try:
        # Get configuration from environment variables
        env_total_num = os.getenv('PIC_SEARCH_TOTAL_NUM')
        if env_total_num and env_total_num.isdigit():
            # Force override input num parameter with environment variable
            num = int(env_total_num)
        
        # If no query provided, return empty list
        if not query:
            return json.dumps([])
        
        # Get actual number of results to return
        slice_num = os.getenv('PIC_SEARCH_SLICE_NUM')
        if slice_num and slice_num.isdigit():
            actual_num = int(slice_num)
        else:
            actual_num = num
        
        # Execute the query
        result = await search_single(query, actual_num)
        
        # Filter results
        valid_docs = filter_valid_docs(result)
        
        # Return results
        result_json = json.dumps(valid_docs, ensure_ascii=False)
        logger.info(f"Completed query: '{query}', found {len(valid_docs)} valid documents")
        logger.info(result_json)
        
        return result_json
    except Exception as e:
        # Return empty list on exception
        logger.error(f"Error processing query: {str(e)}")
        return json.dumps([])


def main():
    from dotenv import load_dotenv

    load_dotenv()

    print("Starting Audio MCP picsearch-server...", file=sys.stderr)
    mcp.run(transport="stdio")


# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    main()

sys.modules[__name__].__call__ = __call__

if __name__ == "__main__":
    main()

# if __name__ == "__main__":
#     # Configure logging
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
#
#
#     # Test single query
#     asyncio.run(search(query="Image search test"))
#
#     # Test multiple queries no longer applies