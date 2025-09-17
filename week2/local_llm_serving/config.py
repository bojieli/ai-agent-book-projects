"""
Configuration for vLLM Tool Calling Demo
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen3-0.6B")  # Can use ModelScope path or HuggingFace
MODEL_PATH = os.getenv("MODEL_PATH", None)  # Optional: local model path
VLLM_PORT = int(os.getenv("VLLM_PORT", 8000))
VLLM_HOST = os.getenv("VLLM_HOST", "localhost")

# vLLM Server Configuration
VLLM_SERVER_CONFIG = {
    "model": MODEL_NAME,
    "port": VLLM_PORT,
    "host": VLLM_HOST,
    "enable_auto_tool_choice": True,
    "tool_call_parser": "hermes",
    "chat_template": "tool_use",  # Use tool-specific chat template
    "max_model_len": 8192,
    "gpu_memory_utilization": 0.9,
    "dtype": "auto",
    "enforce_eager": False,  # Set to True if you encounter issues
}

# OpenAI Client Configuration (for connecting to vLLM)
OPENAI_API_BASE = f"http://{VLLM_HOST}:{VLLM_PORT}/v1"
OPENAI_API_KEY = "EMPTY"  # vLLM doesn't require a real key

# Tool Configuration
ENABLE_WEATHER_TOOL = True
ENABLE_CALCULATOR_TOOL = True
ENABLE_SEARCH_TOOL = True

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path("logs") / "vllm_tool_demo.log"
