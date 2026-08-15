import asyncio
import json
import logging
import os
import traceback
from typing import List, Dict, Any, Optional, Union

import aiohttp
import requests
from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field
from tavily import TavilyClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

mcp = FastMCP("readweb-server")


def filter_valid_images(result: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                valid_docs.append({
                    "type": "IMAGE",
                    "title": filtered_doc.get("title", ""),
                    "url": filtered_doc.get("picUrl", "")
                })

        return valid_docs
    except Exception:
        return []


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

@mcp.tool(
    description="提取并将网页内容转换为清晰、可读的markdown格式。非常适合阅读文章、文档、博客文章或任何网页内容。当您需要分析网站的文本内容、绕过付费墙或获取结构化数据时，请使用此工具。")
async def read_url(
        url: str = Field(
            description="一个强大的网页内容提取工具，可以从指定URL检索和处理原始内容，非常适合数据收集、内容分析和研究任务。"
        ),
        include_images: bool = Field(
            False,
            description="在响应中包含从URL提取的图片列表"
        )
) -> Union[str, TextContent]:
    try:
        if not url:
            return TextContent(
                type="text",
                text="",  # Empty string instead of None
                **{"metadata": {}}  # Pass as additional fields
            )
        urls = [url]
        TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
        if not TAVILY_API_KEY:
            return TextContent(
                type="text",
                text="",  # Empty string instead of None
                **{"metadata": {}}  # Pass as additional fields
            )
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        response = tavily_client.extract(urls=urls, include_images=include_images,format="text")
        text_extracted_content = ""

        if response and isinstance(response, dict):
            results = response.get("results", [])
            if results and isinstance(results, list) and len(results) > 0:
                first_result = results[0]
                if isinstance(first_result, dict):
                    raw_content = first_result.get("raw_content")
                    if raw_content and isinstance(raw_content, str):
                        text_extracted_content = raw_content
        markdown_response = tavily_client.extract(urls=urls, include_images=include_images, include_favicon=False,
                                                  format="markdown")
        markdown_extracted_content = ""
        if markdown_response and isinstance(markdown_response, dict):
            results = markdown_response.get("results", [])
            if results and isinstance(results, list) and len(results) > 0:
                first_result = results[0]
                if isinstance(first_result, dict):
                    raw_content = first_result.get("raw_content")
                    if raw_content and isinstance(raw_content, str):
                        markdown_extracted_content = raw_content

        search_output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": markdown_extracted_content
        }
        # Initialize TextContent with additional parameters
        return TextContent(
            type="text",
            text=text_extracted_content,
            **{"metadata": search_output_dict}  # Pass processed data as metadata
        )
    except Exception as e:
        # Handle errors
        logging.error(f"Search error: {e}")
        # Initialize TextContent with additional parameters
        return TextContent(
            type="text",
            text="",  # Empty string instead of None
            **{"metadata": {}}  # Pass as additional fields
        )


async def search_image_single(query: str, num: int = 5) -> Optional[Dict[str, Any]]:
    """Execute a single search query, returns None on error"""
    try:
        url = os.getenv('PIC_SEARCH_URL')
        searchMode = os.getenv('PIC_SEARCH_SEARCHMODE')
        source = os.getenv('PIC_SEARCH_SOURCE')
        domain = os.getenv('PIC_SEARCH_DOMAIN')
        uid = os.getenv('PIC_SEARCH_UID')
        if not url or not searchMode or not source or not domain:
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
                        return None

                    result = await response.json()
                    return result
            except aiohttp.ClientError:
                return None
    except Exception:
        return None




if __name__ == "__main__":
    load_dotenv(override=True)
    logger.info("Starting readweb-server MCP server!")
    mcp.run(transport="stdio")
