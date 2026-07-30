"""LLM helper for safety checks, approval, and summarization."""

import json
import datetime as dt
import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
from openai import OpenAI
from config import Config


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


def _parse_json_response(content):
    """Parse a JSON object out of an LLM reply, tolerating markdown fences.

    Reasoning models (notably kimi-k3) reliably return valid JSON but wrap it
    in a ```json ... ``` code fence, so a bare json.loads() fails with
    "Expecting value: line 1 column 1". Strip an optional fence and, as a last
    resort, slice from the first '{' to the last '}' before parsing."""
    text = (content or "").strip()
    if text.startswith("```"):
        # Drop the opening fence line (``` or ```json) and the closing fence.
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


class LLMHelper:
    """Helper class for LLM-based operations."""
    
    def __init__(self):
        """Initialize the LLM helper.

        The OpenAI-compatible client is created lazily on first use so that
        execution tools which do not need an LLM (e.g. Python code execution
        with local syntax checking, terminal commands, file writes) work
        offline without any API key configured. Methods that actually call
        the LLM (approval, summarization, non-Python syntax check) will raise
        or fail-safe if no key is available.
        """
        self.client = None
        self.model = None
        self.provider = None

    def _record_receipt(self, purpose: str, request: dict, response, latency: float) -> None:
        """Checkpoint credential-free raw provider evidence after every call."""
        target = os.getenv("EXECUTION_LLM_RECEIPT_PATH")
        if not target:
            return
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        usage = getattr(response, "usage", None)
        choice = response.choices[0]
        row = {
            "purpose": purpose,
            "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "provider": self.provider,
            "request": request,
            "response": {
                "id": getattr(response, "id", None),
                "model": getattr(response, "model", None),
                "finish_reason": getattr(choice, "finish_reason", None),
                "content": choice.message.content,
            },
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
            "latency_seconds": round(latency, 3),
        }
        existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
        existing.append(row)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def _ensure_client(self) -> None:
        """Create the LLM client on first use (raises if no API key)."""
        if self.client is None:
            llm_config = Config.get_llm_config()
            # All providers use OpenAI-compatible API
            self.client = OpenAI(
                api_key=llm_config["api_key"],
                base_url=llm_config.get("base_url")
            )
            self.model = llm_config["model"]
            self.provider = llm_config["provider"]
    
    def request_approval(
        self, 
        operation: str, 
        details: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Request LLM approval for a dangerous operation.
        
        Args:
            operation: The operation name
            details: Details about the operation
            
        Returns:
            Tuple of (approved, reason)
        """
        prompt = f"""You are a safety reviewer for an AI agent execution system.
Review the following operation and determine if it should be approved.

Operation: {operation}
Details: {json.dumps(details, indent=2)}

Analyze the operation for:
1. Potential data loss or destructive actions
2. Security risks
3. Resource consumption concerns
4. Compliance with best practices

Respond in JSON format:
{{
    "approved": true/false,
    "reason": "Brief explanation of your decision",
    "risk_level": "low/medium/high",
    "recommendations": ["List of recommendations if any"]
}}
"""
        
        try:
            self._ensure_client()
            request = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cautious safety reviewer. Approve operations that are safe and reject risky ones."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": _reasoning_safe_temperature(self.model, 0.1),
                "max_tokens": Config.MAX_TOKENS,
            }
            started = time.perf_counter()
            response = self.client.chat.completions.create(**request)
            self._record_receipt("dangerous_operation_review", request, response,
                                 time.perf_counter() - started)

            result = _parse_json_response(response.choices[0].message.content)
            return result["approved"], result["reason"]
            
        except Exception as e:
            # If approval check fails, default to rejection for safety
            return False, f"Approval check failed: {str(e)}"
    
    def summarize_output(
        self, 
        tool_name: str,
        output: str
    ) -> str:
        """
        Summarize complex tool output.
        
        Args:
            tool_name: Name of the tool that produced the output
            output: The output to summarize
            
        Returns:
            Summarized output
        """
        
        prompt = f"""Summarize the following output from the '{tool_name}' tool.
Focus on:
1. Key results or findings
2. Errors or warnings
3. Important patterns or insights
4. Actionable information

Output to summarize:
{output[:5000]}  # Limit input to avoid token limits

Provide a concise summary that captures the essential information."""
        
        try:
            self._ensure_client()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at summarizing technical output. Be concise and focus on actionable information."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=_reasoning_safe_temperature(self.model, 0.1),
                max_tokens=Config.MAX_TOKENS
            )

            summary = response.choices[0].message.content
            return f"[SUMMARIZED OUTPUT]\n{summary}\n\n[Original output length: {len(output)} characters]"

        except Exception as e:
            return f"[SUMMARIZATION FAILED: {str(e)}]\n\n{output[:Config.MAX_OUTPUT_LENGTH]}..."
    
    def analyze_error(
        self,
        tool_name: str,
        command: str,
        error_output: str
    ) -> str:
        """
        Analyze error output and provide suggestions.
        
        Args:
            tool_name: Name of the tool that produced the error
            command: The command or code that failed
            error_output: The error output
            
        Returns:
            Analysis with suggestions
        """
        prompt = f"""Analyze the following error from the '{tool_name}' tool:

Command/Code:
{command}

Error Output:
{error_output[:3000]}

Provide:
1. Root cause analysis
2. Suggested fixes
3. Prevention strategies

Be concise and practical."""
        
        try:
            self._ensure_client()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert debugger. Analyze errors and provide clear, actionable solutions."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=_reasoning_safe_temperature(self.model, 0.2),
                max_tokens=Config.MAX_TOKENS
            )

            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analysis failed: {str(e)}"
    
    def verify_code_syntax(
        self,
        code: str,
        language: str = "python"
    ) -> tuple[bool, Optional[str]]:
        """
        Verify code syntax and provide feedback.
        
        Args:
            code: The code to verify
            language: Programming language
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # For Python, we can do actual syntax checking
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return True, None
            except SyntaxError as e:
                return False, f"Syntax error at line {e.lineno}: {e.msg}"

        # JavaScript gets a real deterministic parser/linter rather than an
        # LLM opinion. Node's --check performs syntax validation without
        # executing the program.
        if language in {"javascript", "js"}:
            try:
                process = subprocess.run(
                    ["node", "--check", "-"], input=code, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return False, f"JavaScript linter unavailable: {exc}"
            if process.returncode == 0:
                return True, None
            return False, process.stderr.strip() or "JavaScript syntax check failed"
        
        # For other languages, use LLM for basic validation
        prompt = f"""Check the following {language} code for syntax errors:

```{language}
{code}
```

Respond in JSON format:
{{
    "valid": true/false,
    "errors": ["List of syntax errors if any"],
    "warnings": ["List of warnings if any"]
}}
"""
        
        try:
            self._ensure_client()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {language} syntax validator. Check code for syntax errors."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=_reasoning_safe_temperature(self.model, 0.1),
                max_tokens=Config.MAX_TOKENS
            )
            
            result = _parse_json_response(response.choices[0].message.content)
            if result["valid"]:
                return True, None
            else:
                return False, "; ".join(result["errors"])
                
        except Exception as e:
            # If validation fails, allow the code through
            return True, None
