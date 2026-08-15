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

mcp = FastMCP("gen-video-server")

@mcp.tool(description="Generate video from text content")
def gen_video(prompt: str = Field(description="The text prompt to generate a video")) -> Any:
    """Generate video from text prompt"""
    api_key = os.getenv('DASHSCOPE_API_KEY')
    submit_url = os.getenv('DASHSCOPE_VIDEO_SUBMIT_URL', '')
    query_base_url = os.getenv('DASHSCOPE_QUERY_BASE_URL', '')
    
    if not api_key or not submit_url or not query_base_url:
        logger.warning("Query failed: DASHSCOPE_API_KEY, DASHSCOPE_VIDEO_SUBMIT_URL, DASHSCOPE_QUERY_BASE_URL environment variables are not set")
        return None
    
    headers = {
        'X-DashScope-Async': 'enable',
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Get parameters from environment variables or use defaults
    model = os.getenv('DASHSCOPE_VIDEO_MODEL', 'wanx2.1-t2v-turbo')
    size = os.getenv('DASHSCOPE_VIDEO_SIZE', '1280*720')
    
    # Note: Currently the API only supports generating one video at a time
    # But we keep the num parameter for API compatibility
    
    task_data = {
        "model": model,
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "size": size
        }
    }

    try:
        # Step 1: Submit task to generate video
        logger.info("Submitting task to generate video...")
        
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
        max_attempts = int(os.getenv('DASHSCOPE_VIDEO_RETRY_TIMES', 10))  # Increased default retries for video
        wait_time = int(os.getenv('DASHSCOPE_VIDEO_SLEEP_TIME', 5))      # Increased default wait time for video
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
                # Extract video URL
                video_url = query_result.get("output", {}).get("video_url")
                
                if video_url:
                    # Return as array of objects with video_url for consistency with image API
                    return json.dumps({"video_url": video_url})
                else:
                    logger.info("Video URL not found in the response")
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

    print("Starting MCP gen-video-server...", file=sys.stderr)
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
    # result = gen_video("A cat running under moonlight")
    # print("\nFinal Result:")
    # print(result)