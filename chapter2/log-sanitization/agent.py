"""
Log Sanitization Agent using Local Ollama LLM
"""

import os
import time
import re
import json
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import ollama

from config import (
    OLLAMA_MODEL, 
    OLLAMA_TEMPERATURE,
    SYSTEM_PROMPT, 
    USER_PROMPT_TEMPLATE,
    PII_DETECTION_SCHEMA,
    OUTPUT_DIR
)
from metrics import PerformanceMetrics, MetricsCollector


class LogSanitizationAgent:
    """Agent for sanitizing logs using local Qwen3 0.6B model via Ollama"""
    
    def __init__(self, model: str = OLLAMA_MODEL):
        """Initialize the sanitization agent.

        Primary backend is the local Ollama model. If Ollama is unavailable
        (not running / not reachable) and OPENROUTER_API_KEY is set, the agent
        falls back to OpenRouter (default hosted model: openai/gpt-5.6-luna),
        so the experiment still runs without a local model.
        """
        self.model = model
        self.backend = "ollama"
        self.metrics_collector = MetricsCollector(OUTPUT_DIR)

        # Try the local Ollama backend first.
        try:
            self.client = ollama.Client()
            models = self.client.list()
            # models is a dict with 'models' key containing a list
            if isinstance(models, dict) and 'models' in models:
                available_models = [m.get('name', '') for m in models['models']]
            else:
                # If it's a direct list (older API versions)
                available_models = [m.get('name', '') for m in models] if isinstance(models, list) else []

            if not any(self.model in m for m in available_models):
                print(f"⚠️  Model {self.model} not found. Pulling it now...")
                self.client.pull(self.model)
                print(f"✅ Model {self.model} pulled successfully")
            else:
                print(f"✅ Using model: {self.model}")

        except Exception as e:
            # Universal fallback: route through OpenRouter when Ollama is down.
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if openrouter_key:
                from openai import OpenAI
                from openrouter_fallback import (
                    OPENROUTER_BASE_URL,
                    map_model_to_openrouter,
                )
                self.backend = "openrouter"
                self.client = OpenAI(api_key=openrouter_key,
                                     base_url=OPENROUTER_BASE_URL)
                # 本地小模型（qwen3:0.6b 等）在 OpenRouter 上未必可用，
                # 默认改用 openai/gpt-5.6-luna；带 "/" 的 id 原样透传。
                self.model = (map_model_to_openrouter(self.model)
                              if "/" in self.model else "openai/gpt-5.6-luna")
                print(f"⚠️  Ollama unavailable ({e}); "
                      f"falling back to OpenRouter model: {self.model}")
            else:
                print(f"❌ Failed to connect to Ollama: {e}")
                print("Please ensure Ollama is running: ollama serve, "
                      "or set OPENROUTER_API_KEY as a fallback")
                raise

    def _chat_stream(self, messages):
        """Yield content chunks from the active backend (Ollama or OpenRouter)."""
        if self.backend == "ollama":
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                format=PII_DETECTION_SCHEMA,  # Use structured output format
                options={
                    "temperature": OLLAMA_TEMPERATURE,
                    "num_predict": 1000,
                }
            )
            for chunk in stream:
                yield chunk.get('message', {}).get('content', '')
        else:
            # 用与 Ollama 相同的 JSON Schema 强约束输出结构（pii_values 数组），
            # 避免模型自行发明字段名。strict 模式要求 additionalProperties=false。
            strict_schema = dict(PII_DETECTION_SCHEMA)
            strict_schema["additionalProperties"] = False
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=OLLAMA_TEMPERATURE,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "pii_detection",
                        "strict": True,
                        "schema": strict_schema,
                    },
                },
                max_tokens=1000,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                yield chunk.choices[0].delta.content or ""
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters for English text
        # For more accurate counting, we'd need the actual tokenizer
        return len(text) // 4
    
    def detect_pii(self, conversation_text: str) -> Tuple[List[str], Dict]:
        """
        Detect Level 3 PII in conversation text using local LLM
        
        Args:
            conversation_text: Text to analyze
        
        Returns:
            - List of detected PII values
            - Performance metrics dictionary
        """
        # Prepare the prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(conversation_text=conversation_text)
        
        # Count input tokens
        input_tokens = self.count_tokens(SYSTEM_PROMPT + user_prompt)
        
        # Measure prefill time (time to first token)
        start_time = time.perf_counter()
        
        # Create messages for Ollama
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Track first token time
        first_token_time = None
        output_tokens_count = 0
        full_response = ""
        
        try:
            # Use structured output with JSON schema (backend-agnostic stream)
            print("\n   🧠 Analyzing (JSON): \033[90m", end="", flush=True)  # Gray color for JSON

            for content in self._chat_stream(messages):
                if first_token_time is None and content:
                    first_token_time = time.perf_counter()

                full_response += content
                output_tokens_count += len(content) // 4  # Rough token estimate

                # Stream the actual content
                if content:
                    print(content, end="", flush=True)

            print("\033[0m")  # Reset color and new line
            
            end_time = time.perf_counter()
            
        except Exception as e:
            print(f"\n❌ Error during PII detection: {e}")
            return [], {}
        
        # Calculate performance metrics
        prefill_time_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
        total_time_ms = (end_time - start_time) * 1000
        output_time_ms = total_time_ms - prefill_time_ms
        
        prefill_speed = input_tokens / (prefill_time_ms / 1000) if prefill_time_ms > 0 else 0
        output_speed = output_tokens_count / (output_time_ms / 1000) if output_time_ms > 0 else 0
        
        # Parse JSON response
        pii_values = []
        
        try:
            response_json = json.loads(full_response)
            
            # Extract PII values
            pii_values = response_json.get('pii_values') or []
            # Strip leading/trailing whitespace and special characters like '-' or empty
            cleaned_pii_values = []
            for pii in pii_values:
                if pii and isinstance(pii, str):
                    cleaned = pii.strip().strip('-').strip()
                    if cleaned:
                        cleaned_pii_values.append(cleaned)
            pii_values = cleaned_pii_values

        except json.JSONDecodeError as e:
            print(f"\n   ⚠️  Failed to parse JSON response: {e}")
            # Fallback to simple line splitting if JSON parsing fails
            pii_values = [line.strip() for line in full_response.split('\n') if line.strip()]

        metrics = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens_count,
            'prefill_time_ms': prefill_time_ms,
            'output_time_ms': output_time_ms,
            'total_time_ms': total_time_ms,
            'prefill_speed_tps': prefill_speed,
            'output_speed_tps': output_speed,
            'pii_items_found': len(pii_values)
        }
        
        return pii_values, metrics
    
    def sanitize_text(self, text: str, pii_values: List[str]) -> Tuple[str, int]:
        """
        Replace PII values with [REDACTED] in the text
        
        Returns:
            - Sanitized text
            - Number of replacements made
        """
        sanitized = text
        replacements = 0
        
        for pii_value in pii_values:
            # Escape special regex characters in PII value
            escaped_value = re.escape(pii_value)
            # Count occurrences before replacement
            occurrences = len(re.findall(escaped_value, sanitized, re.IGNORECASE))
            # Replace all occurrences
            sanitized = re.sub(escaped_value, '[REDACTED]', sanitized, flags=re.IGNORECASE)
            replacements += occurrences
        
        return sanitized, replacements
    
    def sanitize_conversation(
        self, 
        conversation: Dict,
        test_id: str = "unknown"
    ) -> Dict:
        """
        Sanitize a single conversation and collect metrics
        
        Returns:
            Dictionary with sanitized conversation and metrics
        """
        # Format conversation text
        conv_text = self.format_conversation(conversation)
        conv_id = conversation.get('conversation_id', 'unknown')
        
        print(f"🔍 Processing conversation: {conv_id}")
        
        # Detect PII
        pii_values, perf_metrics = self.detect_pii(conv_text)
        
        if pii_values:
            print(f"   ✅ Found {len(pii_values)} PII items:")
            for pii in pii_values:
                print(f"      - {pii}")
        else:
            print("   ⚠️  No PII items detected")
        
        # Sanitize the text
        sanitized_text, replacements = self.sanitize_text(conv_text, pii_values)
        
        # Create performance metric. detect_pii() returns an empty metrics dict
        # when the LLM backend fails (e.g. Ollama not running) — fall back to
        # zeros so one failed conversation doesn't crash the whole batch.
        metric = PerformanceMetrics(
            test_id=test_id,
            conversation_id=conv_id,
            input_text_length=len(conv_text),
            input_tokens=perf_metrics.get('input_tokens', 0),
            prefill_time_ms=perf_metrics.get('prefill_time_ms', 0),
            output_time_ms=perf_metrics.get('output_time_ms', 0),
            total_time_ms=perf_metrics.get('total_time_ms', 0),
            output_tokens=perf_metrics.get('output_tokens', 0),
            prefill_speed_tps=perf_metrics.get('prefill_speed_tps', 0),
            output_speed_tps=perf_metrics.get('output_speed_tps', 0),
            pii_items_found=perf_metrics.get('pii_items_found', 0),
            replacements_made=replacements,
            sanitized_text_length=len(sanitized_text)
        )
        
        self.metrics_collector.add_metric(metric)
        
        return {
            'conversation_id': conv_id,
            'original_length': len(conv_text),
            'sanitized_length': len(sanitized_text),
            'pii_found': pii_values,
            'replacements_made': replacements,
            'sanitized_text': sanitized_text,
            'metrics': metric.to_dict()
        }
    
    def format_conversation(self, conversation: Dict) -> str:
        """Format conversation dictionary into text"""
        lines = []
        lines.append(f"Conversation ID: {conversation.get('conversation_id', 'unknown')}")
        lines.append(f"Timestamp: {conversation.get('timestamp', 'unknown')}")
        lines.append("-" * 50)
        
        messages = conversation.get('messages', [])
        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            lines.append(f"{role}: {content}")
            lines.append("")  # Empty line between messages
        
        return "\n".join(lines)
    
    def save_sanitized_log(self, test_id: str, results: List[Dict]):
        """Save sanitized logs to output directory"""
        output_file = OUTPUT_DIR / f"{test_id}_sanitized.txt"
        summary_file = OUTPUT_DIR / f"{test_id}_summary.json"
        
        # Save sanitized text
        with open(output_file, 'w') as f:
            for result in results:
                f.write(f"\n{'='*60}\n")
                f.write(f"Conversation: {result['conversation_id']}\n")
                f.write(f"{'='*60}\n")
                f.write(result['sanitized_text'])
                f.write("\n")
        
        # Save summary
        summary = {
            'test_id': test_id,
            'total_conversations': len(results),
            'total_pii_found': sum(len(r['pii_found']) for r in results),
            'total_replacements': sum(r['replacements_made'] for r in results),
            'conversations': [
                {
                    'conversation_id': r['conversation_id'],
                    'pii_count': len(r['pii_found']),
                    'replacements': r['replacements_made']
                }
                for r in results
            ]
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Sanitized log saved to: {output_file}")
        print(f"✅ Summary saved to: {summary_file}")
    
    def process_test_case(self, test_id: str, conversations: List[Dict]) -> List[Dict]:
        """Process all conversations in a test case"""
        results = []
        
        print(f"\n{'='*60}")
        print(f"Processing Test Case: {test_id}")
        print(f"Total Conversations: {len(conversations)}")
        print(f"{'='*60}")
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n[{i}/{len(conversations)}] ", end="")
            result = self.sanitize_conversation(conv, test_id)
            results.append(result)
        
        # Save results
        self.save_sanitized_log(test_id, results)
        
        # Save metrics
        self.metrics_collector.save_metrics()
        self.metrics_collector.print_summary()
        
        return results
