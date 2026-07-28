"""
Multimodal Agent with Multiple Extraction Techniques
Supports native multimodality, extract to text, and multimodal tools
"""

import os
import sys
import json
import base64
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Union, Generator, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
import mimetypes
from datetime import datetime

# Google Gemini imports
from google import genai
from google.genai import types

# OpenAI imports
from openai import OpenAI, AsyncOpenAI

from config import Config, ExtractionMode, Provider, ModelConfig, _openrouter_model_id


@dataclass
class Message:
    """Unified message format"""
    role: str  # "system", "user", "assistant", "tool"
    content: Union[str, List[Dict[str, Any]]]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {"role": self.role, "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class MultimodalContent:
    """Container for multimodal content"""
    type: str  # "pdf", "image", "audio"
    data: Optional[bytes] = None
    path: Optional[str] = None
    url: Optional[str] = None
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # 自动补全 MIME 类型：优先按文件名推断，再按声明的模态兜底。
        # 否则原生 OpenAI / Doubao 图像请求会拼出 "data:None;base64,..." 导致 400 错误。
        if not self.mime_type and self.path:
            guessed = mimetypes.guess_type(self.path)[0]
            if guessed:
                self.mime_type = guessed
        if not self.mime_type:
            self.mime_type = {
                "pdf": "application/pdf",
                "image": "image/jpeg",
                "audio": "audio/mpeg",
            }.get(self.type)

    def get_bytes(self) -> bytes:
        """Get content as bytes"""
        if self.data:
            return self.data
        elif self.path:
            return Path(self.path).read_bytes()
        elif self.url:
            response = httpx.get(self.url)
            return response.content
        else:
            raise ValueError("No content source available")
            
    def get_base64(self) -> str:
        """Get content as base64 encoded string"""
        return base64.b64encode(self.get_bytes()).decode('utf-8')


class MultimodalTools:
    """Tools for multimodal content analysis"""
    
    def __init__(self, agent: 'MultimodalAgent'):
        self.agent = agent
        
    async def analyze_image(self, image_path: str, query: str) -> str:
        """Analyze an image with a specific query"""
        content = MultimodalContent(
            type="image",
            path=image_path,
            mime_type=mimetypes.guess_type(image_path)[0] or "image/jpeg"
        )
        
        # Use GPT-5 or Doubao for image analysis
        if self.agent.config.get_model_config(self.agent.current_model).provider == Provider.DOUBAO:
            return await self._analyze_with_doubao(content, query)
        else:
            return await self._analyze_with_openai(content, query)
            
    async def analyze_audio(self, audio_path: str, query: str) -> str:
        """Analyze audio with a specific query"""
        content = MultimodalContent(
            type="audio",
            path=audio_path,
            mime_type=mimetypes.guess_type(audio_path)[0] or "audio/mpeg"
        )
        
        # Use Gemini for audio analysis
        return await self._analyze_with_gemini_audio(content, query)
        
    async def analyze_pdf(self, pdf_path: str, query: str) -> str:
        """Analyze a PDF document with a specific query"""
        content = MultimodalContent(
            type="pdf",
            path=pdf_path,
            mime_type="application/pdf"
        )
        
        # Use Gemini for PDF analysis
        return await self._analyze_with_gemini_pdf(content, query)
        
    async def _analyze_with_openai(self, content: MultimodalContent, query: str) -> str:
        """Use OpenAI (or OpenRouter fallback) for content analysis"""
        cfg = self.agent.config
        # 视觉默认 gpt-5.6-luna（视觉可用）；直连 gpt-5.6 需组织实名，故有 OpenRouter key 时优先走 OpenRouter
        if cfg.openrouter_api_key:
            client = AsyncOpenAI(api_key=cfg.openrouter_api_key, base_url=cfg.openrouter_base_url)
            model = _openrouter_model_id("gpt-5.6-luna")
        elif cfg.openai_api_key:
            client = AsyncOpenAI(api_key=cfg.openai_api_key)
            model = "gpt-5.6-luna"
        else:
            raise RuntimeError("需要 OPENAI_API_KEY 或 OPENROUTER_API_KEY 才能进行视觉分析")

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{content.mime_type};base64,{content.get_base64()}"
                    }
                }
            ]
        }]

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.agent.config.temperature
        )

        return response.choices[0].message.content
        
    async def _analyze_with_doubao(self, content: MultimodalContent, query: str) -> str:
        """Use Doubao for content analysis"""
        client = AsyncOpenAI(
            api_key=self.agent.config.doubao_api_key,
            base_url=self.agent.config.models["doubao-1.6"].base_url
        )
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{content.mime_type};base64,{content.get_base64()}"
                    }
                }
            ]
        }]
        
        response = await client.chat.completions.create(
            model="Doubao-1.6",
            messages=messages,
            temperature=self.agent.config.temperature
        )
        
        return response.choices[0].message.content
        
    async def _analyze_with_gemini_audio(self, content: MultimodalContent, query: str) -> str:
        """Use Gemini for audio analysis with thinking mode"""
        client = genai.Client(api_key=self.agent.config.gemini_api_key)
        
        audio_data = content.get_bytes()
        
        # Always enable thinking mode
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True
            )
        )
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                query,
                types.Part.from_bytes(
                    data=audio_data,
                    mime_type=content.mime_type
                )
            ],
            config=config
        )
        
        # Extract and print thinking content, return only the answer
        result = ""
        first_thinking = True
        first_response = True
        
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if not part.text:
                    continue
                if part.thought:
                    if first_thinking:
                        print("\n[Gemini Thinking] ", end="", flush=True)
                        first_thinking = False
                    print(part.text, end="", flush=True)
                else:
                    if first_response:
                        if not first_thinking:  # We had thinking output
                            print()  # End the thinking line
                        print("[Gemini Response]", flush=True)
                        first_response = False
                    # Don't print response text, just collect it
                    result += part.text
        else:
            result = response.text
        
        print("\n", flush=True)  # End the output line
        return result
        
    async def _analyze_with_gemini_pdf(self, content: MultimodalContent, query: str) -> str:
        """Use Gemini for PDF analysis with thinking mode"""
        client = genai.Client(api_key=self.agent.config.gemini_api_key)
        
        # Get PDF bytes directly - no base64 encoding needed with new SDK
        pdf_data = content.get_bytes()
        
        # Always enable thinking mode
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True
            )
        )
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf'
                ),
                query
            ],
            config=config
        )
        
        # Extract and print thinking content, return only the answer
        result = ""
        first_thinking = True
        first_response = True
        
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if not part.text:
                    continue
                if part.thought:
                    if first_thinking:
                        print("\n[Gemini Thinking] ", end="", flush=True)
                        first_thinking = False
                    print(part.text, end="", flush=True)
                else:
                    if first_response:
                        if not first_thinking:  # We had thinking output
                            print()  # End the thinking line
                        print("[Gemini Response]", flush=True)
                        first_response = False
                    # Don't print response text, just collect it
                    result += part.text
        else:
            result = response.text
        
        print("\n", flush=True)  # End the output line
        return result


