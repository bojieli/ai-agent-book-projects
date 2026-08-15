"""
Image MCP Server

This module provides MCP server functionality for image processing and analysis.
It handles image encoding, optimization, and various image analysis tasks such as
OCR (Optical Character Recognition) and visual reasoning.

The server supports both local image files and remote image URLs with proper validation
and handles various image formats including JPEG, PNG, GIF, and others.

Main functions:
- encode_images: Encodes images to base64 format with optimization
- optimize_image: Resizes and optimizes images for better performance
- Various MCP tools for image analysis and processing
"""


import base64
import os
from io import BytesIO
from typing import Any, Dict, List

import logging

from PIL import Image
from pydantic import Field

from utils import get_file_from_source

from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("image-server")


IMAGE_OCR = (
    "Input is a base64 encoded image. Read text from image if present. "
    "Return a json string with the following format: "
    '{"image_text": "text from image"}'
)

IMAGE_REASONING = (
    "Input is a base64 encoded image. Given user's task: {task}, "
    "solve it following the guide line:\n"
    "1. Careful visual inspection\n"
    "2. Contextual reasoning\n"
    "3. Text transcription where relevant\n"
    "4. Logical deduction from visual evidence\n"
    "Return a json string with the following format: "
    '{"image_reasoning_result": "reasoning result given task and image"}'
)


def optimize_image(image_data: bytes, max_size: int = 1024) -> bytes:
    """
    Optimize image by resizing if needed

    Args:
        image_data: Raw image data
        max_size: Maximum dimension size in pixels

    Returns:
        bytes: Optimized image data

    Raises:
        ValueError: When image cannot be processed
    """
    try:
        image = Image.open(BytesIO(image_data))

        # Resize if image is too large
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Save to buffer
        buffered = BytesIO()
        image_format = image.format if image.format else "JPEG"
        image.save(buffered, format=image_format)
        return buffered.getvalue()

    except Exception as e:
        logger.warning(f"Failed to optimize image: {str(e)}")
        return image_data  # Return original data if optimization fails


def encode_images(image_sources: List[str], with_header: bool = True) -> List[str]:
    """
    Encode images to base64 format with robust file handling

    Args:
        image_sources: List of URLs or local file paths of images
        with_header: Whether to include MIME type header

    Returns:
        List[str]: Base64 encoded image strings, with MIME type prefix if with_header is True

    Raises:
        ValueError: When image source is invalid or image format is not supported
    """
    if not image_sources:
        raise ValueError("Image sources cannot be empty")

    images = []
    for image_source in image_sources:
        try:
            # Get file with validation (only image files allowed)
            file_path, mime_type, content = get_file_from_source(
                image_source,
                allowed_mime_prefixes=["image/"],
                max_size_mb=30.0,  # 10MB limit for images
                type="image",
            )

            # Optimize image
            optimized_content = optimize_image(content)

            # Encode to base64
            image_base64 = base64.b64encode(optimized_content).decode()

            # Format with header if requested
            final_image = (
                f"data:{mime_type};base64,{image_base64}"
                if with_header
                else image_base64
            )

            images.append(final_image)

            # Clean up temporary file if it was created for a URL
            if file_path != os.path.abspath(image_source) and os.path.exists(file_path):
                os.unlink(file_path)

        except Exception as e:
            logger.error(f"Error encoding image from {image_source}: {str(e)}")
            raise

    return images

def image_to_base64(image_path):
    try:
        with Image.open(image_path) as image:
            buffered = BytesIO()
            image_format = image.format if image.format else "JPEG"
            image.save(buffered, format=image_format)
            image_bytes = buffered.getvalue()
            base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
            return base64_encoded
    except Exception as e:
        logger.error(f"Base64 error: {e}", exc_info=True)
        return None


def create_image_contents(prompt: str, image_base64: List[str]) -> List[Dict[str, Any]]:
    """Create uniform image format for querying llm."""
    content = [
        {"type": "text", "text": prompt},
    ]
    content.extend(
        [{"type": "image_url", "image_url": {"url": url}} for url in image_base64]
    )
    return content


@mcp.tool(description="Solve the question by careful reasoning given the image(s) in given local filepath or url, including reasoning, ocr, etc.")
def mcp_image_recognition(
    image_urls: List[str] = Field(
        description="The input image(s) in given a list of local filepaths or urls."
    ),
    question: str = Field(description="The question to ask."),
) -> str:
    """solve the question by careful reasoning given the image(s) in given filepath or url."""

    try:
        image_base64 = image_to_base64(image_urls[0])
        logger.info(f"image_url: {image_urls[0]}")
        reasoning_prompt = question
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": 
                [
                    {"type": "text", "text": reasoning_prompt},
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                ],
                },
            ]
        
        client = OpenAI(
            api_key=os.getenv("IMAGE_LLM_API_KEY"), 
            base_url=os.getenv("IMAGE_LLM_BASE_URL")
        )
        response = client.chat.completions.create(
            model=os.getenv("IMAGE_LLM_MODEL_NAME"),  
            messages=messages,
        )

        logger.info(f"response: {response}")
        image_reasoning_result = response.choices[0].message.content

    except Exception as e:
        image_reasoning_result = ""
        logger.error(f"image_reasoning_result-Execute error: {e}", exc_info=True)

    logger.info(
        f"---get_reasoning_by_image-image_reasoning_result:{image_reasoning_result}"
    )

    return image_reasoning_result


# Run the server when the script is executed directly
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    load_dotenv()
    logger.info("Starting Image MCP Server...")
    mcp.run(transport='stdio')
