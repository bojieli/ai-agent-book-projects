import os
import time
import json
import requests
import sys

from dotenv import load_dotenv
from mcp.server import FastMCP
from pydantic import Field
from typing_extensions import Any

from aworld.logs.util import logger

mcp = FastMCP("gen-pic-server")


@mcp.tool(description="Generate picture from text content")
def gen_picture(prompt: str = Field(description="The text prompt to generate an image"),
                num: int = Field(0,
                                 description="Number of images to generate, 0 means use environment variable")) -> Any:
    """Generate picture from text prompt"""
    api_key = os.getenv('DASHSCOPE_API_KEY')
    submit_url = os.getenv('DASHSCOPE_SUBMIT_URL', '')
    query_base_url = os.getenv('DASHSCOPE_QUERY_BASE_URL', '')

    if not api_key or not submit_url or not query_base_url:
        logger.warning(
            "Query failed: DASHSCOPE_API_KEY,DASHSCOPE_SUBMIT_URL,DASHSCOPE_QUERY_BASE_URL environment variable is not set")
        return None

    headers = {
        'X-DashScope-Async': 'enable',
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Get parameters from environment variables or use defaults
    model = os.getenv('DASHSCOPE_MODEL', 'wanx2.1-t2i-turbo')
    size = os.getenv('DASHSCOPE_SIZE', '1024*1024')

    # Use num parameter if provided (>0), otherwise use environment variable
    n = num if num > 0 else int(os.getenv('DASHSCOPE_N', '1'))

    task_data = {
        "model": model,
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "size": size,
            "n": n
        }
    }

    try:
        # Step 1: Submit task to generate image
        logger.info("Submitting task to generate image...")

        response = requests.post(submit_url, headers=headers, json=task_data)

        if response.status_code != 200:
            logger.warning(f"Task submission failed with status code {response.status_code}")
            return None

        result = response.json()

        # Check if task was successfully submitted
        if not result.get("output") or not result.get("output").get("task_id"):
            logger.warning("Failed to get task_id from response")
            return None

        # Extract task ID
        task_id = result.get("output").get("task_id")
        logger.info(f"Task submitted successfully. Task ID: {task_id}")

        # Step 2: Poll for results
        max_attempts = int(os.getenv('DASHSCOPE_RETRY_TIMES', 10))
        wait_time = int(os.getenv('DASHSCOPE_SLEEP_TIME', 5))
        query_url = f"{query_base_url}{task_id}"

        for attempt in range(max_attempts):
            # Wait before polling
            time.sleep(wait_time)
            logger.info(f"Polling attempt {attempt + 1}/{max_attempts}...")

            # Poll for results
            query_response = requests.get(query_url, headers={'Authorization': f'Bearer {api_key}'})

            if query_response.status_code != 200:
                logger.info(f"Poll request failed with status code {query_response.status_code}")
                continue

            try:
                query_result = query_response.json()
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response as JSON: {e}")
                continue

            # Check task status
            task_status = query_result.get("output", {}).get("task_status")

            if task_status == "SUCCEEDED":
                # Extract image URLs
                results = query_result.get("output", {}).get("results", [])
                if results:
                    # Create a simple array of objects with image_url
                    image_urls = []
                    for result in results:
                        if "url" in result:
                            image_urls.append({"image_url": result["url"]})

                    if image_urls:
                        return json.dumps(image_urls)
                    else:
                        logger.info("No valid image URLs found in the response")
                        return None
                else:
                    logger.info("No results found in the response")
                    return None
            elif task_status in ["PENDING", "RUNNING"]:
                # If still running, continue to next polling attempt
                logger.info(f"Task status: {task_status}, continuing to next poll...")
                continue
            elif task_status == "FAILED":
                logger.warning("Task failed")
                return None
            else:
                # Any other status, return None
                logger.warning(f"Unexpected status: {task_status}")
                return None

        # If we get here, polling timed out
        logger.warning("Polling timed out after maximum attempts")
        return None

    except Exception as e:
        logger.warning(f"Exception occurred: {e}")
        return None


def main():
    from dotenv import load_dotenv

    load_dotenv()

    print("Starting MCP gen-pic-server...", file=sys.stderr)
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
    # For testing without MCP
    # result = gen_picture("sunflower", 2)
    # print("\nFinal Result:")
    # print(result)