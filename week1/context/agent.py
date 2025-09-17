"""
Context-Aware AI Agent with Tool Calls
An agent using Qwen model from SiliconFlow with document parsing, currency conversion, and calculator tools.
Designed to demonstrate the importance of context through ablation studies.
"""

import json
import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import requests
from openai import OpenAI
import PyPDF2
from io import BytesIO
import math
from datetime import datetime
from concurrent.futures import TimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ContextMode(Enum):
    """Different context modes for ablation studies"""
    FULL = "full"  # Complete context with all components
    NO_HISTORY = "no_history"  # No historical tool calls
    NO_REASONING = "no_reasoning"  # No reasoning/thinking process
    NO_TOOL_CALLS = "no_tool_calls"  # No tool call commands
    NO_TOOL_RESULTS = "no_tool_results"  # No tool call results


@dataclass
class ToolCall:
    """Represents a single tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentTrajectory:
    """Tracks the agent's execution trajectory"""
    reasoning_steps: List[str] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    context_mode: ContextMode = ContextMode.FULL


class ToolRegistry:
    """Registry for available tools"""
    
    @staticmethod
    def parse_pdf(url: str) -> Dict[str, Any]:
        """
        Download and parse a PDF from URL or local file
        
        Args:
            url: URL or file path of the PDF to parse
            
        Returns:
            Dictionary containing parsed text and metadata
        """
        try:
            # Check if it's a local file
            if url.startswith('file://'):
                # Extract the file path from file:// URL
                file_path = url.replace('file://', '')
                logger.info(f"Reading local PDF from {file_path}")
                
                # Read the file directly
                with open(file_path, 'rb') as f:
                    pdf_content = f.read()
                    
            elif url.startswith('/') or url.startswith('./') or url.startswith('../') or ':\\' in url or ':/' in url[1:3]:
                # Direct file path (absolute or relative)
                logger.info(f"Reading local PDF from {url}")
                
                # Read the file directly
                with open(url, 'rb') as f:
                    pdf_content = f.read()
                    
            else:
                # It's a remote URL, download it
                logger.info(f"Downloading PDF from {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                pdf_content = response.content
            
            # Parse the PDF content
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                text_content.append({
                    "page": page_num,
                    "text": text
                })
            
            result = {
                "url": url,
                "num_pages": len(pdf_reader.pages),
                "content": text_content,
                "metadata": pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {}
            }
            
            logger.info(f"Successfully parsed PDF with {len(pdf_reader.pages)} pages")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Convert currency using live exchange rates
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'EUR')
            
        Returns:
            Dictionary with conversion result
        """
        try:
            # Normalize currency codes (handle S$ notation)
            from_currency = from_currency.replace("S$", "SGD").replace("$", "USD") if from_currency.startswith("S$") else from_currency
            to_currency = to_currency.replace("S$", "SGD").replace("$", "USD") if to_currency.startswith("S$") else to_currency
            
            logger.info(f"Converting {amount} {from_currency} to {to_currency}")
            
            # For demonstration, using fixed rates (in production, use a real API)
            # These are example rates - you would normally fetch from an API
            exchange_rates = {
                "USD": 1.0,
                "EUR": 0.92,
                "GBP": 0.79,
                "JPY": 149.50,
                "CNY": 7.24,
                "CAD": 1.36,
                "AUD": 1.53,
                "CHF": 0.88,
                "INR": 83.12,
                "SGD": 1.34
            }
            
            if from_currency not in exchange_rates or to_currency not in exchange_rates:
                return {"error": f"Unsupported currency: {from_currency} or {to_currency}"}
            
            # Convert to USD first, then to target currency
            usd_amount = amount / exchange_rates[from_currency]
            converted_amount = usd_amount * exchange_rates[to_currency]
            
            result = {
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": round(converted_amount, 2),
                "exchange_rate": round(exchange_rates[to_currency] / exchange_rates[from_currency], 4),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Conversion result: {result['converted_amount']} {to_currency}")
            return result
            
        except Exception as e:
            logger.error(f"Error converting currency: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate(expression: str) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Dictionary with calculation result
        """
        try:
            logger.info(f"Calculating: {expression}")
            
            # Sanitize expression - only allow safe mathematical operations
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
            
            # Replace common operations for clarity
            expression = expression.replace("^", "**")
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
            
        except Exception as e:
            logger.error(f"Error calculating expression: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def code_interpreter(code: str) -> Dict[str, Any]:
        """
        Execute Python code for complex calculations and data processing
        
        Args:
            code: Python code to execute
            
        Returns:
            Dictionary with execution results and any output
        """
        try:
            logger.info(f"Executing Python code: {code[:100]}...")
            
            # Create a restricted namespace with safe built-ins
            safe_namespace = {
                '__builtins__': {
                    'abs': abs,
                    'all': all,
                    'any': any,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'round': round,
                    'len': len,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sorted': sorted,
                    'reversed': reversed,
                    'range': range,
                    'int': int,
                    'float': float,
                    'str': str,
                    'bool': bool,
                    'print': print,
                }
            }
            
            # Add math module
            safe_namespace['math'] = math
            
            # Capture printed output
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer):
                # Execute the code
                exec(code, safe_namespace)
            
            # Get printed output
            printed_output = output_buffer.getvalue()
            
            # Try to extract a result if it's assigned to 'result' variable
            result = safe_namespace.get('result', None)
            
            # Also check for common variable names
            if result is None:
                for var_name in ['total', 'sum', 'output', 'answer', 'final']:
                    if var_name in safe_namespace:
                        result = safe_namespace[var_name]
                        break
            
            # Get all variables defined (excluding built-ins and modules)
            variables = {
                k: v for k, v in safe_namespace.items() 
                if not k.startswith('__') and k not in ['math'] and not callable(v)
            }
            
            return {
                "code": code,
                "result": result,
                "output": printed_output if printed_output else None,
                "variables": variables,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return {
                "code": code,
                "error": str(e),
                "success": False
            }


class ContextAwareAgent:
    """
    AI Agent with configurable LLM providers and context modes for ablation studies
    """
    
    def __init__(self, api_key: str, context_mode: ContextMode = ContextMode.FULL, 
                 provider: str = "siliconflow", model: Optional[str] = None, 
                 verbose: bool = True):
        """
        Initialize the agent
        
        Args:
            api_key: API key for the LLM provider
            context_mode: Context mode for ablation studies
            provider: LLM provider ('siliconflow', 'doubao', 'kimi', or 'moonshot')
            model: Optional model override
            verbose: If True, log full HTTP requests and responses (default: True)
        """
        self.provider = provider.lower()
        self.verbose = verbose
        
        # Configure client based on provider
        if self.provider == "siliconflow":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            self.model = model or "Qwen/Qwen3-235B-A22B-Thinking-2507"
        elif self.provider == "doubao":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3"
            )
            self.model = model or "doubao-seed-1-6-thinking-250715"
        elif self.provider == "kimi" or self.provider == "moonshot":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            self.model = model or "kimi-k2-0905-preview"
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'siliconflow', 'doubao', 'kimi', or 'moonshot'")
        
        self.context_mode = context_mode
        self.trajectory = AgentTrajectory(context_mode=context_mode)
        self.tools = ToolRegistry()
        
        # Initialize conversation history
        self.conversation_history = []
        self._init_system_prompt()
        
        logger.info(f"Agent initialized with provider: {self.provider}, model: {self.model}, context mode: {context_mode.value}, verbose: {self.verbose}")
    
    def _init_system_prompt(self):
        """Initialize the system prompt for the conversation"""
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an intelligent assistant with access to tools. 

