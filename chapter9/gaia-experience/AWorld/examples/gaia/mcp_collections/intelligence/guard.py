import os
import time
import traceback
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic.fields import FieldInfo

from aworld.config.conf import AgentConfig
from aworld.logs.util import Color
from aworld.models.llm import call_llm_model, get_llm_model
from examples.gaia.mcp_collections.base import ActionArguments, ActionCollection, ActionResponse


class GuardCollection(ActionCollection):
    """MCP service for diagnosing and correcting (if necessary) the reasoning/thinking process already existed in the currect context, or avoid the potential loopholes in the future, towards solving the complex problem correctly, through powerful guarding model with sophisticated experience.
    The MUST Choice for the Thinking Process Reviewing phase, good at diagnosing the reasoning process in the context or giving valuable suggestions in advance. 

    Supports advanced guarding for reasoning process:
    - Identify potential loopholes or oversights in the reasoning process already existed in the currect context, while solving the complex problem.
    - If necessary, provide the corresponding supplements or guidance to the reasoning process in advance, to maneuver the reasoning/thinking process towards solving the complex problem in a proper direction.
    """

    def __init__(self, arguments: ActionArguments) -> None:
        super().__init__(arguments)
        env_path = "/Users/zhitianxie/PycharmProjects/AWorld_gaia_July/AWorld/examples/gaia/cmd/agent_deploy/gaia_agent/.env"
        load_dotenv(env_path, override=True, verbose=True)

        # Initialize guarding model configuration
        self._llm_config = AgentConfig(
            llm_provider="openai",
            # llm_model_name="google/gemini-2.5-flash-preview-05-20:thinking",
            llm_model_name=os.getenv("GUARD_LLM_MODEL_NAME", "deepseek/deepseek-r1-0528:free"),
            llm_api_key=os.getenv("GUARD_LLM_API_KEY"),
            llm_base_url=os.getenv("GUARD_LLM_BASE_URL"),
        )

        self._color_log("Intelligence Guard Service initialized", Color.green, "debug")
        self._color_log(f"Using model: {self._llm_config.llm_model_name}", Color.blue, "debug")

    def _prepare_guarding_prompt(self, question: str, original_task: str = "") -> str:
        """Prepare the guarding prompt with question and optional context.

        Args:
            question: The main question for guarding the reasoning process, such as 'is there any potential loopholes or oversights in the reasoning process?'
            original_task: Optional original task description for context

        Returns:
            Formatted prompt string
        """
        if original_task:
            return f"Original Task: {original_task}\n\nQuestion: {question}"
        return f"Question: {question}"

    def _call_guarding_model(self, prompt: str, temperature: float = 0.1) -> str:
        """Call the guarding model with the prepared prompt.

        Args:
            prompt: The formatted prompt for guarding the reasoning process
            temperature: Model temperature for response variability

        Returns:
            guarding result from the model

        Raises:
            Exception: If model call fails
        """
        response = call_llm_model(
            llm_model=get_llm_model(conf=self._llm_config),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "## Your Role\n"
                        "You are an expert at identifying the potential loopholes or oversights"
                        "of the current reasoning process while solving the complex problem.\n\n "
                        "## Your Task: \n"
                        "Based on the gathered information retrieved from the internet, and the reasoning process already" 
                        "generated towards solving a complex task, you need to do the following 1 or 2 things, to guarntee the quality of the reasoning process, and a clear final answer: \n"
                        "  1. Provide your diagnosing result on the generated reasoning process and the corresponding the correction if necessary;\n"
                        "  2. Provide your insight and supplements in advance to avoid the potential loopholes or oversights in the future;\n\n"
                        "## Requirements: \n"
                        "  1. If the reasoning process already generated is complete and correct in your opinion, just say 'No loopholes or oversights found'. \n"
                        "  2. If the reasoning process already generated contains the materials that may lead to the potential logic mistake or lack of some important guardrails in your opinion, you may give a hint to the current reasoning process, with the necessary supplements.\n"
                        "  3. If the reasoning process already generated is seriously incorrect in your opinion, you may give the turn signal to the reasoning process, to maneuver the reasoning process towards solving the complex problem correctly. \n\n"    
                        "## Restriction: \n"
                        "  1. Please do not make judgments about the authenticity of externally sourced information obtained through searches, as this is not part of your job responsibilities;\n"
                        "  2. Do not make additional inferences or assumptions about the content of such information itself.\n"
                        "  3. If the question lacks necessary details/data/clues in your opinion, you may ask for more details.\n\n"
                        "## Example 1:\n"
                        "  Question: Is my reasoning process correct?\n"
                        "  Reasoning Process: (nothing specified)\n"
                        "  Your Identification Result: Your question lacks some information, please provide me more details so I can help you.\n\n"
                        ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )

        return response.content

    def mcp_guarding_reasoning_process(
        self,
        question: str = Field(
            description="The input question for diagnosing the completeness/correctness of the reasoning process.\n" 
                        "For example: based on the staged/phased information/data concluded as 1.xxxx 2. xxxx 3. xxxx...., is there any faults in the current reasoning process aaaaaa"
                        "that should be corrected? Or is there any loopholes or oversights that should be emphized in advance, towards solving the bbbbb problem?\n" 
                        "Requirement: This input question should include a clear question with the necessary details/data/clues from the previous context"
                        "(such as the key information/data retrieved from the internet), to present more clues to help the diagnosing process."    
                        "The more exact details/data contained in this input question, the better the diagnosing result will be."                    
        ),
        original_task: str = Field(default="", description="The original task. This field is required and cannot be simplied, has to be true to the original task."),
        temperature: float = Field(
            default=0.1,
            description="Model temperature for response variability (0.0-1.0)",
            ge=0.0,
            le=1.0,
        ),
        guarding_style: Literal["detailed", "concise", "step-by-step"] = Field(
            default="detailed",
            description="Style of guarding output: detailed analysis, concise summary, or step-by-step breakdown",
        ),
    ) -> ActionResponse:
        """This tool provides advanced logic diagonsing and correcting ability, to improve the quality of the reasoning process that already exists in the current context, while solving the complex question:
        - Identify potential loopholes or oversights in the current reasoning process while solving the complex problem. 
        - Providing the guidance, suggestions to the reasoning process, to correct the loopholes or oversights if identified in this shot.
        
        Invoke Timing: During Thinking Process Reviewing, while diagnosing the reasoning process in the context or give valuable suggestions in advance, this tool is a reliable selection.

        Strengths:
        - Be relatively sensitive to common logical traps in some mathematics or logic problems.

        Weakness:
        - Inability to process media types: image, audio, or video.
        - Inability to check the correctness of the retrieved information from the internet.
        - Require precise description of problem context and settings, including the reasoning process, retrieved data and the complex task itself.

        Args:
            question: The input question that invokes this tool to diagnose and/or correct the suspected reasoning process in the context
            original_task: Optional original task description for additional context
            temperature: Model temperature controlling response variability
            guarding_style: Style of guarding output format

        Returns:
            ActionResponse with guarding result and processing metadata
        """
        try:
            # Handle FieldInfo objects
            if isinstance(question, FieldInfo):
                question = question.default
            if isinstance(original_task, FieldInfo):
                original_task = original_task.default
            if isinstance(temperature, FieldInfo):
                temperature = temperature.default
            if isinstance(guarding_style, FieldInfo): 
                guarding_style = guarding_style.default

            # Validate input
            if not question or not question.strip():
                raise ValueError("Question is required for guarding the complex problem reasoning process")

            self._color_log(f"Processing guarding request: {question[:100]}...", Color.cyan)

            start_time = time.time()

            # Prepare the guarding prompt
            prompt = self._prepare_guarding_prompt(question, original_task) ## 简单的原始问题+分配给mcp server的问题

            # Enhance prompt based on guarding style
            if guarding_style == "step-by-step":
                prompt += "\n\nPlease provide a clear step-by-step breakdown of your reviewing process of the reasoning process."
            elif guarding_style == "concise":
                prompt += "\n\nPlease provide a concise and final guarding answer."
            elif guarding_style == "detailed":
                prompt += "\n\nPlease provide detailed reviewing analysis with comprehensive guarding."

            # Call the guarding model
            guarding_result = self._call_guarding_model(prompt, temperature)

            processing_time = time.time() - start_time

            # Prepare metadata
            metadata = {
                "model_name": self._llm_config.llm_model_name,
                "guarding_style": guarding_style,
                "response_length": len(guarding_result),
            }

            self._color_log(
                f"Successfully completed guarding ({len(guarding_result)} characters, {processing_time:.2f}s)",
                Color.green,
            )

            return ActionResponse(success=True, message=guarding_result, metadata=metadata)

        except ValueError as e:
            self.logger.error(f"Invalid input: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"Invalid input: {str(e)}",
                metadata={"error_type": "invalid_input", "error_message": str(e)},
            )
        except Exception as e:
            self.logger.error(f"Guarding failed: {str(e)}: {traceback.format_exc()}")
            return ActionResponse(
                success=False,
                message=f"Guarding failed: {str(e)}",
                metadata={"error_type": "guarding_error", "error_message": str(e)},
            )

    def mcp_get_guarding_capabilities(self) -> ActionResponse:
        """Get information about the guarding reasoning process service capabilities.

        Returns:
            ActionResponse with service capabilities and configuration
        """
        capabilities = {
            "Logic Loopholes Detecting": "Identifying the logic loopholes in the reasoning process already generated previsouly",
            "Detected Loopholes Correcting": "Correcting the logic loopholes identified in the reasoning process already generated previously",
            "Oversights Prevention": "Providing necessary supplements as hints to the currect reasoning process, to prevent the possible oversights in the future",
        }

        capability_list = "\n".join(
            [f"**{capability}**: {description}" for capability, description in capabilities.items()]
        )

        metadata = {
            "model_name": self._llm_config.llm_model_name,
            "provider": self._llm_config.llm_provider,
            "supported_capabilities": list(capabilities.keys()),
            "total_capabilities": len(capabilities),
            "guarding_styles": ["detailed", "concise", "step-by-step"],
        }

        return ActionResponse(
            success=True,
            message=f"Intelligence guarding Service Capabilities:\n\n{capability_list}",
            metadata=metadata,
        )


# Example usage and entry point
if __name__ == "__main__":
    load_dotenv()

    # Default arguments for testing
    args = ActionArguments(
        name="intelligence_guarding_service",
        transport="stdio",
        workspace=os.getenv("AWORLD_WORKSPACE", "~"),
    )

    # Initialize and run the intelligence guarding service
    try:
        service = GuardCollection(args)
        service.run()
    except Exception as e:
        print(f"An error occurred: {e}: {traceback.format_exc()}")
