"""
Youtube Download MCP Server

This module provides MCP server functionality for downloading files from Youtube URLs.
It handles various download scenarios with proper validation, error handling,
and progress tracking.

Key features:
- File downloading from Youtube HTTP/HTTPS URLs
- Download progress tracking
- File validation
- Safe file saving

Main functions:
- mcpyoutubedownload: Downloads files from URLs of Youtube to local filesystem
"""

import os
import sys
import time
import traceback
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from aworld.logs.util import logger

mcp = FastMCP("youtube-server")
_default_driver_path = os.environ.get(
    "CHROME_DRIVER_PATH",
    os.path.expanduser("~/Downloads/chromedriver-mac-arm64/chromedriver"),
)


class YoutubeDownloadResults(BaseModel):
    """Download result model with file information"""

    file_path: str
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    success: bool
    error: Optional[str] = None


@mcp.tool(
    description="Download the youtube file from the URL and save to the local filesystem."
)
def download_youtube_files(
    url: str = Field(
        description="The URL of youtube file to download. Must be a String."
    ),
    output_dir: str = Field(
        "/tmp/mcp_downloads",
        description="Directory to save the downloaded files (default: /tmp/mcp_downloads).",
    ),
    timeout: int = Field(
        180, description="Download timeout in seconds (default: 180)."
    ),
) -> str:
    """Download the youtube file from the URL and save to the local filesystem.

    Args:
        url: The URL of youtube file to download, must be a String
        output_dir: Directory to save the downloaded files
        timeout: Download timeout in seconds

    Returns:
        JSON string with download results information
    """
    # Handle Field objects if they're passed directly
    if hasattr(url, "default") and not isinstance(url, str):
        url = url.default

    if hasattr(output_dir, "default") and not isinstance(output_dir, str):
        output_dir = output_dir.default

    if hasattr(timeout, "default") and not isinstance(timeout, int):
        timeout = timeout.default

    def _get_youtube_content(url: str, output_dir: str, timeout: int) -> None:
        """Use Selenium to download YouTube content via cobalt.tools"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            # Set download file default path
            prefs = {
                "download.default_directory": output_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            options.add_experimental_option("prefs", prefs)
            # Create WebDriver object and launch Chrome browser
            service = Service(executable_path=_default_driver_path)
            driver = webdriver.Chrome(service=service, options=options)

            logger.info(f"Opening cobalt.tools to download from {url}")
            # Open target webpage
            driver.get("https://cobalt.tools/")
            # Wait for page to load
            time.sleep(5)
            # Find input field and enter YouTube link
            input_field = driver.find_element(By.ID, "link-area")
            input_field.send_keys(url)
            time.sleep(5)
            # Find download button and click
            download_button = driver.find_element(By.ID, "download-button")
            download_button.click()
            time.sleep(5)

            try:
                # Handle bot detection popup
                driver.find_element(
                    By.CLASS_NAME,
                    "button.elevated.popup-button.undefined.svelte-nnawom.active",
                ).click()
            except Exception as e:
                logger.warning(f"Bot detection handling: {str(e)}")

            # Wait for download to complete
            cnt = 0
            while (
                len(os.listdir(output_dir)) == 0
                or os.listdir(output_dir)[0].split(".")[-1] == "crdownload"
            ):
                time.sleep(3)
                cnt += 3
                if cnt >= timeout:
                    logger.warning(f"Download timeout after {timeout} seconds")
                    break

            logger.info("Download process completed")

        except Exception as e:
            logger.error(f"Error during YouTube content download: {str(e)}")
            raise
        finally:
            # Close browser
            if "driver" in locals():
                driver.quit()

    def _download_single_file(
        url: str, output_dir: str, filename: str, timeout: int
    ) -> str:
        """Download a single file from URL and save it to the local filesystem."""
        try:
            # Validate URL
            if not url.startswith(("http://", "https://")):
                raise ValueError(
                    "Invalid URL format. URL must start with http:// or https://"
                )

            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Determine filename if not provided
            if not filename:
                filename = os.path.basename(urllib.parse.urlparse(url).path)
                if not filename:
                    filename = "downloaded_file"
            filename += "_" + datetime.now().strftime("%Y%m%d_%H%M%S")

            file_path = Path(os.path.join(output_path, filename))
            file_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output path: {file_path}")

            # check if video already exists with folder: /tmp/mcp_downloads
            video_id = url.split("?v=")[-1].split("&")[0] if "?v=" in url else ""
            base_path = os.getenv("FILESYSTEM_SERVER_WORKDIR")

            # checker function
            def find_existing_video(search_dir, video_id):
                if not video_id:
                    return None

                for item in os.listdir(search_dir):
                    item_path = os.path.join(search_dir, item)

                    if os.path.isfile(item_path) and video_id in item:
                        return item_path

                    elif os.path.isdir(item_path):
                        found = find_existing_video(item_path, video_id)
                        if found:
                            return found

                return None

            existing_file = find_existing_video(base_path, video_id)
            if existing_file:
                result = YoutubeDownloadResults(
                    file_path=existing_file,
                    file_name=os.path.basename(existing_file),
                    file_size=os.path.getsize(existing_file),
                    content_type="mp4",
                    success=True,
                    error=None,
                )
                logger.info(
                    f"Found {video_id} is already downloaded in: {existing_file}"
                )
                return result.model_dump_json()

            logger.info(f"Downloading file from {url} to {file_path}")

            _get_youtube_content(url, str(file_path), timeout)

            # Check if download was successful
            if len(os.listdir(file_path)) == 0:
                raise FileNotFoundError("No files were downloaded")

            download_file = os.path.join(file_path, os.listdir(file_path)[0])

            # Get actual file size
            actual_size = os.path.getsize(download_file)
            logger.success(f"File downloaded successfully to {download_file}")

            # Create result
            result = YoutubeDownloadResults(
                file_path=download_file,
                file_name=os.listdir(file_path)[0],
                file_size=actual_size,
                content_type="mp4",
                success=True,
                error=None,
            )

            return result.model_dump_json()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download error: {traceback.format_exc()}")

            result = YoutubeDownloadResults(
                file_path="",
                file_name="",
                file_size=0,
                content_type=None,
                success=False,
                error=error_msg,
            )

            return result.model_dump_json()

    result_json = _download_single_file(url, output_dir, "", timeout)
    result = YoutubeDownloadResults.model_validate_json(result_json)
    return result.model_dump_json()


def main():
    load_dotenv()
    print("Starting YoutubeDownload MCP Server...", file=sys.stderr)
    mcp.run(transport="stdio")


# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    main()


sys.modules[__name__].__call__ = __call__

# Run the server when the script is executed directly
if __name__ == "__main__":
    main()
