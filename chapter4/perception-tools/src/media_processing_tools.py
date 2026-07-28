"""
Media processing tools for audio, image, and video.
Based on AWorld MCP server implementation.
"""
import json
import logging
import traceback
import subprocess
import base64
from pathlib import Path
from typing import Union, Dict, Any

import cv2
from PIL import Image
from dotenv import load_dotenv
from mcp.types import TextContent

from base import ActionResponse, validate_file_path


load_dotenv()


def _map_model_for_openrouter(model: str) -> str:
    """Map a plain model id onto OpenRouter's `provider/model` form."""
    if "/" in model:
        return model
    m = model.lower()
    if m.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return f"openai/{model}"
    if m.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return model


def _make_vision_client(default_model: str = "gpt-5.6-luna"):
    """Build an OpenAI-compatible vision client with a universal fallback.

    Preferred path uses OPENAI_API_KEY directly. When it is absent but an
    OPENROUTER_API_KEY is set, transparently route through OpenRouter (mapping
    the model id to provider/model form) so the vision tools still run.

    Returns (client, model). Raises ValueError with the accepted keys listed
    when neither credential is available.
    """
    import os
    from openai import OpenAI

    model = os.getenv("PERCEPTION_VISION_MODEL", default_model)
    or_key = os.getenv("OPENROUTER_API_KEY")
    # gpt-5.x (incl. gpt-5.6*) needs OpenAI org-verification on the direct API;
    # when an OpenRouter key is present, prefer routing these ids through it.
    if or_key and model.lower().startswith("gpt-5"):
        client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
        return client, _map_model_for_openrouter(model)

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        base_url = os.getenv("OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        return client, model

    if or_key:
        client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
        return client, _map_model_for_openrouter(model)

    raise ValueError(
        "No LLM key configured. Set OPENAI_API_KEY or OPENROUTER_API_KEY (universal fallback)."
    )


async def transcribe_audio_whisper(
    file_path: str,
    model_size: str = "base",
    language: str = "en"
) -> Union[str, TextContent]:
    """
    Transcribe audio file using OpenAI Whisper (local).
    Note: Requires whisper package installed.
    
    Args:
        file_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code
        
    Returns:
        TextContent with transcription
    """
    try:
        path = validate_file_path(file_path)
        
        logging.info(f"🎤 Transcribing audio: {path}")
        
        try:
            import whisper
            
            # Load model
            model = whisper.load_model(model_size)
            
            # Transcribe
            result = model.transcribe(str(path), language=language)
            
            transcription = result["text"]
            
            response_data = {
                "file_name": path.name,
                "file_type": path.suffix,
                "model": model_size,
                "language": language,
                "transcription": transcription,
                "word_count": len(transcription.split())
            }
            
            logging.info(f"✅ Transcribed: {len(transcription)} chars")
            
            action_response = ActionResponse(
                success=True,
                message=response_data,
                metadata={"file_path": str(path)}
            )
            
        except ImportError:
            # Fallback: try using OpenAI API if available
            import os
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ImportError("Whisper not installed and no OPENAI_API_KEY found")
            
            client = OpenAI(api_key=api_key)
            
            with open(path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            response_data = {
                "file_name": path.name,
                "file_type": path.suffix,
                "model": "whisper-1 (API)",
                "language": language,
                "transcription": transcription.text,
                "word_count": len(transcription.text.split())
            }
            
            action_response = ActionResponse(
                success=True,
                message=response_data,
                metadata={"file_path": str(path), "method": "openai_api"}
            )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Audio transcription failed: {str(e)}"
        logging.error(f"Audio error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "audio_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def extract_audio_metadata(
    file_path: str
) -> Union[str, TextContent]:
    """
    Extract audio file metadata using ffprobe.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        TextContent with audio metadata
    """
    try:
        path = validate_file_path(file_path)
        
        logging.info(f"🎵 Extracting audio metadata: {path}")
        
        # Use ffprobe to get metadata
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            metadata = json.loads(result.stdout)
            
            format_info = metadata.get("format", {})
            streams = metadata.get("streams", [])
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
            
            response_data = {
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "duration": float(format_info.get("duration", 0)),
                "bit_rate": int(format_info.get("bit_rate", 0)),
                "format": format_info.get("format_name"),
                "codec": audio_stream.get("codec_name"),
                "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream.get("sample_rate") else None,
                "channels": int(audio_stream.get("channels", 0)) if audio_stream.get("channels") else None
            }
            
            logging.info(f"✅ Audio metadata extracted")
            
            action_response = ActionResponse(
                success=True,
                message=response_data,
                metadata={"file_path": str(path)}
            )
        else:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Audio metadata extraction failed: {str(e)}"
        logging.error(f"Audio metadata error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "audio_metadata_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def extract_text_ocr(
    image_path: str,
    language: str = "eng"
) -> Union[str, TextContent]:
    """
    Extract text from image using OCR.
    
    Args:
        image_path: Path to image file
        language: OCR language (eng, chi_sim, etc.)
        
    Returns:
        TextContent with extracted text
    """
    try:
        path = validate_file_path(image_path)
        
        logging.info(f"🔍 OCR extracting from image: {path}")
        
        try:
            import pytesseract
            
            img = Image.open(path)
            text = pytesseract.image_to_string(img, lang=language)
            
            result = {
                "file_name": path.name,
                "image_size": img.size,
                "extracted_text": text,
                "text_length": len(text),
                "word_count": len(text.split()),
                "language": language,
                "method": "pytesseract"
            }
            
            logging.info(f"✅ OCR extracted: {len(text)} chars")
            
            action_response = ActionResponse(
                success=True,
                message=result,
                metadata={"file_path": str(path)}
            )
            
        except ImportError:
            # Fallback to a simpler method or error
            raise ImportError("pytesseract not installed. Install with: pip install pytesseract")
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"OCR extraction failed: {str(e)}"
        logging.error(f"OCR error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "ocr_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def analyze_image_ai(
    image_path: str,
    prompt: str = "Describe this image in detail"
) -> Union[str, TextContent]:
    """
    Analyze image using AI (OpenAI Vision API).
    
    Args:
        image_path: Path to image file
        prompt: Prompt for AI analysis
        
    Returns:
        TextContent with AI analysis
    """
    try:
        path = validate_file_path(image_path)

        logging.info(f"🤖 AI analyzing image: {path}")

        client, model = _make_vision_client()

        # Encode image
        with open(path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        # Call Vision API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        analysis = response.choices[0].message.content

        result = {
            "file_name": path.name,
            "prompt": prompt,
            "analysis": analysis,
            "model": model
        }
        
        logging.info(f"✅ AI analysis completed")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"file_path": str(path)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"AI image analysis failed: {str(e)}"
        logging.error(f"AI analysis error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "ai_analysis_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def extract_video_keyframes(
    video_path: str,
    num_frames: int = 10
) -> Union[str, TextContent]:
    """
    Extract keyframes from video.
    
    Args:
        video_path: Path to video file
        num_frames: Number of keyframes to extract
        
    Returns:
        TextContent with keyframe information
    """
    try:
        path = validate_file_path(video_path)
        
        num_frames = max(1, num_frames)
        
        logging.info(f"🎬 Extracting keyframes from video: {path}")
        
        video = cv2.VideoCapture(str(path))
        
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Calculate frame interval
        interval = max(1, frame_count // num_frames)
        
        keyframes = []
        frame_num = 0
        
        while len(keyframes) < num_frames and video.isOpened():
            ret, frame = video.read()
            if not ret:
                break
            
            if frame_num % interval == 0:
                timestamp = frame_num / fps if fps > 0 else 0
                keyframes.append({
                    "frame_number": frame_num,
                    "timestamp": round(timestamp, 2),
                    "shape": frame.shape if frame is not None else None
                })
            
            frame_num += 1
        
        video.release()
        
        result = {
            "file_name": path.name,
            "duration": duration,
            "total_frames": frame_count,
            "fps": fps,
            "keyframes_extracted": len(keyframes),
            "keyframes": keyframes
        }
        
        logging.info(f"✅ Extracted {len(keyframes)} keyframes")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"file_path": str(path)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Keyframe extraction failed: {str(e)}"
        logging.error(f"Video error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "video_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def analyze_video_ai(
    video_path: str,
    num_frames: int = 5,
    prompt: str = "Analyze this video and describe what's happening"
) -> Union[str, TextContent]:
    """
    Analyze video content using AI vision on keyframes.
    
    Args:
        video_path: Path to video file
        num_frames: Number of frames to analyze
        prompt: Analysis prompt for AI
        
    Returns:
        TextContent with AI analysis
    """
    video = None
    try:
        path = validate_file_path(video_path)

        num_frames = max(1, num_frames)

        logging.info(f"🤖 AI analyzing video: {path}")

        client, model = _make_vision_client()

        # Extract keyframes
        video = cv2.VideoCapture(str(path))
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(1, frame_count // num_frames)
        
        # Extract and encode frames
        frame_analyses = []
        frame_num = 0
        frames_analyzed = 0
        
        while frames_analyzed < num_frames and video.isOpened():
            ret, frame = video.read()
            if not ret:
                break
            
            if frame_num % interval == 0:
                # Encode frame
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Analyze with GPT-4 Vision
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"{prompt} (Frame {frames_analyzed + 1}/{num_frames})"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=300
                )
                
                timestamp = frame_num / fps if fps > 0 else 0
                analysis = response.choices[0].message.content
                
                frame_analyses.append({
                    "frame_number": frame_num,
                    "timestamp": round(timestamp, 2),
                    "analysis": analysis
                })
                
                frames_analyzed += 1
            
            frame_num += 1

        # Generate overall summary
        combined_analyses = "\n\n".join([f"Frame {i+1} (t={a['timestamp']}s): {a['analysis']}" 
                                          for i, a in enumerate(frame_analyses)])
        
        result = {
            "file_name": path.name,
            "frames_analyzed": len(frame_analyses),
            "analyses": frame_analyses,
            "combined_analysis": combined_analyses
        }
        
        logging.info(f"✅ Analyzed {len(frame_analyses)} frames")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"file_path": str(path)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Video analysis failed: {str(e)}"
        logging.error(f"Video analysis error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "video_analysis_error"}
        )

        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
    finally:
        # Release the native decoder/file handle even when a per-frame Vision
        # API call raises mid-loop (the most likely failure point), otherwise
        # the VideoCapture leaks until GC finalizes it.
        if video is not None:
            video.release()


async def trim_audio(
    audio_path: str,
    start_time: float,
    duration: float | None = None,
    output_path: str | None = None
) -> Union[str, TextContent]:
    """
    Trim audio file to specified time range using ffmpeg.
    
    Args:
        audio_path: Path to audio file
        start_time: Start time in seconds
        duration: Duration in seconds (None for trim to end)
        output_path: Output file path (None for auto-generate)
        
    Returns:
        TextContent with trimmed audio info
    """
    try:
        path = validate_file_path(audio_path)
        
        logging.info(f"✂️ Trimming audio: {path}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = str(path.parent / f"{path.stem}_trimmed{path.suffix}")
        
        # Build ffmpeg command
        cmd = ["ffmpeg", "-i", str(path), "-ss", str(start_time)]
        
        if duration is not None:
            cmd.extend(["-t", str(duration)])
        
        cmd.extend(["-c", "copy", "-y", output_path])
        
        # Execute ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")
        
        output_file = Path(output_path)
        
        response_data = {
            "input_file": str(path),
            "output_file": str(output_file),
            "start_time": start_time,
            "duration": duration,
            "file_size": output_file.stat().st_size if output_file.exists() else 0
        }
        
        logging.info(f"✅ Trimmed audio saved to: {output_file}")
        
        action_response = ActionResponse(
            success=True,
            message=response_data,
            metadata={"output_path": str(output_file)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Audio trim failed: {str(e)}"
        logging.error(f"Audio trim error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "audio_trim_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def get_image_metadata(
    image_path: str
) -> Union[str, TextContent]:
    """
    Get detailed image metadata including EXIF data.
    
    Args:
        image_path: Path to image file
        
    Returns:
        TextContent with image metadata
    """
    try:
        path = validate_file_path(image_path)
        
        logging.info(f"📷 Getting image metadata: {path}")
        
        img = Image.open(path)
        
        # Basic metadata
        metadata = {
            "file_name": path.name,
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height,
            "file_size": path.stat().st_size
        }
        
        # Try to get EXIF data
        try:
            from PIL.ExifTags import TAGS
            exif_data = {}
            
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)
            
            if exif_data:
                metadata["exif"] = exif_data
        except Exception as e:
            logging.debug(f"No EXIF data: {e}")
        
        # Image info
        if hasattr(img, 'info'):
            # PIL's img.info routinely carries non-JSON-serializable values --
            # most notably the raw ICC color profile / EXIF blob as `bytes`
            # (present in almost every real photo, screenshot or design export).
            # Copying them verbatim would make the final json.dumps() raise
            # TypeError, turning a valid image into a failure response. Summarize
            # bytes as a size marker so metadata extraction still succeeds.
            metadata["info"] = {
                k: (f"<{len(v)} bytes>" if isinstance(v, (bytes, bytearray)) else v)
                for k, v in img.info.items()
            }
        
        result = {
            "metadata": metadata,
            "has_exif": "exif" in metadata
        }
        
        logging.info(f"✅ Image metadata extracted")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"file_path": str(path)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Metadata extraction failed: {str(e)}"
        logging.error(f"Metadata error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "metadata_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