Your task is to solve the given problems using the available tools. Think step by step and use tools as needed.

Important: When you have gathered all necessary information and computed the final answer, clearly state "FINAL ANSWER:" followed by your answer."""
            }
        ]
    
    def _get_tools_description(self) -> List[Dict[str, Any]]:
        """Get tool descriptions for the model"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "parse_pdf",
                    "description": "Download and parse a PDF document from a URL to extract text content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the PDF document to parse"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "convert_currency",
                    "description": "Convert an amount from one currency to another using current exchange rates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "number",
                                "description": "The amount to convert"
                            },
                            "from_currency": {
                                "type": "string",
                                "description": "The source currency code (e.g., USD, EUR)"
                            },
                            "to_currency": {
                                "type": "string",
                                "description": "The target currency code (e.g., USD, EUR)"
                            }
                        },
                        "required": ["amount", "from_currency", "to_currency"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Evaluate a simple mathematical expression",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "The mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "code_interpreter",
                    "description": "Execute Python code for complex calculations, data processing, and computing totals. Use this for tasks like: summing lists of values, calculating percentages, aggregating financial data, performing multi-step calculations, or any computation requiring variables and intermediate steps.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute. Can use variables, loops, and mathematical operations. Example: 'amounts = [2500000, 2278481, 2541806, 2282609, 2388060]; total = sum(amounts); print(f\"Total: ${total:,.2f}\")"
                            }
                        },
                        "required": ["code"]
                    }
                }
            }
        ]
    
    def _prepare_assistant_message(self, message) -> Dict[str, Any]:
        """
        Prepare assistant message for adding to messages list, 
        filtering out reasoning_content if in NO_REASONING mode
        
        Args:
            message: The assistant message object
            
        Returns:
            Dictionary representation of the message
        """
        msg_dict = message.dict() if hasattr(message, 'dict') else message.model_dump()
        
        # Remove reasoning_content if in NO_REASONING mode
        if self.context_mode == ContextMode.NO_REASONING and 'reasoning_content' in msg_dict:
            msg_dict.pop('reasoning_content')
            
        return msg_dict
    
    def _build_context(self) -> str:
        """
        Build context based on the current mode
        
        Returns:
            Context string for the model
        """
        context_parts = []
        
        # Add reasoning steps if not disabled
        if self.context_mode != ContextMode.NO_REASONING and self.trajectory.reasoning_steps:
            context_parts.append("## Previous Reasoning Steps:")
            for step in self.trajectory.reasoning_steps:
                context_parts.append(f"- {step}")
            context_parts.append("")
        
        # Add tool call history if not disabled
        if self.context_mode not in [ContextMode.NO_HISTORY, ContextMode.NO_TOOL_CALLS] and self.trajectory.tool_calls:
            context_parts.append("## Tool Call History:")
            for call in self.trajectory.tool_calls:
                if self.context_mode != ContextMode.NO_TOOL_CALLS:
                    context_parts.append(f"- Called {call.tool_name} with args: {json.dumps(call.arguments)}")
                if self.context_mode != ContextMode.NO_TOOL_RESULTS and call.result:
                    context_parts.append(f"  Result: {json.dumps(call.result, indent=2)}")
            context_parts.append("")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _log_request_response(self, request_data: Dict[str, Any], response_data: Any, iteration: int):
        """
        Log full request and response when in verbose mode
        
        Args:
            request_data: The request payload sent to the API
            response_data: The response received from the API
            iteration: Current iteration number
        """
        if not self.verbose:
            return
            
        if request_data:
            print("\n" + "="*80)
            print(f"📤 ITERATION {iteration} - FULL REQUEST JSON:")
            print("-"*80)
            print(json.dumps(request_data, indent=2, ensure_ascii=False))
        
        if response_data:
            print("\n" + "="*80)
            print(f"📥 ITERATION {iteration} - FULL RESPONSE:")
            print("-"*80)
        
            # Convert response to dict for display
            if hasattr(response_data, 'model_dump'):
                response_dict = response_data.model_dump()
            elif hasattr(response_data, 'dict'):
                response_dict = response_data.dict()
            else:
                response_dict = {"raw_response": str(response_data)}

            print(json.dumps(response_dict, indent=2, ensure_ascii=False))
            print("="*80 + "\n")
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool and return the result
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        tool_map = {
            "parse_pdf": self.tools.parse_pdf,
            "convert_currency": self.tools.convert_currency,
            "calculate": self.tools.calculate,
            "code_interpreter": self.tools.code_interpreter
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        return tool_map[tool_name](**arguments)

    def execute_task(self, task: str, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Execute a task using available tools
        
        Args:
            task: The task to execute
            max_iterations: Maximum number of tool calls
            
        Returns:
            Task execution result
        """
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": task})
        
        # Use conversation history directly (no copy needed)
        messages = self.conversation_history
        
        iteration = 0
        final_answer = None
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}")
            
            try:
                # Prepare request data for logging
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 8192
                }
                
                if self.context_mode != ContextMode.NO_TOOL_CALLS:
                    request_data["tools"] = self._get_tools_description()
                    request_data["tool_choice"] = "auto"
                
                logger.info(f"Sending request to {self.provider} API")

                # Call the model with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self._get_tools_description() if self.context_mode != ContextMode.NO_TOOL_CALLS else None,
                    tool_choice="auto" if self.context_mode != ContextMode.NO_TOOL_CALLS else None,
                    temperature=0.3,
                    max_tokens=8192,
                    timeout=180  # Add 180 second timeout for main execution
                )
                
                # Log response if verbose
                if self.verbose:
                    self._log_request_response(request_data, response, iteration)
                
                message = response.choices[0].message
                
                # Check for final answer
                if message.content and "FINAL ANSWER:" in message.content:
                    final_answer = message.content.split("FINAL ANSWER:")[1].strip()
                    logger.info(f"Final answer found: {final_answer}")
                    # Add the message to conversation history
                    assistant_msg = self._prepare_assistant_message(message)
                    messages.append(assistant_msg)
                    break
                
                # Handle tool calls
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Add the assistant message with tool calls
                    assistant_msg = self._prepare_assistant_message(message)
                    messages.append(assistant_msg)
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"Executing tool: {function_name} with args: {function_args}")
                        
                        # Execute the tool
                        result = self._execute_tool(function_name, function_args)
                        
                        # Record the tool call
                        tool_call_record = ToolCall(
                            tool_name=function_name,
                            arguments=function_args,
                            result=result
                        )
                        self.trajectory.tool_calls.append(tool_call_record)
                        
                        # Add tool result to messages (if not disabled)
                        if self.context_mode != ContextMode.NO_TOOL_RESULTS:
                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            }
                            messages.append(tool_msg)
                        else:
                            # Add a placeholder message if tool results are disabled
                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": "[Tool result hidden due to context mode]"
                            }
                            messages.append(tool_msg)
                elif message.content:
                    # No tool calls, but there's content - add the message
                    assistant_msg = self._prepare_assistant_message(message)
                    messages.append(assistant_msg)
                
                # Note: We do NOT modify the system prompt anymore.
                # The context is already built into the conversation through tool history
                    
            except TimeoutError as e:
                logger.error(f"Request timed out after 60 seconds")
                return {
                    "error": "Request timed out. The model is taking too long to respond. Try a simpler task or different provider.",
                    "trajectory": self.trajectory,
                    "iterations": iteration
                }
            except Exception as e:
                logger.error(f"Error during task execution: {str(e)}")
                # Check if it's a timeout-related error
                if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                    return {
                        "error": "Request timed out. The model is taking too long to respond. Try a simpler task or different provider.",
                        "trajectory": self.trajectory,
                        "iterations": iteration
                    }
                return {
                    "error": str(e),
                    "trajectory": self.trajectory,
                    "iterations": iteration
                }
        
        return {
            "final_answer": final_answer,
            "trajectory": self.trajectory,
            "iterations": iteration,
            "success": final_answer is not None
        }
    
    def reset(self):
        """Reset the agent's trajectory and conversation history"""
        self.trajectory = AgentTrajectory(context_mode=self.context_mode)
        self._init_system_prompt()  # Reinitialize conversation with system prompt
        logger.info("Agent trajectory and conversation history reset")
    
    def process(self, query: str, max_iterations: int = 10) -> str:
        """
        Process a query and return the final answer as a string
        
        Args:
            query: The query to process
            max_iterations: Maximum number of tool calls
            
        Returns:
            The final answer as a string
        """
        result = self.execute_task(query, max_iterations)
        if result.get('final_answer'):
            return result['final_answer']
        elif result.get('error'):
            return f"Error: {result['error']}"
        else:
            return "No answer found"
