"""
Configuration for Log Sanitization with Local LLM
"""

import os
from pathlib import Path

# Ollama Configuration
# 默认使用 0.6B 超小模型，呼应本章“小模型也能胜任结构化任务”的论点，
# 且可在 CPU / 消费级设备上运行；可用 --model 覆盖为 qwen3:1.7b、qwen3:4b 等。
OLLAMA_MODEL = "qwen3:0.6b"
OLLAMA_TEMPERATURE = 0.1  # Low temperature for consistent detection

# Paths
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Performance Metrics Configuration
METRICS_FILE = OUTPUT_DIR / "performance_metrics.json"

# Evaluation Framework Path
# The user-memory-evaluation framework lives in chapter3, not chapter2.
# PROJECT_ROOT = chapter2/log-sanitization, so go up two levels to the repo root.
EVAL_FRAMEWORK_PATH = PROJECT_ROOT.parent.parent / "chapter3" / "user-memory-evaluation"

# System Prompt for PII Detection
SYSTEM_PROMPT = """You are a privacy protection agent that detects Level 3 PII.

Level 3 PII includes:
- Social Security Numbers (SSN) - format: XXX-XX-XXXX or XXXXXXXXX
- Credit Card Numbers - format: XXXX XXXX XXXX XXXX or 16 digits
- Credit Card Expiry Date and CVV
- Bank Account Numbers
- Full Residential Addresses
- Medical Record Numbers
- Medical Diagnoses and Treatment Details
- Prescription Information
- Driver's License Numbers
- Passport Numbers
- Financial PINs
- Tax ID Numbers
- Health Insurance IDs
- Biometric Data
- Usernames for Financial Accounts
- Passwords

Analyze the conversation and return a JSON with the exact PII values found. NEVER use placeholders. Simply return the PII values found."""

USER_PROMPT_TEMPLATE = """Analyze the following conversation for Level 3 PII:

{conversation_text}"""

# JSON Schema for structured output
PII_DETECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "pii_values": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Array of exact PII values found in the conversation. NEVER use placeholders."
        }
    },
    "required": ["pii_values"]
}
