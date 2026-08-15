"""
YouTube MCP Service

This module provides MCP service functionality for YouTube operations including:
- Downloading videos from YouTube URLs
- Extracting transcripts from YouTube videos

It handles various scenarios with proper validation, error handling,
and progress tracking while providing LLM-friendly formatted results.
"""

import os
import time
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from youtube_transcript_api import FetchedTranscript, YouTubeTranscriptApi

from aworld.logs.util import Color
from examples.gaia.mcp_collections.base import ActionArguments, ActionCollection, ActionResponse

# Default driver path for Chrome WebDriver
_DEFAULT_DRIVER_PATH = os.environ.get(
    "CHROME_DRIVER_PATH", str(Path("~/Downloads/chromedriver-mac-arm64/chromedriver").expanduser())
)


class YoutubeDownloadResults(BaseModel):
    """Download result model with file information"""

    file_path: str
    file_name: str
    file_size: int
    content_type: str | None = None
    success: bool
    error: str | None = None


class TranscriptResult(BaseModel):
    """Transcript result model with transcript information"""

    video_id: str
    transcript: FetchedTranscript
    success: bool
    error: str | None = None


class YouTubeMetadata(BaseModel):
    """Metadata for YouTube operation results"""

    operation: str
    url: str | None = None
    video_id: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    content_type: str | None = None
    language_code: str | None = None
    translate_to_language: str | None = None
    execution_time: float | None = None
    error_type: str | None = None


