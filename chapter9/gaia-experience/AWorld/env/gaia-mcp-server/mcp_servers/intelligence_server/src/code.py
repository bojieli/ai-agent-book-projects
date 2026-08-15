import json
import logging
import os
import time
import traceback
from typing import Union, Literal

from pydantic import BaseModel
from dotenv import load_dotenv
from pydantic.fields import FieldInfo

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field
from openai import OpenAI

from base import (
    ActionResponse,
    _validate_file_path
)

load_dotenv()

mcp = FastMCP(
    "intelligence-code-server",
    instructions="""
MCP service for generating executable Python code snippets using LLM.

    Supports code generation for:
    - Data processing and analysis tasks
    - Algorithm implementations
    - Utility functions and scripts
    - Problem-solving code snippets
    - Educational programming examples
""",
)

class CodeGenerationMetadata(BaseModel):
    """Metadata for code generation results."""

    model_name: str | None = None
    code_style: str | None = None
    code_length: int | None = None
    line_count: int | None = None
    processing_time_seconds: float | None = None
    temperature: float | None = None
    has_requirements: bool | None = None
    has_context: bool | None = None
    saved_file_path: str | None = None
    file_save_error: str | None = None
    error_type: str | None = None
    error_message: str | None = None


@mcp.tool(
    description="""
Generate executable Python code snippets based on task description.

        This tool provides comprehensive code generation capabilities for:
        - Solve simple math tasks and validations
        - Data processing and analysis tasks
        - Algorithm implementations and optimizations
        - Utility functions and helper scripts
        - Problem-solving code snippets
        - Educational programming examples
        - API integrations and automation scripts

        Strengths:
        - Generates clean, executable Python code
        - Follows modern Python best practices (>=3.11)
        - Includes proper error handling
        - Supports various coding styles and complexity levels

        Limitations:
        - Cannot execute or test the generated code
        - May require manual adjustments for specific environments
        - Limited to Python programming language
"""
)
async def generate_python_code(
        task_description: str = Field(description="Description of the programming task or problem to solve"),
        requirements: str = Field(
            default="", description="Specific requirements, constraints, or specifications for the code"
        ),
        context: str = Field(default="", description="Additional context or background information"),
        temperature: float = Field(
            default=0.1,
            description="Model temperature for code generation (0.0-1.0, lower = more deterministic)",
            ge=0.0,
            le=1.0,
        ),
        code_style: Literal["minimal", "documented", "verbose"] = Field(
            default="documented",
            description="Style of generated code: minimal (concise), documented (with comments), verbose (detailed)",
        ),
        save_to_file_path: str | None = Field(
            default=None,
            description="Optional. Path to save the generated Python snippet. e.g., 'output/generated_script.py'",
        )
) -> Union[str, TextContent]:
    try:
        # Handle FieldInfo objects
        if isinstance(task_description, FieldInfo):
            task_description = task_description.default
        if isinstance(requirements, FieldInfo):
            requirements = requirements.default
        if isinstance(context, FieldInfo):
            context = context.default
        if isinstance(temperature, FieldInfo):
            temperature = temperature.default
        if isinstance(code_style, FieldInfo):
            code_style = code_style.default
        if isinstance(save_to_file_path, FieldInfo):
            save_to_file_path = save_to_file_path.default

        # Validate input
        if not task_description or not task_description.strip():
            raise ValueError("Task description is required for code generation")

        logging.info(f"Generating code for: {task_description[:100]}...")

        start_time = time.time()

        # Prepare the code generation prompt
        prompt = _prepare_code_prompt(task_description, requirements, context)

        # Enhance prompt based on code style
        if code_style == "minimal":
            prompt += "\n\nGenerate concise, minimal code without extensive comments."
        elif code_style == "verbose":
            prompt += "\n\nGenerate detailed code with comprehensive comments and explanations."
        elif code_style == "documented":
            prompt += "\n\nGenerate well-documented code with clear comments and docstrings."

        # Call the code generation model
        raw_response = _call_code_model(prompt, temperature)

        # Extract clean Python code
        generated_code = _extract_python_code(raw_response)

        processing_time = time.time() - start_time

        # Populate metadata fields
        metadata = CodeGenerationMetadata(
            model_name=os.getenv("CODE_LLM_MODEL_NAME", ""),
            code_style=code_style,
            code_length=len(generated_code),
            line_count=len(generated_code.split("\n")),
            processing_time_seconds=round(processing_time, 2),
            temperature=temperature,
            has_requirements=bool(requirements.strip()),
            has_context=bool(context.strip()),
        )

        # Save the generated code to a file if path is provided
        if save_to_file_path:
            try:
                # Use _validate_file_path to ensure path is within workspace and get absolute path
                # The check_existence=False allows creating a new file.
                output_file_path_obj = _validate_file_path(save_to_file_path)

                # Ensure parent directories exist
                output_file_path_obj.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file_path_obj, "w", encoding="utf-8") as f:
                    f.write(generated_code)

                metadata.saved_file_path = str(output_file_path_obj)
                logging.info(f"Generated code also saved to: {output_file_path_obj}")
            except Exception as e:
                logging.error(f"Failed to save code to file '{save_to_file_path}': {str(e)}")
                metadata.file_save_error = str(e)

        logging.info(
            f"Successfully generated code ({metadata.code_length} characters, "
            f"{metadata.processing_time_seconds:.2f}s)"
        )

        action_response = ActionResponse(success=True, message=generated_code,
                                         metadata=metadata.model_dump(exclude_none=True))
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(action_response.model_dump()),
        }

        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump()),  # Empty string instead of None
            **{"metadata": output_dict}  # Pass as additional fields
        )

    except ValueError as e:
        logging.error(f"Invalid input: {str(e)}")
        metadata.error_type = "invalid_input"
        metadata.error_message = str(e)
        action_response = ActionResponse(
            success=False,
            message=f"Invalid input: {str(e)}",
            metadata=metadata.model_dump(exclude_none=True),
        )
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump()),  # Empty string instead of None
            **{"metadata": {}}  # Pass as additional fields
        )
    except Exception as e:
        logging.error(f"Code generation failed: {str(e)}: {traceback.format_exc()}")
        metadata.error_type = "generation_error"
        metadata.error_message = str(e)
        action_response = ActionResponse(
            success=False,
            message=f"Code generation failed: {str(e)}",
            metadata=metadata.model_dump(exclude_none=True),
        )
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump()),  # Empty string instead of None
            **{"metadata": {}}  # Pass as additional fields
        )


