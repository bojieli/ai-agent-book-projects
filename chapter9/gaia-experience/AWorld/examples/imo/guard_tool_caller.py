# MIT License
#
# Copyright (c) 2025 Lin Yang, Yichen Huang
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, TaskConfig
from aworld.core.task import Task
from aworld.runner import Runners


class GuardToolCaller:
    """simple reasoning diagnostic tool caller"""
    
    def __init__(self):
        # loading env
        env_path = ".env"
        load_dotenv(env_path, override=True, verbose=True)
        
        # initialize guard llm
        self.guard_llm = self._init_guard_llm()
    
    def _init_guard_llm(self):
        """initialize reasoning diagnostic tool"""
        try:
            agent_config = AgentConfig(
                llm_provider="openai",
                llm_model_name=os.getenv("IMO_LLM_MODEL_NAME", "deepseek/deepseek-r1-0528:free"),
                llm_api_key=os.getenv("IMO_LLM_API_KEY"),
                llm_base_url=os.getenv("IMO_LLM_BASE_URL"),
                llm_temperature=0.1,
            )
            
            guard_llm = Agent(
                conf=agent_config,
                name="guard_llm",
                system_prompt=self._get_guard_system_prompt(),
            )
            
            logging.info("reasoning diagnostic tool LLM initialized successfully")
            return guard_llm
            
        except Exception as e:
            logging.error(f"reasoning diagnostic tool LLM initialized failed: {e}")
            return None
    
    def _get_guard_system_prompt(self) -> str:
        """get reasoning diagnostic tool system prompt"""
        return """You are an expert mathematician and a meticulous grader for an International Mathematical Olympiad (IMO) level exam. Your primary task is to rigorously verify the provided mathematical solution. A solution is to be judged correct only if every step is rigorously justified. A solution that arrives at a correct final answer through flawed reasoning, educated guesses, or with gaps in its arguments must be flagged as incorrect or incomplete.

### Instructions ###
**1. Core Instructions**
*  Your sole task is to find and report all issues in the provided solution. You must act as a **verifier**, NOT a solver. **Do NOT attempt to correct the errors or fill the gaps you find.**
*  You must perform a **step-by-step** check of the entire solution. This analysis will be presented in a **Detailed Verification Log**, where you justify your assessment of each step: for correct steps, a brief justification suffices; for steps with errors or gaps, you must provide a detailed explanation.

**2. How to Handle Issues in the Solution**
When you identify an issue in a step, you MUST first classify it into one of the following two categories and then follow the specified procedure.

*   **a. Critical Error:**
	This is any error that breaks the logical chain of the proof. This includes both **logical fallacies** (e.g., claiming that ‘A > B, C > D’ implies ‘A-C>B-D’) and factual errors (e.g., a calculation error like ‘2+3=6’).
	*  **Procedure:**
		* Explain the specific error and state that it **invalidates the current line of reasoning**.
		* Do NOT check any further steps that rely on this error.
		* You MUST, however, scan the rest of the solution to identify and verify any fully independent parts. For example, if a proof is split into multiple cases, an error in one case does not prevent you from checking the other cases.
*   **b. Justification Gap:**
	This is for steps where the conclusion may be correct, but the provided argument is incomplete, hand-wavy, or lacks sufficient rigor.
	*  **Procedure:**
		* Explain the gap in the justification.
		* State that you will **assume the step’s conclusion is true** for the sake of argument.
		* Then, proceed to verify all subsequent steps to check if the remainder of the argument is sound.

**3. Output Format**
Your response MUST be structured into two main sections: a **Summary** followed by the **Detailed Verification Log**.

*   **a. Summary**
	This section MUST be at the very beginning of your response. It must contain two components:
	*  **Final Verdict**: A single, clear sentence declaring the overall validity of the solution. For example: "The solution is correct," "The solution contains a Critical Error and is therefore invalid," or "The solution’s approach is viable but contains several Justification Gaps."
	*  **List of Findings**: A bulleted list that summarizes **every** issue you discovered. For each finding, you must provide:
		*   **Location:** A direct quote of the key phrase or equation where the issue occurs.
		*   **Issue:** A brief description of the problem and its classification (**Critical Error** or **Justification Gap**).

*   **b. Detailed Verification Log**
	Following the summary, provide the full, step-by-step verification log as defined in the Core Instructions. When you refer to a specific part of the solution, **quote the relevant text** to make your reference clear before providing your detailed analysis of that part.

**Example of the Required Summary Format**
*This is a generic example to illustrate the required format. Your findings must be based on the actual solution provided below.*

**Final Verdict:** The solution is **invalid** because it contains a Critical Error.

**List of Findings:**
*   **Location:** "By interchanging the limit and the integral, we get ..."
	*   **Issue:** Justification Gap - The solution interchanges a limit and an integral without providing justification, such as proving uniform convergence.
*   **Location: **"From $A > B$ and $C > D$, it follows that $A−C>B−D$"
	*	**Issue:** Critical Error - This step is a logical fallacy. Subtracting inequalities in this manner is not a valid mathematical operation.
================================================================================================================================================================
### Problem ###

[Paste the TeX for the problem statement here]

================================================================================================================================================================
### Solution ###

[Paste the TeX for the solution to be verified here]

================================================================================================================================================================
### Verification Task Reminder ###
Your task is to act as an IMO grader. Now, generate the **summary** and the **step-by-step verification log** for the solution above. In your log, justify each correct step and explain in detail any errors or justification gaps you find, as specified in the instructions above."""
    
    async def call_guard_tool(self, super_output: str, original_task: str) -> str:
        """call reasoning diagnostic tool"""
        try:
            if not self.guard_llm:
                return "reasoning diagnostic tool is not availble"
            
            # construct the input
            input_text = f"""Here is the provided solution:
{super_output}

Here is the original task:
{original_task}

Please do your job as expert mathematician and a meticulous grader for an International Mathematical Olympiad (IMO) level exam."""

            # create task
            task = Task(
                input=input_text,
                agent=self.guard_llm,
                conf=TaskConfig()
            )
            
            # run task
            result = Runners.sync_run_task(task=task)
            
            # extract the answer
            if result and task.id in result:
                return result[task.id].answer
            else:
                return "The reasoning diagnostic tool did not return valid results."
                
        except Exception as e:
            logging.error(f"Failed to invoke the reasoning diagnostic tool: {e}")
            return f"Failed to invoke the reasoning diagnostic tool.: {str(e)}" 