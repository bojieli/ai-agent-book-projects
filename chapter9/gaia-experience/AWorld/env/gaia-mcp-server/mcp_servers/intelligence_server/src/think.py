import json
import logging
import os
import time
import traceback
from typing import Union, Literal

from dotenv import load_dotenv
from pydantic.fields import FieldInfo
from openai import OpenAI

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field

from base import ActionResponse

load_dotenv()

mcp = FastMCP(
    "intelligence-think-server",
    instructions="""
MCP service for complex problem reasoning using powerful reasoning models.

    Supports advanced reasoning for:
    - Mathematical problems and proofs
    - Code contest and programming challenges
    - Logic puzzles and riddles
    - Competition-level STEM problems
    - Multi-step analytical reasoning
""",
)


@mcp.tool(
    description="""
his tool provides comprehensive reasoning capabilities for:
        - Mathematical problems and proofs
        - Programming and algorithm challenges
        - Logic puzzles, brain teasers, and fun riddles
        - Competition-level STEM problems
        - Multi-step analytical reasoning tasks

        Weakness:
        - Inability to process media types: image, audio, or video
        - Require precise description of problem context and settings
"""
)
async def complex_problem_reasoning(
    question: str = Field(
        description="The input question for complex problem reasoning, such as math and code contest problems"
    ),
    original_task: str = Field(
        default="", description="The original task description."
    ),
    temperature: float = Field(
        default=0.3,
        description="Model temperature for response variability (0.0-1.0)",
        ge=0.0,
        le=1.0,
    ),
    reasoning_style: Literal["detailed", "concise", "step-by-step"] = Field(
        default="detailed",
        description="Style of reasoning output: detailed(analysis), concise(summary), or step-by-step(breakdown)",
    ),
) -> Union[str, TextContent]:
    try:
        # Handle FieldInfo objects
        if isinstance(question, FieldInfo):
            question = question.default
        if isinstance(original_task, FieldInfo):
            original_task = original_task.default
        if isinstance(temperature, FieldInfo):
            temperature = temperature.default
        if isinstance(reasoning_style, FieldInfo):
            reasoning_style = reasoning_style.default

        # Validate input
        if not question or not question.strip():
            raise ValueError("Question is required for complex problem reasoning")

        logging.info(f"Processing reasoning request: {question[:100]}...")

        start_time = time.time()

        # Prepare the reasoning prompt
        prompt = _prepare_reasoning_prompt(question, original_task)

        # Enhance prompt based on reasoning style
        if reasoning_style == "step-by-step":
            prompt += "\n\nPlease provide a clear step-by-step breakdown of your reasoning process."
        elif reasoning_style == "concise":
            prompt += (
                "\n\nPlease provide a concise but complete reasoning and final answer."
            )
        elif reasoning_style == "detailed":
            prompt += (
                "\n\nPlease provide detailed analysis with comprehensive reasoning."
            )

        # Call the reasoning model
        reasoning_result = _call_reasoning_model(prompt, temperature)

        processing_time = time.time() - start_time

        # Prepare metadata
        metadata = {
            "model_name": os.getenv("THINK_LLM_MODEL_NAME", ""),
            "reasoning_style": reasoning_style,
            "response_length": len(reasoning_result),
        }

        logging.info(
            f"Successfully completed reasoning ({len(reasoning_result)} characters, {processing_time:.2f}s)"
        )

        action_response = ActionResponse(
            success=True, message=reasoning_result, metadata=metadata
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": reasoning_result
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except ValueError as e:
        logging.error(f"Invalid input: {str(e)}")
        action_response = ActionResponse(
            success=False,
            message=f"Invalid input: {str(e)}",
            metadata={"error_type": "invalid_input", "error_message": str(e)},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )
    except Exception as e:
        logging.error(f"Reasoning failed: {str(e)}: {traceback.format_exc()}")
        action_response = ActionResponse(
            success=False,
            message=f"Reasoning failed: {str(e)}",
            metadata={"error_type": "reasoning_error", "error_message": str(e)},
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
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


def _prepare_reasoning_prompt(question: str, original_task: str = "") -> str:
    """Prepare the reasoning prompt with question and optional context.

    Args:
        question: The main question for reasoning
        original_task: Optional original task description for context

    Returns:
        Formatted prompt string
    """
    if original_task:
        return f"Original Task: {original_task}\n\nQuestion: {question}"
    return f"Question: {question}"


def _call_reasoning_model(prompt: str, temperature: float = 0.3) -> str:
    """Call the reasoning model with the prepared prompt.

    Args:
        prompt: The formatted prompt for reasoning
        temperature: Model temperature for response variability

    Returns:
        Reasoning result from the model

    Raises:
        Exception: If model call fails
    """
    openai_params = {
        "model": os.getenv("THINK_LLM_MODEL_NAME", ""),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert at solving complex problems including math, "
                    "code contests, riddles, and puzzles. "
                    "Provide detailed step-by-step reasoning and a clear final answer."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    try:
        client: OpenAI = OpenAI(
            api_key=os.getenv("THINK_LLM_API_KEY"),
            base_url=os.getenv("THINK_LLM_BASE_URL"),
        )
        response = client.chat.completions.create(**openai_params)
        content = ""
        if response and hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            return content
    except BaseException as e:
        logging.warn(f"Reasoning failed: {str(e)}: {traceback.format_exc()}")
        return f"Reasoning failed: {str(e)}"

    return content



if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting intelligence-think-server MCP server!")
    mcp.run(transport="stdio")
