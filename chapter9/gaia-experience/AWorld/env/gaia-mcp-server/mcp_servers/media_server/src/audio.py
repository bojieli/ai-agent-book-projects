import json
import logging
import os
import subprocess
import time
import traceback
from pathlib import Path
from typing import Any, Union, Literal
from openai import OpenAI
from pydantic.fields import FieldInfo

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field, BaseModel
from dotenv import load_dotenv

from base import ActionResponse, _validate_file_path

workspace = Path.home()
_audio_output_dir = workspace / "processed_audio"
_audio_output_dir.mkdir(exist_ok=True, parents=True)

mcp = FastMCP(
    "media-audio-server",
    instructions="""
MCP service for comprehensive audio processing using ffmpeg.

    Supports various audio operations including:
    - Audio format conversion
    - Audio transcription (speech-to-text)
    - Audio metadata extraction
    - Audio quality enhancement
    - Audio trimming and editing
    - Audio analysis and feature extraction
""",
)


class AudioMetadata(BaseModel):
    """Metadata extracted from audio processing."""

    file_name: str = Field(description="Original audio file name")
    file_size: int = Field(description="File size in bytes")
    file_type: str = Field(description="Audio file type/extension")
    absolute_path: str = Field(description="Absolute path to the audio file")
    duration: float | None = Field(
        default=None, description="Duration of audio in seconds"
    )
    sample_rate: int | None = Field(default=None, description="Audio sample rate in Hz")
    channels: int | None = Field(default=None, description="Number of audio channels")
    bitrate: int | None = Field(default=None, description="Audio bitrate in kbps")
    codec: str | None = Field(default=None, description="Audio codec used")
    processing_time: float = Field(
        description="Time taken to process the audio in seconds"
    )
    output_files: list[str] = Field(
        default_factory=list, description="Paths to generated output files"
    )
    transcription: str | None = Field(
        default=None, description="Transcribed text from audio"
    )
    word_count: int | None = Field(
        default=None, description="Number of words in transcription"
    )
    output_format: str = Field(description="Format of the processed output")