@mcp.tool(
    description="""
Get information about the reasoning service capabilities.
"""
)
async def get_reasoning_capabilities() -> Union[str, TextContent]:
    capabilities = {
        "Mathematical Problems": "Advanced mathematical reasoning, proofs, and calculations",
        "Code Contests": "Programming challenges, algorithm design, and optimization",
        "Logic Puzzles": "Brain teasers, riddles, and logical reasoning problems",
        "STEM Problems": "Competition-level science, technology, engineering, and math",
        "Multi-step Analysis": "Complex analytical reasoning with multiple interconnected steps",
    }

    capability_list = "\n".join(
        [
            f"**{capability}**: {description}"
            for capability, description in capabilities.items()
        ]
    )

    metadata = {
        "model_name": os.getenv("THINK_LLM_MODEL_NAME", ""),
        "provider": "openai",
        "supported_capabilities": list(capabilities.keys()),
        "total_capabilities": len(capabilities),
        "reasoning_styles": ["detailed", "concise", "step-by-step"],
    }

    action_response = ActionResponse(
        success=True,
        message=f"Intelligence Reasoning Service Capabilities:\n\n{capability_list}",
        metadata=metadata,
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": f"Intelligence Reasoning Service Capabilities:\n\n{capability_list}"
    }
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )

def _prepare_code_prompt(task_description: str, requirements: str = "", context: str = "") -> str:
    """Prepare the code generation prompt with task description and optional requirements.

    Args:
        task_description: The main task for code generation
        requirements: Optional specific requirements or constraints
        context: Optional additional context or background information

    Returns:
        Formatted prompt string
    """
    prompt_parts = [f"Task: {task_description}"]

    if requirements:
        prompt_parts.append(f"Requirements: {requirements}")

    if context:
        prompt_parts.append(f"Context: {context}")

    return "\n\n".join(prompt_parts)

def _call_code_model(prompt: str, temperature: float = 0.1) -> str:
    """Call the code generation model with the prepared prompt.

    Args:
        prompt: The formatted prompt for code generation
        temperature: Model temperature for response variability

    Returns:
        Generated code from the model

    Raises:
        Exception: If model call fails
    """
    openai_params = {
        "model": os.getenv("TCODE_LLM_MODEL_NAME", ""),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert Python programmer. Generate clean, efficient, and "
                    "well-documented Python code that solves the given task. "
                    "Include proper error handling and follow Python best practices. "
                    "Return only executable Python code with minimal explanatory comments."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    try:
        client: OpenAI = OpenAI(
            api_key=os.getenv("CODE_LLM_API_KEY"),
            base_url=os.getenv("TCODE_LLM_BASE_URL"),
        )
        response = client.chat.completions.create(**openai_params)
        content = ""
        if response and hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            return content
    except BaseException as e:
        logging.warn(f"coding failed: {str(e)}: {traceback.format_exc()}")
        return f"coding failed: {str(e)}"

    return content

def _extract_python_code(response: str) -> str:
    """Extract Python code from the model response.

    Args:
        response: Raw response from the model

    Returns:
        Extracted Python code
    """
    # Remove markdown code blocks if present
    lines = response.strip().split("\n")

    # Find code block boundaries
    start_idx = 0
    end_idx = len(lines)

    for i, line in enumerate(lines):
        if line.strip().startswith("```python") or line.strip().startswith("```"):
            start_idx = i + 1
            break

    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "```":
            end_idx = i
            break

    # Extract the code
    code_lines = lines[start_idx:end_idx]
    return "\n".join(code_lines).strip()



if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting intelligence-think-server MCP server!")
    mcp.run(transport="stdio")
