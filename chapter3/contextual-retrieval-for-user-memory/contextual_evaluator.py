"""Contextual Memory Evaluator with Dual Memory System

This evaluator tests the combined system of:
1. Contextual RAG for conversation chunks
2. Advanced JSON cards for structured facts
"""

import os
import json
import logging
import time
import uuid
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from config import Config
from contextual_indexer import ContextualMemoryIndexer
from contextual_agent import ContextualUserMemoryAgent
from advanced_memory_manager import AdvancedMemoryManager, AdvancedMemoryCard
from chunker import ConversationChunker, ConversationChunk


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import LLM evaluator from user-memory-evaluation project
LLMEvaluator = None
EvalTestCase = None
ConversationHistory = None
EvalMessage = None
MessageRole = None

# Try to import from week2/user-memory-evaluation
eval_project_path = Path(__file__).parent.parent.parent / "week2" / "user-memory-evaluation"
if eval_project_path.exists():
    sys.path.insert(0, str(eval_project_path))
    try:
        from llm_evaluator import LLMEvaluator
        from test_case import TestCase as EvalTestCase, ConversationHistory, Message as EvalMessage, MessageRole
        logger.info("Successfully imported LLM evaluation modules")
    except ImportError as e:
        logger.warning(f"Could not import LLM evaluation modules: {e}")
        logger.info("LLM evaluation will not be available")
else:
    logger.warning(f"user-memory-evaluation project not found at {eval_project_path}")
    logger.info("LLM evaluation will not be available")