class YouTubeActionCollection(ActionCollection):
    """MCP service for YouTube operations.

    Provides YouTube capabilities including:
    - Video downloading with Selenium automation
    - Transcript extraction and translation
    - LLM-friendly result formatting
    - Error handling and logging
    """

    def __init__(self, arguments: ActionArguments) -> None:
        super().__init__(arguments)

        # Initialize supported file extensions
        self.supported_extensions = {".mp4", ".webm", ".mkv"}

        self._color_log("YouTube service initialized", Color.green, "debug")

    def _format_transcript_output(self, result: TranscriptResult, format_type: str = "markdown") -> str:
        """Format transcript results for LLM consumption.

        Args:
            result: Transcript extraction result
            format_type: Output format ('markdown', 'json', 'text')

        Returns:
            Formatted string suitable for LLM consumption
        """
        if result is None or not result.success:
            return f"Failed to extract transcript: {result.error}"

        if format_type == "json":
            return result.model_dump()
        elif format_type == "text":
            output = [f"Transcript for video ID: {result.video_id}\n"]

            # Access snippets from FetchedTranscript
            for entry in result.transcript.snippets:
                start_time = entry["start"]
                text = entry["text"]

                minutes, seconds = divmod(int(start_time), 60)
                timestamp = f"{minutes:02d}:{seconds:02d}"

                output.append(f"[{timestamp}] {text}")

            return "\n".join(output)
        else:  # markdown (default)
            output = [f"# Transcript for YouTube Video: {result.video_id}\n"]
            output.append("| Timestamp | Text |")
            output.append("| --- | --- |")

            # Access snippets from FetchedTranscript
            for entry in result.transcript.snippets:
                start_time = entry["start"]
                text: str = entry["text"]

                minutes, seconds = divmod(int(start_time), 60)
                timestamp = f"{minutes:02d}:{seconds:02d}"

                # Escape pipe characters in markdown table
                safe_text = text.replace("|", "\\|")
                output.append(f"| {timestamp} | {safe_text} |")

            return "\n".join(output)

    def _format_download_output(self, result: YoutubeDownloadResults, format_type: str = "markdown") -> str:
        """Format download results for LLM consumption.

        Args:
            result: Download result
            format_type: Output format ('markdown', 'json', 'text')

        Returns:
            Formatted string suitable for LLM consumption
        """
        if not result.success:
            return f"Failed to download video: {result.error}"

        if format_type == "json":
            return result.model_dump()
        elif format_type == "text":
            output_parts = [
                "Download completed successfully",
                f"File: {result.file_name}",
                f"Path: {result.file_path}",
                f"Size: {result.file_size} bytes",
            ]
            if result.content_type:
                output_parts.append(f"Content Type: {result.content_type}")

            return "\n".join(output_parts)
        else:  # markdown (default)
            output_parts = [
                "# YouTube Download Results ✅",
                "",
                "## File Information",
                f"**Filename:** `{result.file_name}`",
                f"**Path:** `{result.file_path}`",
                f"**Size:** {result.file_size} bytes",
            ]
            if result.content_type:
                output_parts.append(f"**Content Type:** {result.content_type}")

            return "\n".join(output_parts)

    def _get_youtube_content(self, url: str, output_dir: str, timeout: int) -> None:
        """Use Selenium to download YouTube content via cobalt.tools

        Args:
            url: YouTube video URL
            output_dir: Directory to save downloaded content
            timeout: Maximum time to wait for download in seconds
        """
        driver = None
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
            service = Service(executable_path=_DEFAULT_DRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=options)

            self._color_log(f"Opening cobalt.tools to download from {url}", Color.blue)
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
                self._color_log(f"Bot detection handling: {str(e)}", Color.yellow)

            # try:
            #     t = 0
            #     while t < timeout:
            #         if (
            #             "downloading" not in driver.find_element(By.CLASS_NAME, "status-text.svelte-dmosdd").text
            #             and "starting" not in driver.find_element(By.CLASS_NAME, "status-text.svelte-dmosdd").text
            #         ):
            #             driver.find_element(By.CLASS_NAME, "button.action-button.svelte-dmosdd").click()
            #             break
            #         t += 3
            #         time.sleep(3)
            # except Exception as e:
            #     self._color_log(f"Bot detection handling: {str(e)}", Color.yellow)

            # Wait for download to complete
            cnt = 0
            while len(os.listdir(output_dir)) == 0 or os.listdir(output_dir)[0].split(".")[-1] == "crdownload":
                time.sleep(3)
                cnt += 3
                if cnt >= timeout:
                    self._color_log(f"Download timeout after {timeout} seconds", Color.yellow)
                    break

            self._color_log("Download process completed", Color.green)

        except Exception as e:
            self._color_log(f"Error during YouTube content download: {str(e)}", Color.red)
            raise
        finally:
            # Close browser
            if driver:
                driver.quit()

    def _find_existing_video(self, search_dir: str, video_id: str) -> str | None:
        """Recursively search for an existing video file with the given ID.

        Args:
            search_dir: Directory to search in
            video_id: YouTube video ID to look for

        Returns:
            Path to existing file if found, None otherwise
        """
        if not video_id:
            return None

        search_path = Path(search_dir)
        if not search_path.exists():
            return None

        for item in search_path.iterdir():
            if item.is_file() and video_id in item.name:
                return str(item)
            elif item.is_dir():
                found = self._find_existing_video(str(item), video_id)
                if found:
                    return found

        return None

    async def mcp_download_youtube_video(
        self,
        url: str = Field(description="The URL of YouTube video to download."),
        timeout: int = Field(180, description="Download timeout in seconds (default: 180)."),
        output_format: str = Field(
            "markdown", description="Output format: 'markdown', 'json', or 'text' (default: markdown)."
        ),
    ) -> ActionResponse:
        """Download a YouTube video from URL and save it to the local filesystem.

        This tool provides YouTube video downloading with:
        - Selenium-based automation via cobalt.tools
        - Configurable timeout controls
        - Existing file detection to avoid redundant downloads
        - LLM-optimized result formatting

        Args:
            url: The URL of YouTube video to download
            timeout: Maximum download time in seconds
            output_format: Format for the response output

        Returns:
            ActionResponse with download results and metadata
        """
        start_time = time.time()

        try:
            # Validate URL
            if not url.startswith(("http://", "https://")):
                raise ValueError("Invalid URL format. URL must start with http:// or https://")

            if not ("youtube.com" in url or "youtu.be" in url):
                raise ValueError("URL must be a valid YouTube URL")

            # Create output directory if it doesn't exist
            output_path = self.workspace / "youtube_downloads"
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate filename based on timestamp
            filename = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = output_path / filename
            file_path.mkdir(parents=True, exist_ok=True)
            self._color_log(f"Output path: {file_path}", Color.blue)

            # Extract video ID for existing file check
            video_id = url.split("?v=")[-1].split("&")[0] if "?v=" in url else ""
            if "youtu.be/" in url and not video_id:
                video_id = url.split("youtu.be/")[-1].split("?")[0]

            # Check if video already exists
            base_path = self.workspace
            existing_file = self._find_existing_video(str(base_path), video_id)

            if existing_file:
                existing_path = Path(existing_file)
                result = YoutubeDownloadResults(
                    file_path=str(existing_path),
                    file_name=existing_path.name,
                    file_size=existing_path.stat().st_size,
                    content_type="mp4",
                    success=True,
                    error=None,
                )
                self._color_log(f"Found {video_id} already downloaded in: {existing_file}", Color.green)

                # Format output for LLM
                message = self._format_download_output(result, output_format)
                execution_time = time.time() - start_time

                # Create metadata
                metadata = YouTubeMetadata(
                    operation="download",
                    url=url,
                    video_id=video_id,
                    file_path=str(existing_path),
                    file_name=existing_path.name,
                    file_size=existing_path.stat().st_size,
                    content_type="mp4",
                    execution_time=execution_time,
                ).model_dump()

                return ActionResponse(success=True, message=message, metadata=metadata)

            # Download the video
            self._color_log(f"Downloading video from {url} to {file_path}", Color.blue)
            self._get_youtube_content(url, str(file_path), timeout)

            # Check if download was successful
            downloaded_files = list(file_path.iterdir())
            if not downloaded_files:
                raise FileNotFoundError("No files were downloaded")

            download_file = downloaded_files[0]
            file_size = download_file.stat().st_size

            self._color_log(f"File downloaded successfully to {download_file}", Color.green)

            # Create result
            result = YoutubeDownloadResults(
                file_path=str(download_file),
                file_name=download_file.name,
                file_size=file_size,
                content_type="mp4",
                success=True,
                error=None,
            )

            # Format output for LLM
            message = self._format_download_output(result, output_format)
            execution_time = time.time() - start_time

            # Create metadata
            metadata = YouTubeMetadata(
                operation="download",
                url=url,
                video_id=video_id,
                file_path=str(download_file),
                file_name=download_file.name,
                file_size=file_size,
                content_type="mp4",
                execution_time=execution_time,
            ).model_dump()

            return ActionResponse(success=True, message=message, metadata=metadata)

        except Exception as e:
            error_msg = str(e)
            self._color_log(f"Download error: {traceback.format_exc()}", Color.red)

            # Format error for LLM
            message = f"Failed to download YouTube video: {error_msg}"
            execution_time = time.time() - start_time

            # Create metadata
            metadata = YouTubeMetadata(
                operation="download",
                url=url,
                error_type="download_failure",
                execution_time=execution_time,
            ).model_dump()

            return ActionResponse(success=False, message=message, metadata=metadata)

    async def mcp_extract_youtube_transcript(
        self,
        video_id: str = Field(description="The YouTube video ID or URL to extract transcript from."),
        language_code: str = Field("en", description="Language code for the transcript (default: en)."),
        translate_to_language: str | None = Field(
            None, description="Translate transcript to this language code if provided."
        ),
        output_format: str = Field(
            "markdown", description="Output format: 'markdown', 'json', or 'text' (default: markdown)."
        ),
    ) -> ActionResponse:
        """Extract transcript from a YouTube video given its video ID or URL.

        This tool provides transcript extraction with:
        - Support for multiple languages
        - Translation capabilities
        - URL or video ID input handling
        - LLM-optimized result formatting

        Args:
            video_id: The YouTube video ID or URL to extract transcript from
            language_code: Language code for the transcript
            translate_to_language: Translate transcript to this language code if provided
            output_format: Format for the response output

        Returns:
            ActionResponse with transcript data and metadata
        """
        start_time = time.time()

        try:
            # Clean video_id if full URL was provided
            if "youtube.com" in video_id or "youtu.be" in video_id:
                if "?v=" in video_id:
                    video_id = video_id.split("?v=")[-1].split("&")[0]
                elif "youtu.be/" in video_id:
                    video_id = video_id.split("youtu.be/")[-1].split("?")[0]

            self._color_log(f"Extracting transcript for video ID: {video_id}", Color.blue)

            # Get transcript in specified language
            if translate_to_language:
                # Get transcript and translate it
                y_api = YouTubeTranscriptApi()
                transcript_list = y_api.list(video_id)
                transcript = None

                try:
                    # Try to get transcript in specified language
                    transcript = transcript_list.find_transcript([language_code])
                except Exception:
                    # If specified language not found, get any available transcript
                    transcript = transcript_list.find_generated_transcript(["en"])

                # Translate to target language
                transcript_data = transcript.translate(translate_to_language).fetch()

            else:
                try:
                    # Get transcript without translation
                    transcript_data: FetchedTranscript = (
                        YouTubeTranscriptApi()
                        .list(video_id)
                        .find_transcript((language_code,))
                        .fetch(preserve_formatting=False)
                    )
                except Exception:
                    transcript_data = None

            result = TranscriptResult(video_id=video_id, transcript=transcript_data, success=True, error=None)

            self._color_log(f"Successfully extracted transcript for video ID: {video_id}", Color.green)

            # Format output for LLM
            message = self._format_transcript_output(result, output_format)
            execution_time = time.time() - start_time

            # Create metadata
            metadata = YouTubeMetadata(
                operation="transcript",
                video_id=video_id,
                language_code=language_code,
                translate_to_language=translate_to_language,
                execution_time=execution_time,
            ).model_dump()

            return ActionResponse(success=True, message=message, metadata=metadata)

        except Exception as e:
            error_msg = str(e)
            self._color_log(f"Transcript extraction error: {traceback.format_exc()}", Color.red)

            # Format error for LLM
            message = f"Failed to extract transcript: {error_msg}"
            execution_time = time.time() - start_time

            # Create metadata
            metadata = YouTubeMetadata(
                operation="transcript",
                video_id=video_id,
                language_code=language_code,
                translate_to_language=translate_to_language,
                error_type="transcript_failure",
                execution_time=execution_time,
            ).model_dump()

            return ActionResponse(success=False, message=message, metadata=metadata)


# Default arguments for testing
if __name__ == "__main__":
    load_dotenv()

    arguments = ActionArguments(
        name="youtube_service",
        transport="stdio",
        workspace=os.getenv("AWORLD_WORKSPACE", "~"),
    )

    try:
        youtube_service = YouTubeActionCollection(arguments)
        youtube_service.run()
    except Exception as e:
        print(f"Error: {e}")
