"""LLM-based evaluator for agent responses."""

import json
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import openai
from config import Config
from models import TestCase, EvaluationResult


class LLMEvaluator:
    """LLM-based evaluator for agent responses."""
    
    def __init__(self, evaluator_type: Optional[str] = None):
        """Initialize the evaluator with specified LLM."""
        self.config = Config.get_evaluator_config(evaluator_type)
        self.client = self._create_client()
        
    def _create_client(self) -> openai.OpenAI:
        """Create OpenAI-compatible client."""
        return openai.OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_llm(self, messages: list) -> str:
        """Call the LLM with retry logic."""
        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=0,  # Use deterministic evaluation
            timeout=Config.REQUEST_TIMEOUT
        )
        return response.choices[0].message.content
    
    def evaluate(
        self,
        test_case: TestCase,
        agent_response: str,
        extracted_memory: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate an agent's response against the test case criteria.
        
        Args:
            test_case: The test case being evaluated
            agent_response: The agent's response to the user question
            extracted_memory: Optional extracted memory from the agent
            
        Returns:
            EvaluationResult with detailed scoring and reasoning
        """
        evaluation_prompt = self._build_evaluation_prompt(
            test_case,
            agent_response,
            extracted_memory
        )
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert evaluator for AI agent memory systems. "
                    "Your task is to evaluate how well an agent's response demonstrates "
                    "proper memory recall and utilization based on given criteria. "
                    "Provide a nuanced continuous reward score from 0.0 to 1.0, where: \n"
                    "- 0.0-0.2: Complete failure, no relevant memory recall\n"
                    "- 0.2-0.4: Poor performance, minimal memory utilization without meeting any important requirements\n"
                    "- 0.4-0.6: Partial success, some memory recall but missing the most important requirements\n"
                    "- 0.6-0.8: Good performance, most key requirements met but missing some key requirements or many details\n"
                    "- 0.8-1.0: Excellent performance, comprehensive memory utilization with only minor missing details\n"
                    "Be objective, thorough, and provide clear reasoning. "
                    "Output your evaluation as a JSON object."
                )
            },
            {
                "role": "user",
                "content": evaluation_prompt
            }
        ]
        
        try:
            response = self._call_llm(messages)
            return self._parse_evaluation_response(response, test_case.test_id)
        except Exception as e:
            # Return failed evaluation on error
            return EvaluationResult(
                test_id=test_case.test_id,
                reward=0.0,
                passed=False,  # For backward compatibility
                reasoning=f"Evaluation failed due to error: {str(e)}",
                required_info_found={}
            )
    
    def _build_evaluation_prompt(
        self,
        test_case: TestCase,
        agent_response: str,
        extracted_memory: Optional[str]
    ) -> str:
        """Build the evaluation prompt for the LLM."""
        prompt = f"""Test Case: {test_case.title}
Category: {test_case.category}
Description: {test_case.description}

User Question: {test_case.user_question}

Agent Response:
{agent_response}

"""
        if extracted_memory:
            prompt += f"""Extracted Memory (if provided by agent):
{extracted_memory}

"""
        
        prompt += f"""Evaluation Criteria:
{test_case.evaluation_criteria}
"""
        if test_case.expected_behavior:
            prompt += f"""
Expected Behavior: {test_case.expected_behavior}
"""
        prompt += """
Please evaluate the agent's response and assign a continuous reward score (0.0-1.0) based on:
1. How well does the response demonstrate memory recall from conversation histories?
2. What proportion of required information is present and correctly utilized?
3. How comprehensive and accurate is the memory integration?
4. Are there partial successes that deserve partial credit?
5. For {test_case.category}:"""
        
        if test_case.category == "layer1":
            prompt += """
   - Does the agent accurately retrieve basic factual information?
   - Is the retrieved information correct and complete?"""
        elif test_case.category == "layer2":
            prompt += """
   - Does the agent properly disambiguate when faced with multiple possibilities?
   - Does it retrieve ALL relevant memory pieces, not just one?
   - Does it demonstrate contextual understanding?"""
        elif test_case.category == "layer3":
            prompt += """
   - Does the agent synthesize information across multiple conversations?
   - Does it proactively identify relevant connections?
   - Does it provide comprehensive and forward-thinking assistance?"""
        
        prompt += """

Please provide your evaluation in the following JSON format:
{
    "reward": 0.0-1.0,
    "reasoning": "Detailed explanation of your reward score assignment",
    "required_info_found": {
        "info_piece_1": 0.0-1.0,
        "info_piece_2": 0.0-1.0,
        ...
    },
    "partial_credit_details": "Explain any partial credit awarded",
    "suggestions": "Optional suggestions for improvement"
}

IMPORTANT: 
- Assign a continuous reward score from 0.0 to 1.0 based on the quality of memory recall
- For required_info_found, assign partial scores (0.0-1.0) for each piece
- Consider partial credit for incomplete but relevant responses
- Focus on semantic understanding rather than exact string matching
- Reward progressive improvement and partial successes"""
        
        return prompt
    
    def _parse_evaluation_response(
        self,
        response: str,
        test_id: str
    ) -> EvaluationResult:
        """Parse the LLM's evaluation response."""
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            
            # Handle both new reward format and old score/passed format for compatibility
            reward = float(data.get("reward", data.get("score", 0.0)))
            
            # Convert old boolean required_info_found to float scores if needed
            required_info = data.get("required_info_found", {})
            if required_info and isinstance(next(iter(required_info.values()), None), bool):
                # Convert boolean values to float (True=1.0, False=0.0)
                required_info = {k: 1.0 if v else 0.0 for k, v in required_info.items()}
            
            # Determine passed status based on reward if not explicitly provided
            passed = data.get("passed")
            if passed is None:
                passed = reward >= 0.8  # Default threshold
            
            return EvaluationResult(
                test_id=test_id,
                reward=reward,
                passed=bool(passed),  # Keep for backward compatibility
                reasoning=data.get("reasoning", "No reasoning provided"),
                required_info_found=required_info,
                suggestions=data.get("suggestions")
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback parsing if JSON is malformed
            # Try to extract reward/score from the response text
            import re
            reward_match = re.search(r'"reward"\s*:\s*([0-9.]+)', response)
            score_match = re.search(r'"score"\s*:\s*([0-9.]+)', response)
            
            if reward_match:
                reward = float(reward_match.group(1))
            elif score_match:
                reward = float(score_match.group(1))
            else:
                # Default to 0.5 if we can't parse any score
                reward = 0.5
            
            return EvaluationResult(
                test_id=test_id,
                reward=reward,
                passed=reward >= 0.8,  # Default threshold
                reasoning=f"Evaluation response parsing failed: {str(e)}. Raw response: {response[:500]}",
                required_info_found={},
                suggestions="Consider reviewing the evaluation format"
            )


class BatchEvaluator:
    """Evaluator for running multiple test cases."""
    
    def __init__(self, evaluator_type: Optional[str] = None):
        """Initialize the batch evaluator."""
        self.evaluator = LLMEvaluator(evaluator_type)
    
    def evaluate_test_suite(
        self,
        test_cases: list[TestCase],
        agent_responses: Dict[str, str],
        extracted_memories: Optional[Dict[str, str]] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple test cases.
        
        Args:
            test_cases: List of test cases to evaluate
            agent_responses: Dictionary mapping test_id to agent response
            extracted_memories: Optional dictionary mapping test_id to extracted memory
            
        Returns:
            Dictionary mapping test_id to evaluation result
        """
        results = {}
        extracted_memories = extracted_memories or {}
        
        for test_case in test_cases:
            if test_case.test_id not in agent_responses:
                results[test_case.test_id] = EvaluationResult(
                    test_id=test_case.test_id,
                    reward=0.0,
                    passed=False,  # For backward compatibility
                    reasoning="No agent response provided for this test case",
                    required_info_found={}
                )
                continue
            
            result = self.evaluator.evaluate(
                test_case,
                agent_responses[test_case.test_id],
                extracted_memories.get(test_case.test_id)
            )
            results[test_case.test_id] = result
        
        return results
    
    def generate_report(
        self,
        results: Dict[str, EvaluationResult],
        test_cases: list[TestCase]
    ) -> str:
        """Generate a summary report of evaluation results."""
        report = "=" * 80 + "\n"
        report += "USER MEMORY EVALUATION REPORT\n"
        report += "=" * 80 + "\n\n"
        
        # Group results by category
        categories = {"layer1": [], "layer2": [], "layer3": []}
        for test_case in test_cases:
            if test_case.test_id in results:
                categories[test_case.category].append(
                    (test_case, results[test_case.test_id])
                )
        
        # Report for each category
        for category, items in categories.items():
            if not items:
                continue
                
            report += f"\n{category.upper()} - "
            if category == "layer1":
                report += "Basic Recall & Direct Retrieval\n"
            elif category == "layer2":
                report += "Contextual Reasoning & Disambiguation\n"
            elif category == "layer3":
                report += "Cross-Session Synthesis & Proactive Assistance\n"
            report += "-" * 60 + "\n"
            
            # Calculate pass count based on reward threshold (0.8)
            passed = sum(1 for _, result in items if (result.passed if result.passed is not None else result.reward >= 0.8))
            total = len(items)
            avg_reward = sum(result.reward for _, result in items) / total if total > 0 else 0
            
            report += f"Pass Rate (≥0.8): {passed}/{total} ({100*passed/total:.1f}%)\n"
            report += f"Average Reward: {avg_reward:.3f}/1.000\n\n"
            
            # Individual test results
            for test_case, result in items:
                # Determine pass/fail based on reward or passed field
                is_pass = result.passed if result.passed is not None else result.reward >= 0.8
                status = "✓ PASS" if is_pass else "✗ FAIL"
                report += f"  [{status}] {test_case.title} (Reward: {result.reward:.3f})\n"
                if result.reward < 0.8:
                    report += f"    Reason: {result.reasoning}\n"
            
        # Overall summary
        report += "\n" + "=" * 80 + "\n"
        report += "OVERALL SUMMARY\n"
        report += "=" * 80 + "\n"
        
        all_results = list(results.values())
        total_passed = sum(1 for r in all_results if (r.passed if r.passed is not None else r.reward >= 0.8))
        total_tests = len(all_results)
        overall_avg = sum(r.reward for r in all_results) / total_tests if total_tests > 0 else 0
        
        report += f"Total Tests: {total_tests}\n"
        report += f"Passed: {total_passed}\n"
        report += f"Failed: {total_tests - total_passed}\n"
        report += f"Pass Rate (≥0.8): {100*total_passed/total_tests:.1f}%\n"
        report += f"Average Reward: {overall_avg:.3f}/1.000\n"
        
        return report