@mcp.tool(
    description="""
Transcribe audio file to text using OpenAI Whisper.

        This tool converts speech in audio files to text with high accuracy.
        Supports multiple languages and provides various output formats including
        timestamped segments for detailed analysis.
"""
)
async def transcribe_audio(
    file_path: str = Field(description="Path to the audio file to transcribe"),
    model_size: Literal["tiny", "base", "small", "medium", "large"] = Field(
        default="base",
        description="Whisper model size: tiny (fastest), base (balanced), small, medium, large (most accurate)",
    ),
    output_format: Literal["text", "detailed", "segments"] = Field(
        default="text",
        description="Output format: 'text' (plain text), 'detailed' (with metadata), 'segments' (timestamped)",
    ),
) -> Union[str, TextContent]:
    try:
        # Handle FieldInfo objects
        if isinstance(file_path, FieldInfo):
            file_path = file_path.default
        if isinstance(model_size, FieldInfo):
            model_size = model_size.default
        if isinstance(output_format, FieldInfo):
            output_format = output_format.default

        start_time = time.time()

        # Validate input file
        file_path: Path = _validate_file_path(file_path)
        logging.info(f"Transcribing audio: {file_path.name}")

        # Get original metadata
        original_metadata = _get_audio_metadata(file_path)

        # Prepare audio for transcription
        prepared_audio = _prepare_audio_for_transcription(file_path)

        # Perform transcription
        transcription_result = _transcribe_with_whisper(prepared_audio)

        processing_time = time.time() - start_time

        # Prepare file statistics
        file_stats = file_path.stat()

        # Count words in transcription
        word_count = (
            len(transcription_result["text"].split())
            if transcription_result["text"]
            else 0
        )

        # Create metadata object
        audio_metadata = AudioMetadata(
            file_name=file_path.name,
            file_size=file_stats.st_size,
            file_type=file_path.suffix.lower(),
            absolute_path=str(file_path.absolute()),
            duration=original_metadata.get("duration"),
            sample_rate=original_metadata.get("sample_rate"),
            channels=original_metadata.get("channels"),
            bitrate=original_metadata.get("bitrate"),
            codec=original_metadata.get("codec"),
            processing_time=processing_time,
            output_files=[str(prepared_audio)],
            transcription=transcription_result["text"],
            word_count=word_count,
            output_format=f"transcription_{output_format}",
        )

        # Format output based on requested format
        if output_format == "text":
            result_message = transcription_result["text"]
        elif output_format == "detailed":
            confidence_str = (
                f"{transcription_result['confidence']:.2f}"
                if transcription_result["confidence"]
                else "N/A"
            )
            result_message = (
                f"Transcription Results for {file_path.name}:\n\n"
                f"**Text:** {transcription_result['text']}\n\n"
                f"**Confidence:** {confidence_str}\n"
                f"**Word Count:** {word_count}\n"
                f"**Duration:** {original_metadata.get('duration', 0):.2f} seconds\n"
                f"**Model:** {model_size}\n"
                f"**Processing Time:** {processing_time:.2f} seconds"
            )
        elif output_format == "segments":
            segments_text = "\n".join(
                [
                    f"[{seg.get('start', 0):.2f}s - {seg.get('end', 0):.2f}s]: {seg.get('text', '').strip()}"
                    for seg in transcription_result.get("segments", [])
                ]
            )
            result_message = (
                f"Timestamped Transcription for {file_path.name}:\n\n"
                f"{segments_text}\n\n"
                f"**Full Text:** {transcription_result['text']}"
            )
        else:
            result_message = transcription_result["text"]

        # Clean up temporary file
        try:
            prepared_audio.unlink()
        except Exception:
            pass  # Ignore cleanup errors

        logging.info(
            f"Transcription completed: {word_count} words, {processing_time:.2f}s"
        )

        action_response = ActionResponse(
            success=True, message=result_message, metadata=audio_metadata.model_dump()
        )
        # output_dict = {
        #     "artifact_type": "MARKDOWN",
        #     "artifact_data": formatted_content
        # }
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        logging.error(f"Audio transcription failed: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"Audio transcription failed: {str(e)}",
            metadata={"error_type": "transcription_error"},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
Extract comprehensive metadata from audio files.

        This tool analyzes audio files and extracts detailed metadata including
        duration, sample rate, channels, bitrate, codec, and other technical information.
"""
)
async def extract_audio_metadata(
    file_path: str = Field(description="Path to the audio file to analyze"),
) -> Union[str, TextContent]:
    try:
        if isinstance(file_path, FieldInfo):
            file_path = file_path.default

        start_time = time.time()

        # Validate input file
        file_path: Path = _validate_file_path(file_path)
        logging.info(f"Extracting metadata from: {file_path.name}")

        # Extract metadata
        metadata = _get_audio_metadata(file_path)
        processing_time = time.time() - start_time

        # Prepare file statistics
        file_stats = file_path.stat()

        # Create metadata object
        audio_metadata = AudioMetadata(
            file_name=file_path.name,
            file_size=file_stats.st_size,
            file_type=file_path.suffix.lower(),
            absolute_path=str(file_path.absolute()),
            duration=metadata.get("duration"),
            sample_rate=metadata.get("sample_rate"),
            channels=metadata.get("channels"),
            bitrate=metadata.get("bitrate"),
            codec=metadata.get("codec"),
            processing_time=processing_time,
            output_files=[],
            output_format="metadata",
        )

        # Format metadata for LLM consumption
        result_message = (
            f"Audio Metadata for {file_path.name}:\n"
            f"Duration: {metadata.get('duration', 'Unknown'):.2f} seconds\n"
            f"Sample Rate: {metadata.get('sample_rate', 'Unknown')} Hz\n"
            f"Channels: {metadata.get('channels', 'Unknown')}\n"
            f"Bitrate: {metadata.get('bitrate', 'Unknown')} kbps\n"
            f"Codec: {metadata.get('codec', 'Unknown')}\n"
            f"File Size: {file_stats.st_size / 1024 / 1024:.2f} MB\n"
            f"Format: {file_path.suffix.upper()}"
        )

        logging.info(f"Metadata extraction completed in {processing_time:.2f}s")

        action_response = ActionResponse(
            success=True, message=result_message, metadata=audio_metadata.model_dump()
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        logging.error(f"Metadata extraction failed: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"Metadata extraction failed: {str(e)}",
            metadata={"error_type": "metadata_error"},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
Trim audio file to specified time range.

        This tool cuts audio files to extract specific segments based on start time
        and duration. Useful for creating clips or removing unwanted sections.
"""
)
async def trim_audio(
    file_path: str = Field(description="Path to the audio file to trim"),
    start_time: float = Field(description="Start time in seconds"),
    duration: float | None = Field(
        default=None, description="Duration in seconds (if None, trim to end)"
    ),
) -> Union[str, TextContent]:
    try:
        if isinstance(file_path, FieldInfo):
            file_path = file_path.default
        if isinstance(start_time, FieldInfo):
            start_time = start_time.default
        if isinstance(duration, FieldInfo):
            duration = duration.default

        process_start = time.time()

        # Validate input file
        file_path: Path = _validate_file_path(file_path)
        logging.info(f"Trimming audio: {file_path.name}")

        # Get original metadata
        original_metadata = _get_audio_metadata(file_path)

        # Validate time parameters
        if start_time < 0:
            raise ValueError("Start time cannot be negative")
        if duration is not None and duration <= 0:
            raise ValueError("Duration must be positive")
        if (
            original_metadata.get("duration")
            and start_time >= original_metadata["duration"]
        ):
            raise ValueError("Start time exceeds audio duration")

        # Trim audio
        output_path = _trim_audio(file_path, start_time, duration)

        # Get trimmed file metadata
        trimmed_metadata = _get_audio_metadata(output_path)
        processing_time = time.time() - process_start

        # Prepare file statistics
        file_stats = file_path.stat()

        # Create metadata object
        audio_metadata = AudioMetadata(
            file_name=file_path.name,
            file_size=file_stats.st_size,
            file_type=file_path.suffix.lower(),
            absolute_path=str(file_path.absolute()),
            duration=trimmed_metadata.get("duration"),
            sample_rate=trimmed_metadata.get("sample_rate"),
            channels=trimmed_metadata.get("channels"),
            bitrate=trimmed_metadata.get("bitrate"),
            codec=trimmed_metadata.get("codec"),
            processing_time=processing_time,
            output_files=[str(output_path)],
            output_format="trimmed_audio",
        )

        end_time = start_time + (
            duration or (original_metadata.get("duration", 0) - start_time)
        )
        result_message = (
            f"Successfully trimmed {file_path.name}\n"
            f"Original duration: {original_metadata.get('duration', 0):.2f} seconds\n"
            f"Trimmed segment: {start_time:.2f}s - {end_time:.2f}s\n"
            f"New duration: {trimmed_metadata.get('duration', 0):.2f} seconds\n"
            f"Output file: {output_path.name}"
        )

        logging.info(f"Audio trimming completed in {processing_time:.2f}s")

        action_response = ActionResponse(
            success=True, message=result_message, metadata=audio_metadata.model_dump()
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }

        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        logging.error(f"Audio trimming failed: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"Audio trimming failed: {str(e)}",
            metadata={"error_type": "trimming_error"},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
List all supported audio formats for processing.
"""
)
async def list_supported_formats() -> Union[str, TextContent]:
    supported_formats = {
        "MP3": "MPEG Audio Layer III (.mp3) - Most common compressed format",
        "WAV": "Waveform Audio File Format (.wav) - Uncompressed, high quality",
        "FLAC": "Free Lossless Audio Codec (.flac) - Lossless compression",
        "AAC": "Advanced Audio Coding (.aac) - Efficient compression",
        "OGG": "Ogg Vorbis (.ogg) - Open source compressed format",
        "M4A": "MPEG-4 Audio (.m4a) - Apple's preferred format",
        "WMA": "Windows Media Audio (.wma) - Microsoft format",
        "OPUS": "Opus Audio (.opus) - Modern, efficient codec",
        "AIFF": "Audio Interchange File Format (.aiff) - Apple's uncompressed format",
        "AU": "Sun Audio (.au) - Unix audio format",
        "RA": "RealAudio (.ra) - Streaming audio format",
        "AMR": "Adaptive Multi-Rate (.amr) - Mobile audio format",
    }
    format_list = "\n".join(
        [
            f"**{format_name}**: {description}"
            for format_name, description in supported_formats.items()
        ]
    )
    action_response = ActionResponse(
        success=True,
        message=f"Supported audio formats:\n\n{format_list}",
        metadata={
            "supported_formats": list(supported_formats.keys()),
            "total_formats": len(supported_formats),
            "ffmpeg_available": _check_ffmpeg_availability(),
        },
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": json.dumps(action_response.model_dump())
    }

    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )


def _check_ffmpeg_availability() -> bool:
    """Check if ffmpeg is available in the system.

    Returns:
        bool: True if ffmpeg is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            logging.info("FFmpeg is available")
        else:
            logging.info("FFmpeg not found in system PATH")
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logging.info(
            "FFmpeg not available or timeout, Please refer to https://github.com/inclusionAI/AWorld/blob/main/examples/gaia/README.md#system-tools-setup for more details"
        )
        return False


def _get_audio_metadata(file_path: Path) -> dict[str, Any]:
    """Extract audio metadata using ffprobe.

    Args:
        file_path: Path to the audio file

    Returns:
        Dictionary containing audio metadata
    """
    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=False
        )

        if result.returncode == 0:
            metadata = json.loads(result.stdout)

            # Extract relevant audio information
            format_info = metadata.get("format", {})
            streams = metadata.get("streams", [])
            audio_stream = next(
                (s for s in streams if s.get("codec_type") == "audio"), {}
            )

            return {
                "duration": float(format_info.get("duration", 0)),
                "sample_rate": (
                    int(audio_stream.get("sample_rate", 0))
                    if audio_stream.get("sample_rate")
                    else None
                ),
                "channels": (
                    int(audio_stream.get("channels", 0))
                    if audio_stream.get("channels")
                    else None
                ),
                "bitrate": (
                    int(format_info.get("bit_rate", 0)) // 1000
                    if format_info.get("bit_rate")
                    else None
                ),
                "codec": audio_stream.get("codec_name"),
            }
        else:
            logging.warning(f"Failed to extract metadata: {result.stderr}")
            return {}

    except Exception as e:
        logging.error(f"Error extracting audio metadata: {str(e)}")
        return {}