class MultimodalAgent:
    """Main agent class supporting multiple extraction modes"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        mode: Optional[ExtractionMode] = None,
        enable_tools: bool = False
    ):
        self.config = Config()
        self.current_model = model or self.config.default_model
        self.extraction_mode = mode or self.config.default_mode
        self.enable_multimodal_tools = False
        
        # Conversation history
        self.conversation_history: List[Message] = []
        
        # Store current content path for reference
        self.current_content_path: Optional[str] = None
        
        # Multimodal tools
        self.tools: Optional[MultimodalTools] = None
        
        # Tool definitions for OpenAI-style function calling
        self.tool_definitions: List[Dict[str, Any]] = []
        self.set_multimodal_tools_enabled(enable_tools)

    def set_multimodal_tools_enabled(self, enabled: bool) -> None:
        """Keep the multimodal tool state in sync."""
        self.enable_multimodal_tools = enabled
        if not enabled:
            self.tools = None
            return

        if self.tools is None:
            self.tools = MultimodalTools(self)

        if not self.tool_definitions:
            self.tool_definitions = [
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_image",
                        "description": "Analyze an image with a specific query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "image_path": {
                                    "type": "string",
                                    "description": "Path to the image file"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Question or analysis request about the image"
                                }
                            },
                            "required": ["image_path", "query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_audio",
                        "description": "Analyze audio content with a specific query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "audio_path": {
                                    "type": "string",
                                    "description": "Path to the audio file"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Question or analysis request about the audio"
                                }
                            },
                            "required": ["audio_path", "query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_pdf",
                        "description": "Analyze a PDF document with a specific query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "pdf_path": {
                                    "type": "string",
                                    "description": "Path to the PDF file"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Question or analysis request about the PDF"
                                }
                            },
                            "required": ["pdf_path", "query"]
                        }
                    }
                }
            ]
            
    def add_message(self, message: Message):
        """Add a message to conversation history"""
        self.conversation_history.append(message)
        
    async def process_multimodal_content(
        self,
        content: MultimodalContent,
        query: Optional[str] = None
    ) -> str:
        """Process multimodal content based on extraction mode"""
        
        if self.extraction_mode == ExtractionMode.NATIVE:
            return await self._process_native(content, query)
        elif self.extraction_mode == ExtractionMode.EXTRACT_TO_TEXT:
            return await self._extract_to_text(content, query)
        else:
            raise ValueError(f"Unknown extraction mode: {self.extraction_mode}")
            
    async def _process_native(self, content: MultimodalContent, query: Optional[str]) -> str:
        """Process using native multimodal capabilities"""
        model_config = self.config.get_model_config(self.current_model)
        
        if not model_config.supports_native_multimodal:
            raise ValueError(f"Model {self.current_model} doesn't support native multimodality")

        # Universal OpenRouter fallback: the model's own provider key is missing
        # but OPENROUTER_API_KEY is present -> route via OpenRouter (OpenAI-compat).
        if self.config.use_openrouter(model_config.provider):
            return await self._process_native_openrouter(model_config, content, query)

        if model_config.provider == Provider.GEMINI:
            return await self._process_native_gemini(content, query)
        elif model_config.provider == Provider.OPENAI:
            return await self._process_native_openai(content, query)
        elif model_config.provider == Provider.DOUBAO:
            return await self._process_native_doubao(content, query)
        else:
            raise ValueError(f"Unknown provider: {model_config.provider}")

    async def _process_native_openrouter(self, model_config: ModelConfig, content: MultimodalContent, query: Optional[str]) -> str:
        """Process content via OpenRouter's OpenAI-compatible endpoint.
        Images are sent as native vision input; other types are extracted to
        text first (OpenRouter has no audio-transcription / native-PDF path)."""
        client_kwargs, model_name = self.config.openai_client_args(model_config)
        client = AsyncOpenAI(**client_kwargs)

        message_content = []
        if query:
            message_content.append({"type": "text", "text": query})

        if content.type == "image":
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{content.mime_type};base64,{content.get_base64()}"
                }
            })
        else:
            extracted = await self._extract_single_content(content)
            message_content.append({"type": "text", "text": extracted})

        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": message_content}],
            temperature=self.config.temperature
        )
        return response.choices[0].message.content
            
    async def _process_native_gemini(self, content: MultimodalContent, query: Optional[str]) -> str:
        """Process using Gemini's native multimodal API with thinking mode"""
        client = genai.Client(api_key=self.config.gemini_api_key)
        
        # Build content parts
        contents = []
        
        # Add the multimodal content using types.Part.from_bytes
        content_bytes = content.get_bytes()
        
        if content.type == "pdf":
            mime_type = "application/pdf"
        elif content.type == "image":
            mime_type = content.mime_type or "image/jpeg"
        elif content.type == "audio":
            mime_type = content.mime_type or "audio/mpeg"
        else:
            mime_type = content.mime_type
            
        contents.append(types.Part.from_bytes(
            data=content_bytes,
            mime_type=mime_type
        ))
        
        # Add the query
        if query:
            contents.append(query)
        else:
            contents.append(f"Please analyze this {content.type} content.")
        
        # Always enable thinking mode
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True
            )
        )
            
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=contents,
            config=config
        )
        
        # Extract and print thinking content, return only the answer
        result = ""
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'thought') and part.thought and part.text:
                    print(f"\n💭 [Gemini Thinking]: {part.text}\n", flush=True)
                elif part.text:
                    result += part.text
        else:
            result = response.text
            
        return result
        
    async def _process_native_openai(self, content: MultimodalContent, query: Optional[str]) -> str:
        """Process using OpenAI's native multimodal API"""
        client = AsyncOpenAI(api_key=self.config.openai_api_key)
        
        messages = []
        message_content = []
        
        if query:
            message_content.append({"type": "text", "text": query})
            
        # OpenAI primarily supports images natively
        if content.type == "image":
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{content.mime_type};base64,{content.get_base64()}"
                }
            })
        else:
            # For other types, we'll need to extract to text first
            extracted = await self._extract_single_content(content)
            message_content.append({"type": "text", "text": extracted})
            
        messages.append({"role": "user", "content": message_content})
        
        response = await client.chat.completions.create(
            model=self.current_model,
            messages=messages,
            temperature=self.config.temperature
        )
        
        return response.choices[0].message.content
        
    async def _process_native_doubao(self, content: MultimodalContent, query: Optional[str]) -> str:
        """Process using Doubao's native multimodal API"""
        client = AsyncOpenAI(
            api_key=self.config.doubao_api_key,
            base_url=self.config.models["doubao-1.6"].base_url
        )
        
        messages = []
        message_content = []
        
        if query:
            message_content.append({"type": "text", "text": query})
            
        # Doubao supports images natively
        if content.type == "image":
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{content.mime_type};base64,{content.get_base64()}"
                }
            })
        else:
            # For other types, extract to text first
            extracted = await self._extract_single_content(content)
            message_content.append({"type": "text", "text": extracted})
            
        messages.append({"role": "user", "content": message_content})
        
        response = await client.chat.completions.create(
            model="Doubao-1.6",
            messages=messages,
            temperature=self.config.temperature
        )
        
        return response.choices[0].message.content
        
    async def _extract_to_text(self, content: MultimodalContent, query: Optional[str]) -> str:
        """Extract multimodal content to text first"""
        extracted_text = await self._extract_single_content(content)
        content.extracted_text = extracted_text
        
        # Now process the query with extracted text
        if query:
            return await self._answer_with_context(extracted_text, query)
        else:
            return extracted_text
            
    async def _extract_single_content(self, content: MultimodalContent) -> str:
        """Extract a single piece of content to text"""
        if content.type == "pdf":
            return await self._extract_pdf_to_text(content)
        elif content.type == "image":
            return await self._extract_image_to_text(content)
        elif content.type == "audio":
            return await self._extract_audio_to_text(content)
        else:
            raise ValueError(f"Unknown content type: {content.type}")
            
    async def _extract_pdf_to_text(self, content: MultimodalContent) -> str:
        """Extract PDF to text using OCR with thinking mode"""
        # Use Gemini for PDF extraction with new SDK
        client = genai.Client(api_key=self.config.gemini_api_key)
        
        pdf_data = content.get_bytes()
        
        # Always enable thinking mode
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True
            )
        )
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf'
                ),
                "Extract all text content from this PDF document, preserving structure and formatting."
            ],
            config=config
        )
        
        # Extract and print thinking content, return only the answer
        result = ""
        first_thinking = True
        first_response = True
        
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if not part.text:
                    continue
                if part.thought:
                    if first_thinking:
                        print("\n[Gemini Thinking] ", end="", flush=True)
                        first_thinking = False
                    print(part.text, end="", flush=True)
                elif part.text:
                    if first_response:
                        if not first_thinking:  # We had thinking output
                            print()  # End the thinking line
                        print("[Gemini Response] ", end="", flush=True)
                        first_response = False
                    print(part.text, end="", flush=True)
                    result += part.text
        else:
            result = response.text
        
        print("\n", flush=True)  # End the output line
        return result
        
    async def _extract_image_to_text(self, content: MultimodalContent) -> str:
        """Extract image to text description"""
        # 图像转文本：gpt-5.6-luna（优先 OpenRouter，直连 5.6 需组织实名）/ Doubao / OpenRouter 兜底
        if self.config.openrouter_api_key:
            client = AsyncOpenAI(
                api_key=self.config.openrouter_api_key,
                base_url=self.config.openrouter_base_url
            )
            model = _openrouter_model_id("gpt-5.6-luna")
        elif self.config.openai_api_key:
            client = AsyncOpenAI(api_key=self.config.openai_api_key)
            model = "gpt-5.6-luna"
        elif self.config.doubao_api_key:
            client = AsyncOpenAI(
                api_key=self.config.doubao_api_key,
                base_url=self.config.models["doubao-1.6"].base_url
            )
            model = "Doubao-1.6"
        else:
            raise RuntimeError("需要 OPENAI_API_KEY / OPENROUTER_API_KEY / DOUBAO_API_KEY 才能进行图像转文本")
            
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in detail, including all text, objects, and contextual information."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{content.mime_type};base64,{content.get_base64()}"
                    }
                }
            ]
        }]
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    async def _extract_audio_to_text(self, content: MultimodalContent) -> str:
        """Extract audio to text transcript"""
        # Option 1: Use Whisper API
        if self.config.openai_api_key:
            client = AsyncOpenAI(api_key=self.config.openai_api_key)
            
            # Save audio temporarily for Whisper
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(content.get_bytes())
                tmp_path = tmp.name
                
            try:
                with open(tmp_path, "rb") as audio_file:
                    transcript = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return transcript.text
            finally:
                os.unlink(tmp_path)
        else:
            # Option 2: Use Gemini for audio understanding
            client = genai.Client(api_key=self.config.gemini_api_key)
            
            audio_data = content.get_bytes()
            
            # Always enable thinking mode
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True
                )
            )
            
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[
                    "Transcribe this audio content completely and accurately.",
                    types.Part.from_bytes(
                        data=audio_data,
                        mime_type=content.mime_type or "audio/mpeg"
                    )
                ],
                config=config
            )
            
            # Extract and print thinking content, return only the answer
            result = ""
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought and part.text:
                        print(f"\n💭 [Gemini Thinking]: {part.text}\n", flush=True)
                    elif part.text:
                        result += part.text
            else:
                result = response.text
            
            return result
            
    async def _answer_with_context(self, context: str, query: str) -> str:
        """Answer a query given extracted text context"""
        model_config = self.config.get_model_config(self.current_model)
        
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

        # Universal OpenRouter fallback (primary provider key absent).
        if self.config.use_openrouter(model_config.provider):
            client_kwargs, model_name = self.config.openai_client_args(model_config)
            client = AsyncOpenAI(**client_kwargs)
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature
            )
            return response.choices[0].message.content

        if model_config.provider == Provider.GEMINI:
            client = genai.Client(api_key=self.config.gemini_api_key)
            
            # Always enable thinking mode
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True
                )
            )
            
            response = client.models.generate_content(
                model=model_config.model_name,
                contents=[prompt],
                config=config
            )
            
            # Extract and print thinking content, return only the answer
            result = ""
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought and part.text:
                        print(f"\n💭 [Gemini Thinking]: {part.text}\n", flush=True)
                    elif part.text:
                        result += part.text
            else:
                result = response.text
                
            return result
        else:
            # Use OpenAI-compatible API
            if model_config.provider == Provider.OPENAI:
                client = AsyncOpenAI(api_key=self.config.openai_api_key)
            else:  # Doubao
                client = AsyncOpenAI(
                    api_key=self.config.doubao_api_key,
                    base_url=model_config.base_url
                )
                
            response = await client.chat.completions.create(
                model=model_config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature
            )
            
            return response.choices[0].message.content
            
    async def chat(
        self,
        message: str,
        multimodal_content: Optional[MultimodalContent] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Main chat interface with streaming support"""
        
        # Add user message to history
        self.add_message(Message(role="user", content=message))
        
        # Process new multimodal content if provided (for native mode)
        # In extract mode, content should already be in conversation history via load_and_extract_content
        if multimodal_content and self.extraction_mode == ExtractionMode.EXTRACT_TO_TEXT:
            # If new content is provided inline during chat, extract and add to the current message
            extracted = await self._extract_single_content(multimodal_content)
            
            # Update the last message with extracted context
            enhanced_message = f"[Context from {multimodal_content.type}]:\n{extracted}\n\n{message}"
            self.conversation_history[-1].content = enhanced_message
                
        # Get response based on model
        model_config = self.config.get_model_config(self.current_model)
        
        if stream:
            async for chunk in self._stream_response(model_config, multimodal_content):
                yield chunk
        else:
            response = await self._get_response(model_config)
            yield response
            
    async def _stream_response(self, model_config: ModelConfig, multimodal_content: Optional[MultimodalContent] = None) -> AsyncGenerator[str, None]:
        """Stream response from the model"""
        # Universal OpenRouter fallback -> use the OpenAI-compatible stream path.
        if self.config.use_openrouter(model_config.provider):
            async for chunk in self._stream_openai_response(model_config):
                yield chunk
        elif model_config.provider == Provider.GEMINI:
            async for chunk in self._stream_gemini_response(multimodal_content):
                yield chunk
        else:
            async for chunk in self._stream_openai_response(model_config):
                yield chunk
                
    async def _stream_gemini_response(self, multimodal_content: Optional[MultimodalContent] = None) -> AsyncGenerator[str, None]:
        """Stream response from Gemini with thinking mode for debugging"""
        client = genai.Client(api_key=self.config.gemini_api_key)
        
        # Build full conversation history for Gemini
        # Format: alternating user/assistant messages as a single string
        conversation_parts = []
        
        for msg in self.conversation_history:
            if msg.role == "user":
                conversation_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                conversation_parts.append(f"Assistant: {msg.content}")
            # System messages can be included as context
            elif msg.role == "system":
                conversation_parts.append(f"System: {msg.content}")
        
        # Join all conversation parts
        full_conversation = "\n\n".join(conversation_parts)
        
        if not full_conversation:
            return
            
        # Build content list
        contents = []
        
        # Add multimodal content if present and in native mode
        if multimodal_content and self.extraction_mode == ExtractionMode.NATIVE:
            # Add the multimodal data first
            content_bytes = multimodal_content.get_bytes()
            
            if multimodal_content.type == "pdf":
                mime_type = "application/pdf"
            elif multimodal_content.type == "image":
                mime_type = multimodal_content.mime_type or "image/jpeg"
            elif multimodal_content.type == "audio":
                mime_type = multimodal_content.mime_type or "audio/mpeg"
            else:
                mime_type = multimodal_content.mime_type
                
            contents.append(types.Part.from_bytes(
                data=content_bytes,
                mime_type=mime_type
            ))
            
        # Add the full conversation as context
        contents.append(full_conversation)
        
        # Always enable thinking mode for transparency and debugging
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True
            )
        )
        
        # Stream the response - note: generate_content_stream returns a regular generator
        response = client.models.generate_content_stream(
            model=self.config.get_model_config(self.current_model).model_name,
            contents=contents,
            config=config
        )
        
        full_response = ""
        first_thinking = True
        first_response = True
        
        # Use regular for loop since the SDK returns a regular generator
        for chunk in response:
            # Handle thinking mode output
            if hasattr(chunk, 'candidates') and chunk.candidates:
                for part in chunk.candidates[0].content.parts:
                    if not part.text:
                        continue
                    if part.thought:
                        # Print thinking header once, then content without newlines
                        if first_thinking:
                            print("\n[Gemini Thinking] ", end="", flush=True)
                            first_thinking = False
                        print(part.text, end="", flush=True)
                    else:
                        # Print response header once for debugging
                        if first_response:
                            if not first_thinking:  # We had thinking output
                                print()  # End the thinking line
                            print("[Gemini Response]", flush=True)
                            first_response = False
                        # Yield regular response text to the user (don't print, it will be printed in main.py)
                        yield part.text
                        full_response += part.text
            elif chunk.text:
                # Fallback for standard streaming
                if first_response:
                    if not first_thinking:  # We had thinking output
                        print()  # End the thinking line
                    print("[Gemini Response]", flush=True)
                    first_response = False
                # Yield text without printing (will be printed in main.py)
                yield chunk.text
                full_response += chunk.text
        
        # End the console output line
        print("\n", flush=True)
                
        # Add assistant response to history (excluding thinking parts)
        self.add_message(Message(role="assistant", content=full_response))
        
    async def _stream_openai_response(self, model_config: ModelConfig) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI-compatible API (direct or via OpenRouter)"""
        client_kwargs, model_name = self.config.openai_client_args(model_config)
        client = AsyncOpenAI(**client_kwargs)

        # Convert conversation history to OpenAI format
        messages = [msg.to_dict() for msg in self.conversation_history]

        # Add tools if enabled
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "stream": True
        }
        
        if self.enable_multimodal_tools and self.tool_definitions:
            kwargs["tools"] = self.tool_definitions
            kwargs["tool_choice"] = "auto"
            
        response = await client.chat.completions.create(**kwargs)
        
        full_response = ""
        tool_calls = []
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield content
                full_response += content
                
            # Handle tool calls
            if chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    # Accumulate tool call information
                    if tool_call.index >= len(tool_calls):
                        tool_calls.append({
                            "id": tool_call.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })
                    
                    if tool_call.function.name:
                        tool_calls[tool_call.index]["function"]["name"] = tool_call.function.name
                    if tool_call.function.arguments:
                        tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                        
        # Process tool calls if any
        if tool_calls:
            # Add assistant message with tool calls
            self.add_message(Message(
                role="assistant",
                content=full_response or "",
                tool_calls=tool_calls
            ))
            
            # Execute tools
            for tool_call in tool_calls:
                tool_result = await self._execute_tool(tool_call)
                
                # Add tool result to history
                self.add_message(Message(
                    role="tool",
                    content=tool_result,
                    tool_call_id=tool_call["id"],
                    name=tool_call["function"]["name"]
                ))
                
                # Stream tool result
                yield f"\n[Tool: {tool_call['function']['name']}]\n{tool_result}\n"
                
            # Get final response after tool execution
            async for chunk in self._stream_openai_response(model_config):
                yield chunk
        else:
            # Add assistant response to history
            self.add_message(Message(role="assistant", content=full_response))
            
    async def _execute_tool(self, tool_call: Dict[str, Any]) -> str:
        """Execute a tool call"""
        function_name = tool_call["function"]["name"]
        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return f"Error: invalid JSON arguments for tool '{function_name}'"
        
        if function_name == "analyze_image":
            image_path = arguments.get("image_path")
            query = arguments.get("query")
            if not image_path or not query:
                return "Error: analyze_image requires 'image_path' and 'query' arguments"
            return await self.tools.analyze_image(image_path, query)
        elif function_name == "analyze_audio":
            audio_path = arguments.get("audio_path")
            query = arguments.get("query")
            if not audio_path or not query:
                return "Error: analyze_audio requires 'audio_path' and 'query' arguments"
            return await self.tools.analyze_audio(audio_path, query)
        elif function_name == "analyze_pdf":
            pdf_path = arguments.get("pdf_path")
            query = arguments.get("query")
            if not pdf_path or not query:
                return "Error: analyze_pdf requires 'pdf_path' and 'query' arguments"
            return await self.tools.analyze_pdf(pdf_path, query)
        else:
            return f"Unknown tool: {function_name}"
            
    async def _get_response(self, model_config: ModelConfig) -> str:
        """Get non-streaming response"""
        full_response = ""
        async for chunk in self._stream_response(model_config):
            full_response += chunk
        return full_response
        
    def reset_conversation(self):
        """Clear conversation history and current content"""
        self.conversation_history = []
        self.current_content_path = None
        
    async def load_and_extract_content(self, content: MultimodalContent) -> str:
        """Load and extract content if in extract mode"""
        # Store the current content path
        self.current_content_path = content.path
        
        if self.extraction_mode == ExtractionMode.EXTRACT_TO_TEXT:
            # Extract content immediately
            print("Extracting content to text...", flush=True)
            extracted_text = await self._extract_single_content(content)
            
            # Add the extracted content directly to conversation history as a user message
            # This provides context for all subsequent questions
            context_msg = f"[Document: {content.path}]\n\n{extracted_text}"
            self.add_message(Message(role="user", content=context_msg))
            
            return f"Extracted {content.type} content and added to conversation context. Ready for questions."
        else:
            # In native mode, just note that content is loaded
            return f"Loaded {content.type}: {content.path}"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history in OpenAI format"""
        return [msg.to_dict() for msg in self.conversation_history]