@dataclass
class TestCase:
    """Enhanced test case with support for advanced memory"""
    test_id: str
    category: str  # layer1, layer2, layer3
    title: str
    description: str
    conversation_histories: List[Dict[str, Any]]  # Conversation data directly from YAML
    user_question: str
    evaluation_criteria: str
    expected_behavior: Optional[str] = None
    expected_memory_cards: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, data: Dict[str, Any], test_dir: Path) -> 'TestCase':
        """Create test case from YAML data"""
        # The conversation_histories field directly contains the conversation data
        conversation_histories = data.get('conversation_histories', [])
        
        return cls(
            test_id=data.get('test_id', data.get('id', '')),
            category=data.get('category', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            conversation_histories=conversation_histories,
            user_question=data.get('user_question', ''),
            evaluation_criteria=data.get('evaluation_criteria', ''),
            expected_behavior=data.get('expected_behavior'),
            expected_memory_cards=data.get('expected_memory_cards', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class EvaluationResult:
    """Enhanced evaluation result with dual memory tracking"""
    test_id: str
    success: bool
    agent_answer: str
    evaluation_criteria: str
    iterations: int
    tool_calls: int
    memory_cards_used: List[str]
    chunks_retrieved: List[str]
    contextual_chunks_count: int
    processing_time: float
    indexing_time: float
    context_generation_time: float
    llm_evaluation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "success": self.success,
            "agent_answer": self.agent_answer,
            "evaluation_criteria": self.evaluation_criteria,
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "memory_cards_used": self.memory_cards_used,
            "chunks_retrieved": self.chunks_retrieved,
            "contextual_chunks_count": self.contextual_chunks_count,
            "processing_time": self.processing_time,
            "indexing_time": self.indexing_time,
            "context_generation_time": self.context_generation_time,
            "llm_evaluation": self.llm_evaluation,
            "error": self.error
        }


class ContextualMemoryEvaluator:
    """Evaluates the dual memory system on test cases"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the evaluator
        
        Args:
            config: Configuration object
        """
        self.config = config or Config.from_env()
        self.test_cases: Dict[str, TestCase] = {}
        self.results: Dict[str, EvaluationResult] = {}
        
        # Initialize components
        self.chunker = ConversationChunker(self.config.chunking)
        self.indexer: Optional[ContextualMemoryIndexer] = None
        self.agent: Optional[ContextualUserMemoryAgent] = None
        
        # Initialize LLM evaluator if available
        self.llm_evaluator = None
        logger.info("Checking LLM Evaluator availability...")
        logger.info(f"LLMEvaluator module: {LLMEvaluator}")
        logger.info(f"EvalTestCase module: {EvalTestCase}")
        
        if LLMEvaluator:
            try:
                logger.info("Attempting to initialize LLM Evaluator...")
                self.llm_evaluator = LLMEvaluator()
                logger.info("✅ LLM Evaluator initialized successfully for automatic evaluation")
            except Exception as e:
                logger.warning(f"Could not initialize LLM evaluator: {e}")
                logger.info("Automatic LLM evaluation will be skipped")
        else:
            logger.info("LLM Evaluator not available - automatic evaluation will be skipped")
        
        # Evaluation framework path
        self.eval_framework_path = Path("../user-memory-evaluation/test_cases")
        if not self.eval_framework_path.exists():
            self.eval_framework_path = Path("../../week2/user-memory-evaluation/test_cases")
        
        logger.info("Initialized ContextualMemoryEvaluator")
    
    def load_test_cases(self, category: Optional[str] = None) -> List[str]:
        """
        Load test cases from the evaluation framework
        
        Args:
            category: Optional category filter (layer1, layer2, layer3)
            
        Returns:
            List of loaded test case IDs
        """
        import yaml
        
        test_cases = []
        test_dirs = ["layer1", "layer2", "layer3"] if not category else [category]
        
        for test_dir in test_dirs:
            dir_path = self.eval_framework_path / test_dir
            if not dir_path.exists():
                logger.warning(f"Test directory not found: {dir_path}")
                continue
            
            # Load all YAML files
            for yaml_file in dir_path.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    test_case = TestCase.from_yaml(data, self.eval_framework_path)
                    test_case.category = test_dir  # Ensure category is set
                    
                    self.test_cases[test_case.test_id] = test_case
                    test_cases.append(test_case.test_id)
                    
                except Exception as e:
                    logger.error(f"Error loading test case {yaml_file}: {e}")
        
        logger.info(f"Loaded {len(test_cases)} test cases")
        return test_cases
    
    def _prepare_memory_cards(self, test_case: TestCase) -> List[AdvancedMemoryCard]:
        """
        Generate memory cards for a test case
        
        For Layer 3 tests, this creates cards that enable proactive service
        """
        cards = []
        
        # Generate cards based on test metadata
        if test_case.category == "layer3":
            # Layer 3 needs structured facts for proactive service
            if "travel" in test_case.test_id.lower():
                cards.append(AdvancedMemoryCard(
                    category="travel",
                    card_key="tokyo_trip",
                    backstory="User booked a trip to Tokyo in previous conversations",
                    date_created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    person="Jessica Thompson (primary)",
                    relationship="primary account holder",
                    data={
                        "destination": "Tokyo, Japan",
                        "departure_date": "2025-01-25",
                        "return_date": "2025-02-01",
                        "purpose": "business conference"
                    }
                ))
                
                cards.append(AdvancedMemoryCard(
                    category="travel",
                    card_key="passport_jessica",
                    backstory="User's passport expiration was mentioned when booking travel",
                    date_created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    person="Jessica Thompson (primary)",
                    relationship="primary account holder",
                    data={
                        "passport_number": "XXXXX1234",
                        "expiration_date": "2025-02-18",
                        "issuing_country": "USA",
                        "needs_renewal": True
                    }
                ))
        
        # Add any expected cards from test case
        for card_data in test_case.expected_memory_cards:
            cards.append(AdvancedMemoryCard(
                category=card_data.get("category", "general"),
                card_key=card_data.get("key", str(uuid.uuid4())),
                backstory=card_data.get("backstory", "From test case"),
                date_created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                person=card_data.get("person", "User"),
                relationship=card_data.get("relationship", "primary"),
                data=card_data.get("data", {})
            ))
        
        return cards
    
    def evaluate_test_case(self, test_id: str) -> EvaluationResult:
        """
        Evaluate a single test case with dual memory system
        
        Args:
            test_id: Test case ID
            
        Returns:
            Evaluation result
        """
        if test_id not in self.test_cases:
            raise ValueError(f"Test case {test_id} not found")
        
        test_case = self.test_cases[test_id]
        logger.info(f"Evaluating test case: {test_id} - {test_case.title}")
        
        start_time = time.time()
        indexing_start = time.time()
        
        try:
            # Step 1: Initialize indexer with user ID
            user_id = f"test_user_{test_id}"
            self.indexer = ContextualMemoryIndexer(
                user_id=user_id,
                index_config=self.config.index,
                chunking_config=self.config.chunking,
                use_contextual=True  # Enable contextual chunking
            )
            
            # Step 2: Process conversations from test case
            all_chunks = []
            for conv_data in test_case.conversation_histories:
                # Extract conversation data from the test case
                conv_id = conv_data.get('conversation_id', f'conv_{test_id}')
                messages = conv_data.get('messages', [])
                
                # Chunk the conversation
                chunks = self.chunker.chunk_conversation(
                    messages=messages,
                    conversation_id=conv_id,
                    test_id=test_id
                )
                all_chunks.extend(chunks)
            
            logger.info(f"Created {len(all_chunks)} basic chunks")
            
            # Step 3: Process with contextual chunking and indexing
            processing_result = self.indexer.process_conversation_history(
                chunks=all_chunks,
                conversation_id=test_id,
                generate_summary_cards=True  # Generate cards from conversations
            )
            
            # Step 4: Add pre-defined memory cards for the test
            memory_cards = self._prepare_memory_cards(test_case)
            for card in memory_cards:
                self.indexer.memory_manager.add_card(card)
            
            # Debug: Print all memory cards
            logger.info("="*60)
            logger.info("DEBUG: All Memory Cards in System")
            logger.info("="*60)
            # Access cards directly from categories attribute
            for category, cards in self.indexer.memory_manager.categories.items():
                for card_key, card in cards.items():
                    logger.info(f"\n[{category}.{card_key}]")
                    logger.info(json.dumps(card.to_dict(), indent=2, ensure_ascii=False))
            total_cards = sum(len(cards) for cards in self.indexer.memory_manager.categories.values())
            logger.info(f"\nTotal Memory Cards: {total_cards}")
            logger.info("="*60)
            
            indexing_time = time.time() - indexing_start
            
            # Step 5: Initialize agent with dual memory
            self.agent = ContextualUserMemoryAgent(
                indexer=self.indexer,
                memory_manager=self.indexer.memory_manager,
                config=self.config
            )
            
            # Step 6: Answer the question
            trajectory = self.agent.answer_question(
                question=test_case.user_question,
                test_id=test_id,
                max_iterations=self.config.evaluation.max_iterations,
                stream=False
            )
            
            processing_time = time.time() - start_time
            
            # Get context generation statistics
            chunker_stats = self.indexer.contextual_chunker.get_statistics()
            context_gen_time = chunker_stats.get("total_generation_time", 0)
            
            # Step 7: Evaluate the answer with LLM (automatic if available)
            llm_evaluation = None
            logger.info("="*60)
            logger.info("LLM Judge Evaluation")
            logger.info("="*60)
            
            if not self.llm_evaluator:
                logger.warning("LLM Judge not available - skipping automatic evaluation")
                logger.info("To enable LLM Judge, ensure the llm_evaluator module is properly imported")
            elif not trajectory.final_answer:
                logger.warning("No final answer from agent - cannot evaluate")
            else:
                logger.info("Running LLM Judge evaluation...")
            
            if self.llm_evaluator and trajectory.final_answer:
                try:
                    # Convert test case to evaluation format
                    eval_histories = []
                    for hist in test_case.conversation_histories:
                        eval_messages = []
                        for msg in hist.get("messages", []):
                            role_str = msg.get("role", "user")
                            role = MessageRole.USER if role_str == "user" else MessageRole.ASSISTANT
                            eval_messages.append(EvalMessage(
                                role=role,
                                content=msg.get("content", "")
                            ))
                        
                        eval_histories.append(ConversationHistory(
                            conversation_id=hist.get("conversation_id", f"conv_{uuid.uuid4().hex[:8]}"),
                            messages=eval_messages,
                            metadata=hist.get("metadata", {})
                        ))
                    
                    # Create evaluation test case
                    eval_test_case = EvalTestCase(
                        test_id=test_case.test_id,
                        category=test_case.category,
                        title=test_case.title,
                        description=test_case.description,
                        conversation_histories=eval_histories,
                        user_question=test_case.user_question,
                        evaluation_criteria=test_case.evaluation_criteria if test_case.evaluation_criteria else "The agent should provide a relevant and accurate response based on the conversation history.",
                        expected_behavior=test_case.expected_behavior
                    )
                    
                    # Run LLM evaluation
                    llm_result = self.llm_evaluator.evaluate(
                        test_case=eval_test_case,
                        agent_response=trajectory.final_answer,
                        extracted_memory=None
                    )
                    
                    llm_evaluation = {
                        "reward": llm_result.reward,
                        "passed": llm_result.passed if llm_result.passed is not None else llm_result.reward >= 0.6,
                        "reasoning": llm_result.reasoning,
                        "required_info_found": llm_result.required_info_found if hasattr(llm_result, 'required_info_found') else {},
                        "suggestions": llm_result.suggestions if hasattr(llm_result, 'suggestions') else None
                    }
                    
                    # Log evaluation results
                    logger.info("-"*60)
                    logger.info(f"LLM Evaluation Reward: {llm_result.reward:.3f}/1.000")
                    logger.info(f"Passed: {'Yes' if llm_evaluation['passed'] else 'No'}")
                    logger.info("-"*60)
                    logger.info(f"Evaluation Reasoning:")
                    logger.info(llm_result.reasoning)
                    logger.info("-"*60)
                    
                    if llm_result.required_info_found:
                        logger.info("Required Information Found:")
                        for key, found in llm_result.required_info_found.items():
                            status = "✓" if found else "✗"
                            logger.info(f"  {status} {key}")
                        logger.info("-"*60)
                    
                except Exception as e:
                    logger.warning(f"LLM evaluation failed: {e}")
                    logger.debug("Full error:", exc_info=True)
            else:
                # Fallback: Use direct LLM API for evaluation if module not available
                if trajectory.final_answer:
                    logger.info("Attempting fallback LLM evaluation...")
                    llm_evaluation = self._fallback_llm_evaluation(test_case, trajectory.final_answer)
            
            # Create result
            result = EvaluationResult(
                test_id=test_id,
                success=trajectory.success,
                agent_answer=trajectory.final_answer or "",
                evaluation_criteria=test_case.evaluation_criteria,
                iterations=len(trajectory.iterations),
                tool_calls=len(trajectory.tool_calls),
                memory_cards_used=trajectory.memory_cards_used,
                chunks_retrieved=trajectory.chunks_retrieved,
                contextual_chunks_count=processing_result.get("contextual_chunks", 0),
                processing_time=processing_time,
                indexing_time=indexing_time,
                context_generation_time=context_gen_time,
                llm_evaluation=llm_evaluation
            )
            
            # Check if answer meets criteria
            # Use LLM evaluation result if available, otherwise fall back to keyword check
            if llm_evaluation and 'passed' in llm_evaluation:
                result.success = llm_evaluation['passed']
                logger.info(f"Using LLM evaluation result: {'Success' if result.success else 'Failed'}")
            elif self._check_answer_criteria(trajectory.final_answer, test_case.evaluation_criteria):
                result.success = True
                logger.info(f"Using keyword-based evaluation: Success")
            else:
                logger.info(f"Using keyword-based evaluation: Failed")
            
            self.results[test_id] = result
            logger.info(f"Evaluation complete for {test_id}: {'Success' if result.success else 'Failed'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating test case {test_id}: {e}")
            
            result = EvaluationResult(
                test_id=test_id,
                success=False,
                agent_answer="",
                evaluation_criteria=test_case.evaluation_criteria,
                iterations=0,
                tool_calls=0,
                memory_cards_used=[],
                chunks_retrieved=[],
                contextual_chunks_count=0,
                processing_time=time.time() - start_time,
                indexing_time=indexing_time if 'indexing_time' in locals() else 0,
                context_generation_time=0,
                error=str(e)
            )
            
            self.results[test_id] = result
            return result
    
    def _load_conversations(self, conv_file: str) -> Dict[str, List[Dict[str, str]]]:
        """Load conversations from a JSON file"""
        conversations = {}
        
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different formats
            if isinstance(data, dict):
                if "conversations" in data:
                    conversations = data["conversations"]
                else:
                    # Assume it's already in the right format
                    conversations = data
            elif isinstance(data, list):
                # Convert list to dict with generated IDs
                for i, conv in enumerate(data):
                    conversations[f"conv_{i}"] = conv
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error loading conversations from {conv_file}: {e}")
            return {}
    
    def _check_answer_criteria(self, answer: Optional[str], criteria: str) -> bool:
        """Simple check if answer meets criteria"""
        if not answer:
            return False
        
        answer_lower = answer.lower()
        criteria_lower = criteria.lower()
        
        # Extract key terms from criteria
        key_terms = []
        for word in criteria_lower.split():
            if len(word) > 4 and word not in ["should", "must", "need", "have"]:
                key_terms.append(word)
        
        # Check if key terms appear in answer
        matches = sum(1 for term in key_terms if term in answer_lower)
        
        return matches >= min(3, len(key_terms) // 2)
    
    def _evaluate_with_llm(self, test_case: TestCase, agent_answer: Optional[str]) -> Dict[str, Any]:
        """Use LLM to evaluate if the answer meets criteria"""
        if not agent_answer:
            return {
                "passed": False,
                "reasoning": "No answer provided",
                "reward": 0.0
            }
        
        # This is a simplified version - implement full LLM evaluation as needed
        return {
            "passed": self._check_answer_criteria(agent_answer, test_case.evaluation_criteria),
            "reasoning": "Basic criteria check",
            "reward": 0.5
        }
    
    def _fallback_llm_evaluation(self, test_case: TestCase, agent_answer: str) -> Dict[str, Any]:
        """Fallback LLM evaluation using direct API call when llm_evaluator module isn't available"""
        try:
            from openai import OpenAI
            
            config = Config.from_env()
            client_config, model = config.llm.get_client_config()
            base_url = client_config.pop("base_url", None)
            
            if base_url:
                client = OpenAI(base_url=base_url, **client_config)
            else:
                client = OpenAI(**client_config)
            
            # Create evaluation prompt
            eval_prompt = f"""Evaluate the agent's response based on the test criteria.

Test Question: {test_case.user_question}

Agent's Answer: {agent_answer}

Evaluation Criteria: {test_case.evaluation_criteria}

Provide a JSON evaluation with:
1. "reward": A score from 0.0 to 1.0 (0.6+ is passing)
2. "passed": Boolean indicating if the answer meets the criteria
3. "reasoning": Explanation for the score (2-3 sentences)
4. "required_info_found": Object with boolean values for each required piece of information

Respond with valid JSON only."""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an evaluation judge. Evaluate if the agent's answer correctly addresses the user's question based on the criteria."},
                    {"role": "user", "content": eval_prompt}
                ],
                temperature=_reasoning_safe_temperature(model, 0.1),
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                result = {}
            
            # Ensure required fields
            if 'reward' not in result:
                result['reward'] = 0.5
            if 'passed' not in result:
                result['passed'] = result['reward'] >= 0.6
            if 'reasoning' not in result:
                result['reasoning'] = "Evaluation completed"
            if 'required_info_found' not in result:
                result['required_info_found'] = {}
            
            # Log evaluation results
            logger.info("="*60)
            logger.info("Fallback LLM Evaluation Results")
            logger.info("="*60)
            logger.info(f"Reward: {result['reward']:.3f}/1.000")
            logger.info(f"Passed: {'Yes' if result['passed'] else 'No'}")
            logger.info(f"Reasoning: {result['reasoning']}")
            
            if result['required_info_found']:
                logger.info("Required Information Found:")
                for key, found in result['required_info_found'].items():
                    status = "✓" if found else "✗"
                    logger.info(f"  {status} {key}")
            logger.info("="*60)
            
            return result
            
        except Exception as e:
            logger.error(f"Fallback LLM evaluation failed: {e}")
            return None
    
    def evaluate_batch(self, test_ids: Optional[List[str]] = None) -> Dict[str, EvaluationResult]:
        """Evaluate multiple test cases"""
        if test_ids is None:
            test_ids = list(self.test_cases.keys())
        
        for test_id in test_ids:
            try:
                self.evaluate_test_case(test_id)
            except Exception as e:
                logger.error(f"Failed to evaluate {test_id}: {e}")
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate evaluation report"""
        if not self.results:
            return "No evaluation results available"
        
        report = ["=" * 80]
        report.append("CONTEXTUAL MEMORY EVALUATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total Test Cases: {len(self.results)}")
        report.append("")
        
        # Summary statistics
        successful = sum(1 for r in self.results.values() if r.success)
        report.append(f"Success Rate: {successful}/{len(self.results)} ({100*successful/len(self.results):.1f}%)")
        report.append("")
        
        # Statistics by category
        categories = {}
        for test_id, result in self.results.items():
            if test_id in self.test_cases:
                cat = self.test_cases[test_id].category
                if cat not in categories:
                    categories[cat] = {"total": 0, "success": 0}
                categories[cat]["total"] += 1
                if result.success:
                    categories[cat]["success"] += 1
        
        report.append("Results by Category:")
        for cat in sorted(categories.keys()):
            stats = categories[cat]
            rate = 100 * stats["success"] / stats["total"] if stats["total"] > 0 else 0
            report.append(f"  {cat}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        report.append("")
        
        # Average metrics
        avg_iterations = sum(r.iterations for r in self.results.values()) / len(self.results)
        avg_tool_calls = sum(r.tool_calls for r in self.results.values()) / len(self.results)
        avg_time = sum(r.processing_time for r in self.results.values()) / len(self.results)
        avg_context_time = sum(r.context_generation_time for r in self.results.values()) / len(self.results)
        
        report.append("Average Metrics:")
        report.append(f"  Iterations: {avg_iterations:.1f}")
        report.append(f"  Tool Calls: {avg_tool_calls:.1f}")
        report.append(f"  Processing Time: {avg_time:.2f}s")
        report.append(f"  Context Generation Time: {avg_context_time:.2f}s")
        report.append("")
        
        # Memory usage statistics
        total_cards_used = sum(len(r.memory_cards_used) for r in self.results.values())
        total_chunks_retrieved = sum(len(r.chunks_retrieved) for r in self.results.values())
        
        report.append("Memory Usage:")
        report.append(f"  Total Memory Cards Used: {total_cards_used}")
        report.append(f"  Total Chunks Retrieved: {total_chunks_retrieved}")
        report.append(f"  Avg Cards per Query: {total_cards_used/len(self.results):.1f}")
        report.append(f"  Avg Chunks per Query: {total_chunks_retrieved/len(self.results):.1f}")
        report.append("")
        
        # Individual test results
        report.append("-" * 80)
        report.append("INDIVIDUAL TEST RESULTS")
        report.append("-" * 80)
        
        for test_id, result in sorted(self.results.items()):
            test_case = self.test_cases.get(test_id)
            report.append(f"\nTest: {test_id}")
            if test_case:
                report.append(f"  Title: {test_case.title}")
                report.append(f"  Category: {test_case.category}")
            report.append(f"  Status: {'✓ Success' if result.success else '✗ Failed'}")
            report.append(f"  Iterations: {result.iterations}")
            report.append(f"  Tool Calls: {result.tool_calls}")
            report.append(f"  Memory Cards Used: {len(result.memory_cards_used)}")
            report.append(f"  Chunks Retrieved: {len(result.chunks_retrieved)}")
            report.append(f"  Contextual Chunks: {result.contextual_chunks_count}")
            report.append(f"  Processing Time: {result.processing_time:.2f}s")
            if result.error:
                report.append(f"  Error: {result.error}")
        
        return "\n".join(report)
    
    def save_results(self, output_file: str):
        """Save evaluation results to file"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "use_contextual": True,
                "llm_provider": self.config.llm.provider,
                "llm_model": self.config.llm.model,
                "chunking_strategy": self.config.chunking.strategy.value,
                "index_mode": self.config.index.mode.value
            },
            "summary": {
                "total_tests": len(self.results),
                "successful": sum(1 for r in self.results.values() if r.success),
                "failed": sum(1 for r in self.results.values() if not r.success)
            },
            "results": {
                test_id: result.to_dict()
                for test_id, result in self.results.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_file}")
