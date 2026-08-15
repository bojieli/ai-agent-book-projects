import hashlib
import hmac
import json
import re
import secrets
import string

VERSION = "1.1.0-candidate"

# Store tokens for confirmation
confirmation_tokens = {}

# Define high-risk tool patterns
HIGH_RISK_TOOLS = {
    "delete_file": lambda args: True,
    "git_push": lambda args: args.get('force', False),
    "sql_query": lambda args: re.search(r"\b(DROP TABLE|TRUNCATE|DELETE)\b", args.get('query', ''), re.IGNORECASE) is not None,
    "run_shell": lambda args: re.search(r"\b(rm -rf|mkfs|shutdown|dd if=)\b", args.get('command', ''), re.IGNORECASE) is not None,
}

def requires_confirmation(tool_name, args=None):
    if tool_name in HIGH_RISK_TOOLS:
        return HIGH_RISK_TOOLS[tool_name](args)
    return False


def issue_confirmation(tool_name, args=None):
    token = secrets.token_hex(16)
    confirmation_tokens[token] = (tool_name, args)
    return token


def dispatch(tool_name, args=None, *, execute, confirm_token=None):
    if requires_confirmation(tool_name, args):
        if confirm_token is None:
            return {
                "status": "pending_confirmation",
                "reason": "High-risk operation requires confirmation."
            }
        if confirm_token in confirmation_tokens:
            expected_tool, expected_args = confirmation_tokens[confirm_token]
            if expected_tool == tool_name and expected_args == args:
                del confirmation_tokens[confirm_token]  # Consume the token
                return {
                    "status": "executed",
                    "confirmed": true,
                    "result": execute(tool_name, args)
                }
            else:
                return {
                    "status": "rejected",
                    "reason": "Invalid or already used token."
                }
        else:
            return {
                "status": "rejected",
                "reason": "Invalid or already used token."
            }
    else:
        return {
            "status": "executed",
            "confirmed": false,
            "result": execute(tool_name, args)
        }
