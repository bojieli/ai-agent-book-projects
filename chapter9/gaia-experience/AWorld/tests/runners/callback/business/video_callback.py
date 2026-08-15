import json
import os
import time

import requests
from aworld.core.common import Observation, ActionResult, CallbackResult, CallbackActionType
from typing_extensions import Any

from aworld.runners.callback.decorator import reg_callback

from aworld.logs.util import logger

@reg_callback("gen_video_server__video_tasks")
def gen_video(actionResult:ActionResult) -> CallbackResult:
    try:
        calback_result = CallbackResult(
            success=True,
            result_data=None,
            callback_action_type=CallbackActionType.BYPASS
        )
        if not actionResult or not actionResult.content:
            calback_result.success = False
            return calback_result
        content = json.loads(actionResult.content)
        task_id = content.get("task_id")
        if not task_id:
            calback_result.success = False
            return calback_result
        item = gen_video_item(task_id)
        if not item:
            calback_result.success = False
            return calback_result

        calback_result.success = True
        return calback_result
    except Exception as e:
        logger.warning(f"Exception gen_video occurred: {e}")
        calback_result.success = False
        return calback_result

def gen_video_item(task_id:str) -> Any:
    if not task_id:
        return None
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('DASHSCOPE_API_KEY')
        query_base_url = os.getenv('DASHSCOPE_QUERY_BASE_URL', '')
        # Step 2: Poll for results
        max_attempts = int(os.getenv('DASHSCOPE_VIDEO_RETRY_TIMES', 10))  # Increased default retries for video
        wait_time = int(os.getenv('DASHSCOPE_VIDEO_SLEEP_TIME', 5))  # Increased default wait time for video
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
                logger.info(f"gen_video_item Task status: {task_status}, continuing to next poll...")
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
        logger.warning(f"Exception gen_video_item occurred: {e}")
        return None