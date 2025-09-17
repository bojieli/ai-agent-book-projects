"""
Configuration for Log Sanitization with Local LLM
"""

import os
from pathlib import Path

# Ollama Configuration
OLLAMA_MODEL = "qwen3:8b"  # Using larger model for better accuracy
OLLAMA_TEMPERATURE = 0.1  # Low temperature for consistent detection

# Paths
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Performance Metrics Configuration
METRICS_FILE = OUTPUT_DIR / "performance_metrics.json"

# Evaluation Framework Path
EVAL_FRAMEWORK_PATH = PROJECT_ROOT.parent / "user-memory-evaluation"

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
