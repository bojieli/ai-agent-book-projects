import os
import time
import json
import requests
import sys
import hashlib

from dotenv import load_dotenv
from mcp.server import FastMCP
from pydantic import Field
from typing_extensions import Any

from aworld.logs.util import logger

mcp = FastMCP("gen-audio-server")


def calculate_sha256(plain_text):
    """
    Calculate SHA-256 digest of a string.

    Args:
        plain_text (str): The text to digest

    Returns:
        str: Hexadecimal representation of the digest
    """
    try:
        # Create SHA-256 hash object
        sha256 = hashlib.sha256()

        # Update with the bytes of the plain text (UTF-8 encoded)
        sha256.update(plain_text.encode('utf-8'))

        # Get the digest in bytes
        digest_bytes = sha256.digest()

        # Convert each byte to hexadecimal and join
        hex_digest = ''.join([f'{b:02x}' for b in digest_bytes])

        return hex_digest
    except Exception as e:
        logger.warning(f"Error calculating SHA-256 digest: {e}")
        return ""


def generate_headers(app_key, secret):
    """Generate headers with fresh timestamp and digest"""
    timestamp = str(int(time.time() * 1000))
    plain_text = f"{app_key}_{secret}_{timestamp}"
    digest = calculate_sha256(plain_text)

    return {
        'Content-Type': 'application/json',
        'Alipay-Mf-Appkey': app_key,
        'Alipay-Mf-Digest': digest,
        'Alipay-Mf-Timestamp': timestamp
    }


@mcp.tool(description="Generate audio from text content")
def gen_audio(content: str = Field(description="The text content to convert to audio")) -> Any:
    """Generate audio from text content using TTS service"""
    task_url = os.getenv('AUDIO_TASK_URL')
    query_url = os.getenv('AUDIO_QUERY_URL')
    app_key = os.getenv('AUDIO_APP_KEY')
    secret = os.getenv('AUDIO_SECRET')
    if not (task_url and query_url and app_key and secret):
        logger.warning(f"Query failed: task_url, query_url, app_key, secret parameters incomplete")
        return None

    # Generate initial headers
    headers = generate_headers(app_key, secret)

    sample_rate = os.getenv('AUDIO_SAMPLE_RATE', '16000')
    audio_format = os.getenv('AUDIO_AUDIO_FORMAT', 'wav')
    tts_voice = os.getenv('AUDIO_TTS_VOICE', 'DBCNF245')
    tts_speech_rate = os.getenv('AUDIO_TTS_SPEECH_RATE', '0')
    tts_volume = os.getenv('AUDIO_TTS_VOLUME', '50')
    tts_pitch = os.getenv('AUDIO_TTS_PITCH', '0')
    voice_type = os.getenv('AUDIO_VOICE_TYPE', 'VOICE_CLONE_LAM')

    # task_data
    task_data = {
        "sample_rate": sample_rate,
        "audio_format": audio_format,
        "tts_voice": tts_voice,
        "tts_speech_rate": tts_speech_rate,
        "tts_volume": tts_volume,
        "tts_pitch": tts_pitch,
        "tts_text": content,
        "voice_type": voice_type,
    }

    try:
        # Step 1: Submit task to generate audio

        response = requests.post(task_url, headers=headers, json=task_data)

        if response.status_code != 200:
            return None

        result = response.json()

        # Check if task was successfully submitted
        if not result.get("success"):
            return None

        # Extract task ID
        task_id = result.get("data")
        if not task_id:
            return None

        logger.info(f"Task submitted successfully. Task ID: {task_id}")

        # Step 2: Poll for results
        max_attempts = int(os.getenv('AUDIO_RETRY_TIMES', 10))
        wait_time = int(os.getenv('AUDIO_SLEEP_TIME', 5))
        query_url = query_url + f"?async_task_id={task_id}"

        for attempt in range(max_attempts):
            # Wait before polling
            time.sleep(wait_time)
            logger.info(f"Polling attempt {attempt + 1}/{max_attempts}...")

            # Generate fresh headers for each poll request
            query_headers = generate_headers(app_key, secret)

            # Poll for results
            query_response = requests.post(query_url, headers=query_headers)

            if query_response.status_code != 200:
                logger.info(f"Poll request failed with status code {query_response.status_code}")
                continue

            try:
                query_result = query_response.json()
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response as JSON: {e}")
                continue

            # Check if processing is complete
            if query_result.get("success") and query_result.get("data", {}).get("status") == "ST_SUCCESS":
                # Extract audio URL based on the correct JSON structure
                # Navigate through the nested structure: data -> result -> result -> audioUrl
                audio_url = query_result.get("data", {}).get("result", {}).get("result", {}).get("audioUrl")

                if audio_url:
                    return json.dumps({"audio_data": audio_url})
                else:
                    logger.info("Audio URL not found in the response")
                    return None
            elif query_result.get("success") and query_result.get("data", {}).get("status") == "ST_RUNNING":
                # If still running, continue to next polling attempt
                logger.info("Task still running, continuing to next poll...")
                continue
            else:
                # Any other status, return None
                logger.warning(f"Unexpected status: {query_result.get('data', {}).get('status')}")
                return None

        # If we get here, polling timed out
        logger.warning("Polling timed out after maximum attempts")
        return None

    except Exception as e:
        import traceback
        logger.warning(f"Exception occurred: {e}")
        return None


def main():
    from dotenv import load_dotenv

    load_dotenv()

    print("Starting Audio MCP gen-audio-server...", file=sys.stderr)
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
    # result = gen_audio("hello ,this is test")
    # print("\nFinal Result:")
    # print(result)