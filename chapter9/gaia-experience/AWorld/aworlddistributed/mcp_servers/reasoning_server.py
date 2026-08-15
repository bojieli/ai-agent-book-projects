import os
import sys
import traceback

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from aworld.config.conf import AgentConfig
from aworld.logs.util import logger
from aworld.models.llm import call_llm_model, get_llm_model

# Initialize MCP server
mcp = FastMCP("reasoning-server")


@mcp.tool(
    description="Perform complex problem reasoning using powerful reasoning model."
)
def complex_problem_reasoning(
    question: str = Field(
        description="The input question for complex problem reasoning,"
        + " such as math and code contest problem",
    ),
    original_task: str = Field(
        default="",
        description="The original task description."
        + " This argument could be fetched from the <task>TASK</task> tag",
    ),
) -> str:
    """
    Perform complex problem reasoning using Powerful Reasoning model,
    such as riddle, game or competition-level STEM(including code) problems.

    Args:
        question: The input question for complex problem reasoning
        original_task: The original task description (optional)

    Returns:
        str: The reasoning result from the model
    """
    try:
        # Prepare the prompt with both the question and original task if provided
        prompt = question
        if original_task:
            prompt = f"Original Task: {original_task}\n\nQuestion: {question}"

        # Call the LLM model for reasoning
        response = call_llm_model(
            llm_model=get_llm_model(
                conf=AgentConfig(
                    llm_provider="openai",
                    llm_model_name=os.getenv("LLM_MODEL_NAME", "your_openai_api_key"),
                    llm_api_key=os.getenv("LLM_API_KEY", "your_openai_api_key"),
                    llm_base_url=os.getenv("LLM_BASE_URL", "your_openai_base_url"),
                )
            ),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at solving complex problems including math,"
                        " code contests, riddles, and puzzles."
                        " Provide detailed step-by-step reasoning and a clear final answer."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        )

        # Extract the reasoning result
        reasoning_result = response.content

        logger.info("Complex reasoning completed successfully")
        return reasoning_result

    except Exception as e:
        logger.error(f"Error in complex problem reasoning: {traceback.format_exc()}")
        return f"Error performing reasoning: {str(e)}"


def main():
    load_dotenv()
    print("Starting Reasoning MCP Server...", file=sys.stderr)
    mcp.run(transport="stdio")


# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    main()


sys.modules[__name__].__call__ = __call__

# Run the server when the script is executed directly
if __name__ == "__main__":
    main()
