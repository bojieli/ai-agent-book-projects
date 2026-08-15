import base64
import json
import os
import traceback
from typing import List

from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from pydantic import Field

import logging

from utils import get_file_from_source
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("audio-server")


client = OpenAI(
    api_key=os.getenv("AUDIO_LLM_API_KEY"), 
    base_url=os.getenv("AUDIO_LLM_BASE_URL")
)

AUDIO_TRANSCRIBE = (
    "Input is a base64 encoded audio. Transcribe the audio content. "
    "Return a json string with the following format: "
    '{"audio_text": "transcribed text from audio"}'
)


def encode_audio(audio_source: str, with_header: bool = True) -> str:
    """
    Encode audio to base64 format with robust file handling

    Args:
        audio_source: URL or local file path of the audio
        with_header: Whether to include MIME type header

    Returns:
        str: Base64 encoded audio string, with MIME type prefix if with_header is True

    Raises:
        ValueError: When audio source is invalid or audio format is not supported
        IOError: When audio file cannot be read
    """
    if not audio_source:
        raise ValueError("Audio source cannot be empty")

    try:
        # Get file with validation (only audio files allowed)
        file_path, mime_type, content = get_file_from_source(
            audio_source,
            allowed_mime_prefixes=["audio/"],
            max_size_mb=200.0,  # 200MB limit for audio files
            type="audio",  # Specify type as audio to handle audio files
        )

        # Encode to base64
        audio_base64 = base64.b64encode(content).decode()

        # Format with header if requested
        final_audio = (
            f"data:{mime_type};base64,{audio_base64}" if with_header else audio_base64
        )

        # Clean up temporary file if it was created for a URL
        if file_path != os.path.abspath(audio_source) and os.path.exists(file_path):
            os.unlink(file_path)

        return final_audio

    except Exception:
        logger.error(
            f"Error encoding audio from {audio_source}: {traceback.format_exc()}"
        )
        raise


@mcp.tool(description="Transcribe the given audio in a list of filepaths or urls.")
async def mcp_transcribe_audio(
    audio_urls: List[str] = Field(
        description="The input audio in given a list of filepaths or urls."
    ),
) -> str:
    """
    Transcribe the given audio in a list of filepaths or urls.

    Args:
        audio_urls: List of audio file paths or URLs

    Returns:
        str: JSON string containing transcriptions
    """
    transcriptions = []
    for audio_url in audio_urls:
        try:
            # Get file with validation (only audio files allowed)
            file_path, _, _ = get_file_from_source(
                audio_url,
                allowed_mime_prefixes=["audio/"],
                max_size_mb=200.0,  # 200MB limit for audio files
                type="audio",  # Specify type as audio to handle audio files
            )

            # Use the file for transcription
            with open(file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model=os.getenv("AUDIO_LLM_MODEL_NAME"),
                    response_format="text",
                )
                transcriptions.append(transcription)

            # Clean up temporary file if it was created for a URL
            if file_path != os.path.abspath(audio_url) and os.path.exists(file_path):
                os.unlink(file_path)

        except Exception as e:
            logger.error(f"Error transcribing {audio_url}: {traceback.format_exc()}")
            transcriptions.append(f"Error: {str(e)}")

    logger.info(f"---get_text_by_transcribe-transcription:{transcriptions}")
    return json.dumps(transcriptions, ensure_ascii=False)


# Run the server when the script is executed directly
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    load_dotenv()
    logger.info("Starting Audio MCP Server...")
    mcp.run(transport="stdio")