def _trim_audio(
    input_path: Path, start_time: float, duration: float | None = None
) -> Path:
    """Trim audio file to specified time range.

    Args:
        input_path: Path to input audio file
        start_time: Start time in seconds
        duration: Duration in seconds (if None, trim to end)

    Returns:
        Path to trimmed audio file
    """
    output_path = _audio_output_dir / f"{input_path.stem}_trimmed{input_path.suffix}"

    cmd = ["ffmpeg", "-i", str(input_path), "-ss", str(start_time), "-y"]

    if duration is not None:
        cmd.extend(["-t", str(duration)])

    cmd.extend(["-c", "copy", str(output_path)])

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, check=False
    )

    if result.returncode != 0:
        raise RuntimeError(f"Audio trimming failed: {result.stderr}")

    return output_path


def _prepare_audio_for_transcription(file_path: Path) -> Path:
    """Prepare audio file for transcription by converting to optimal format.

    Args:
        file_path: Path to the original audio file

    Returns:
        Path to the prepared audio file (WAV format, 16kHz)
    """
    output_path = _audio_output_dir / f"{file_path.stem}_for_transcription.wav"

    # Convert to WAV format with 16kHz sample rate for optimal transcription
    cmd = [
        "ffmpeg",
        "-i",
        str(file_path),
        "-ar",
        "16000",  # 16kHz sample rate
        "-ac",
        "1",  # Mono channel
        "-c:a",
        "pcm_s16le",  # 16-bit PCM
        "-y",
        str(output_path),
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, check=False
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Audio preparation for transcription failed: {result.stderr}"
        )

    return output_path


def _transcribe_with_whisper(audio_path: Path) -> dict[str, Any]:
    """Transcribe audio using OpenAI Whisper.

    Args:
        audio_path: Path to the audio file

    Returns:
        Dictionary containing transcription results
    """
    try:
        client: OpenAI = OpenAI(
            api_key=os.getenv("AUDIO_LLM_API_KEY"),
            base_url=os.getenv("AUDIO_LLM_BASE_URL"),
        )

        # Use the file for transcription
        with open(audio_path, "rb") as audio_file:
            transcription: str = client.audio.transcriptions.create(
                file=audio_file,
                model=os.getenv("AUDIO_LLM_MODEL_NAME"),
                response_format="text",
            )

        return {"text": transcription.strip() if transcription else ""}
    except Exception as e:
        raise RuntimeError(
            f"Audio transcription failed: {e}: {traceback.format_exc()}"
        ) from e


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting media-audio-server MCP server!")
    mcp.run(transport="stdio")
