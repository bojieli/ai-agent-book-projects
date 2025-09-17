"""
LOCOMO Benchmark Integration for User Memory System
Based on: https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/LOCOMO
"""

import json
import os
import logging
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from agent import UserMemoryAgent
from config import Config, MemoryMode

logger = logging.getLogger(__name__)


@dataclass
class LOCOMOResult:
    """Result of a LOCOMO benchmark test"""
    test_id: str
    memory_mode: str
    success: bool
    score: float
    response_time: float
    memory_retrievals: int
    memory_updates: int
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class LOCOMOBenchmark:
    """LOCOMO benchmark implementation for memory systems"""
    
    def __init__(self, dataset_path: str = None):
        """
        Initialize LOCOMO benchmark
        
        Args:
            dataset_path: Path to LOCOMO dataset
        """
        self.dataset_path = dataset_path or Config.LOCOMO_DATASET_PATH
        self.results_dir = Config.LOCOMO_OUTPUT_DIR
        self.test_cases = []
        self.load_dataset()
    
    def load_dataset(self):
        """Load LOCOMO dataset"""
        # Try to load from local file
        local_file = os.path.join(self.dataset_path, "locomo_test_cases.json")
        
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                self.test_cases = json.load(f)
            logger.info(f"Loaded {len(self.test_cases)} LOCOMO test cases")
        else:
            # If local file doesn't exist, create sample test cases
            self.test_cases = self._create_sample_test_cases()
            os.makedirs(self.dataset_path, exist_ok=True)
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_cases, f, indent=2, ensure_ascii=False)
            logger.info(f"Created {len(self.test_cases)} sample LOCOMO test cases")
    
    def _create_sample_test_cases(self) -> List[Dict[str, Any]]:
        """Create sample test cases based on LOCOMO structure"""
        return [
            {
                "test_id": "personal_info_retention",
                "category": "memory_retention",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "Hi, I'm Alice. I work as a software engineer at TechCorp.",
                        "expected_memory": ["name: Alice", "occupation: software engineer", "company: TechCorp"]
                    },
                    {
                        "turn": 2,
                        "user": "What do you remember about me?",
                        "expected_response_contains": ["Alice", "software engineer", "TechCorp"]
                    }
                ]
            },
            {
                "test_id": "preference_tracking",
                "category": "preference_memory",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "I prefer Python over Java for backend development, and I love dark theme IDEs.",
                        "expected_memory": ["language_preference: Python", "theme_preference: dark"]
                    },
                    {
                        "turn": 2,
                        "user": "What programming setup would you recommend for me?",
                        "expected_response_contains": ["Python", "dark theme"]
                    }
                ]
            },
            {
                "test_id": "context_switching",
                "category": "context_management",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "I'm planning a trip to Tokyo next month for a tech conference.",
                        "expected_memory": ["travel_plan: Tokyo", "purpose: tech conference"]
                    },
                    {
                        "turn": 2,
                        "user": "By the way, my favorite color is blue.",
                        "expected_memory": ["favorite_color: blue"]
                    },
                    {
                        "turn": 3,
                        "user": "What should I pack for my trip?",
                        "expected_response_contains": ["Tokyo", "conference", "tech"]
                    }
                ]
            },
            {
                "test_id": "memory_update",
                "category": "memory_modification",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "I live in San Francisco.",
                        "expected_memory": ["location: San Francisco"]
                    },
                    {
                        "turn": 2,
                        "user": "Actually, I just moved to Seattle last week.",
                        "expected_memory": ["location: Seattle"],
                        "memory_should_not_contain": ["San Francisco"]
                    },
                    {
                        "turn": 3,
                        "user": "Where do I live?",
                        "expected_response_contains": ["Seattle"],
                        "response_should_not_contain": ["San Francisco"]
                    }
                ]
            },
            {
                "test_id": "multi_session_continuity",
                "category": "session_continuity",
                "sessions": [
                    {
                        "session_id": "session_1",
                        "conversations": [
                            {
                                "turn": 1,
                                "user": "I'm learning Spanish and practice 30 minutes every day.",
                                "expected_memory": ["learning: Spanish", "practice_duration: 30 minutes daily"]
                            }
                        ]
                    },
                    {
                        "session_id": "session_2",
                        "conversations": [
                            {
                                "turn": 1,
                                "user": "How long have I been practicing my language studies?",
                                "expected_response_contains": ["Spanish", "30 minutes"]
                            }
                        ]
                    }
                ]
            },
            {
                "test_id": "complex_reasoning",
                "category": "reasoning_with_memory",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "I'm allergic to peanuts and shellfish.",
                        "expected_memory": ["allergies: peanuts, shellfish"]
                    },
                    {
                        "turn": 2,
                        "user": "I'm thinking of trying Thai food. Any recommendations?",
                        "expected_response_contains": ["avoid", "peanut", "shellfish"],
                        "reasoning_check": "Should warn about common allergens in Thai cuisine"
                    }
                ]
            },
            {
                "test_id": "temporal_memory",
                "category": "time_awareness",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "My birthday is on June 15th.",
                        "expected_memory": ["birthday: June 15"]
                    },
                    {
                        "turn": 2,
                        "user": "How many days until my birthday?",
                        "response_type": "temporal_calculation",
                        "expected_response_contains": ["June 15"]
                    }
                ]
            },
            {
                "test_id": "conflicting_information",
                "category": "conflict_resolution",
                "conversations": [
                    {
                        "turn": 1,
                        "user": "I have 2 cats named Fluffy and Whiskers.",
                        "expected_memory": ["pets: 2 cats", "pet_names: Fluffy, Whiskers"]
                    },
                    {
                        "turn": 2,
                        "user": "I got a new dog yesterday! Now I have 3 pets.",
                        "expected_memory": ["pets: 3 total", "has_dog: true"],
                        "reasoning_check": "Should reconcile pet count"
                    },
                    {
                        "turn": 3,
                        "user": "Tell me about my pets.",
                        "expected_response_contains": ["2 cats", "1 dog", "Fluffy", "Whiskers", "3 pets"]
                    }
                ]
            }
        ]
    
    def run_single_test(
        self,
        agent: UserMemoryAgent,
        test_case: Dict[str, Any]
    ) -> LOCOMOResult:
        """
        Run a single test case
        
        Args:
            agent: User memory agent
            test_case: Test case definition
            
        Returns:
            Test result
        """
        test_id = test_case.get("test_id", "unknown")
        start_time = time.time()
        
        try:
            if "sessions" in test_case:
                # Multi-session test
                return self._run_multi_session_test(agent, test_case)
            else:
                # Single session test
                return self._run_single_session_test(agent, test_case)
                
        except Exception as e:
            logger.error(f"Error running test {test_id}: {e}")
            return LOCOMOResult(
                test_id=test_id,
                memory_mode=agent.memory_mode.value,
                success=False,
                score=0.0,
                response_time=time.time() - start_time,
                memory_retrievals=0,
                memory_updates=0,
                details={"error": str(e)}
            )
    
    def _run_single_session_test(
        self,
        agent: UserMemoryAgent,
        test_case: Dict[str, Any]
    ) -> LOCOMOResult:
        """Run a single session test"""
        test_id = test_case.get("test_id", "unknown")
        start_time = time.time()
        
        # Start new session
        session_id = agent.start_session()
        
        total_score = 0.0
        total_checks = 0
        details = {
            "session_id": session_id,
            "turns": []
        }
        
        # Run each conversation turn
        for conv in test_case.get("conversations", []):
            turn_num = conv.get("turn", 0)
            user_message = conv.get("user", "")
            
            # Get agent response
            response = agent.chat(user_message)
            
            turn_details = {
                "turn": turn_num,
                "user": user_message,
                "response": response,
                "checks": []
            }
            
            # Check expected response contents
            if "expected_response_contains" in conv:
                for expected in conv["expected_response_contains"]:
                    contains = expected.lower() in response.lower()
                    turn_details["checks"].append({
                        "type": "response_contains",
                        "expected": expected,
                        "found": contains
                    })
                    total_score += 1.0 if contains else 0.0
                    total_checks += 1
            
            # Check response should not contain
            if "response_should_not_contain" in conv:
                for unexpected in conv["response_should_not_contain"]:
                    not_contains = unexpected.lower() not in response.lower()
                    turn_details["checks"].append({
                        "type": "response_not_contains",
                        "unexpected": unexpected,
                        "correct": not_contains
                    })
                    total_score += 1.0 if not_contains else 0.0
                    total_checks += 1
            
            # Check memory updates
            if "expected_memory" in conv:
                memory_summary = agent.get_memory_summary()
                for expected_mem in conv["expected_memory"]:
                    contains = expected_mem.lower() in memory_summary.lower()
                    turn_details["checks"].append({
                        "type": "memory_contains",
                        "expected": expected_mem,
                        "found": contains
                    })
                    total_score += 1.0 if contains else 0.0
                    total_checks += 1
            
            details["turns"].append(turn_details)
        
        # Calculate final score
        final_score = (total_score / total_checks) if total_checks > 0 else 0.0
        
        return LOCOMOResult(
            test_id=test_id,
            memory_mode=agent.memory_mode.value,
            success=final_score >= 0.7,  # 70% threshold for success
            score=final_score,
            response_time=time.time() - start_time,
            memory_retrievals=len(details["turns"]),
            memory_updates=len([t for t in details["turns"] if any(c["type"] == "memory_contains" for c in t.get("checks", []))]),
            details=details
        )
    
    def _run_multi_session_test(
        self,
        agent: UserMemoryAgent,
        test_case: Dict[str, Any]
    ) -> LOCOMOResult:
        """Run a multi-session test"""
        test_id = test_case.get("test_id", "unknown")
        start_time = time.time()
        
        total_score = 0.0
        total_checks = 0
        details = {
            "sessions": []
        }
        
        # Run each session
        for session_def in test_case.get("sessions", []):
            # Start new session
            session_id = agent.start_session()
            
            session_details = {
                "session_id": session_id,
                "turns": []
            }
            
            # Run conversations in this session
            for conv in session_def.get("conversations", []):
                turn_num = conv.get("turn", 0)
                user_message = conv.get("user", "")
                
                # Get agent response
                response = agent.chat(user_message)
                
                turn_details = {
                    "turn": turn_num,
                    "user": user_message,
                    "response": response,
                    "checks": []
                }
                
                # Check expected response contents
                if "expected_response_contains" in conv:
                    for expected in conv["expected_response_contains"]:
                        contains = expected.lower() in response.lower()
                        turn_details["checks"].append({
                            "type": "response_contains",
                            "expected": expected,
                            "found": contains
                        })
                        total_score += 1.0 if contains else 0.0
                        total_checks += 1
                
                # Check memory updates
                if "expected_memory" in conv:
                    memory_summary = agent.get_memory_summary()
                    for expected_mem in conv["expected_memory"]:
                        contains = expected_mem.lower() in memory_summary.lower()
                        turn_details["checks"].append({
                            "type": "memory_contains",
                            "expected": expected_mem,
                            "found": contains
                        })
                        total_score += 1.0 if contains else 0.0
                        total_checks += 1
                
                session_details["turns"].append(turn_details)
            
            details["sessions"].append(session_details)
        
        # Calculate final score
        final_score = (total_score / total_checks) if total_checks > 0 else 0.0
        
        return LOCOMOResult(
            test_id=test_id,
            memory_mode=agent.memory_mode.value,
            success=final_score >= 0.7,
            score=final_score,
            response_time=time.time() - start_time,
            memory_retrievals=sum(len(s["turns"]) for s in details["sessions"]),
            memory_updates=sum(len([t for t in s["turns"] if any(c["type"] == "memory_contains" for c in t.get("checks", []))]) for s in details["sessions"]),
            details=details
        )
    
    def run_benchmark(
        self,
        memory_modes: List[MemoryMode] = None,
        test_ids: List[str] = None
    ) -> Dict[str, List[LOCOMOResult]]:
        """
        Run full benchmark
        
        Args:
            memory_modes: List of memory modes to test (defaults to all)
            test_ids: Specific test IDs to run (defaults to all)
            
        Returns:
            Results grouped by memory mode
        """
        memory_modes = memory_modes or [MemoryMode.NOTES, MemoryMode.JSON_CARDS]
        test_cases_to_run = self.test_cases
        
        if test_ids:
            test_cases_to_run = [tc for tc in self.test_cases if tc.get("test_id") in test_ids]
        
        results = {}
        
        for mode in memory_modes:
            logger.info(f"Running benchmark with {mode.value} memory mode")
            mode_results = []
            
            for test_case in test_cases_to_run:
                # Create fresh agent for each test
                user_id = f"benchmark_user_{test_case.get('test_id', 'unknown')}"
                agent = UserMemoryAgent(
                    user_id=user_id,
                    memory_mode=mode,
                    enable_streaming=False,
                    verbose=False
                )
                
                # CRITICAL: Clear any existing memory for this user before test
                # This ensures clean test runs even if the same test_id is run multiple times
                if hasattr(agent, 'memory_manager') and hasattr(agent.memory_manager, 'clear_all_memories'):
                    agent.memory_manager.clear_all_memories()
                    logger.info(f"Cleared memory for user {user_id} before test")
                
                # Run test
                result = self.run_single_test(agent, test_case)
                mode_results.append(result)
                
                logger.info(f"Test {result.test_id}: {'✓' if result.success else '✗'} (Score: {result.score:.2f})")
            
            results[mode.value] = mode_results
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict[str, List[LOCOMOResult]]):
        """Save benchmark results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(
            self.results_dir,
            f"locomo_results_{timestamp}.json"
        )
        
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Convert results to dict
        results_dict = {
            mode: [r.to_dict() for r in mode_results]
            for mode, mode_results in results.items()
        }
        
        # Add summary statistics
        summary = {}
        for mode, mode_results in results.items():
            scores = [r.score for r in mode_results]
            summary[mode] = {
                "total_tests": len(mode_results),
                "passed": sum(1 for r in mode_results if r.success),
                "failed": sum(1 for r in mode_results if not r.success),
                "average_score": sum(scores) / len(scores) if scores else 0,
                "average_response_time": sum(r.response_time for r in mode_results) / len(mode_results) if mode_results else 0
            }
        
        output = {
            "timestamp": timestamp,
            "summary": summary,
            "results": results_dict
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {result_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("LOCOMO BENCHMARK SUMMARY")
        print("="*60)
        
        for mode, stats in summary.items():
            print(f"\n{mode.upper()} Mode:")
            print(f"  Total Tests: {stats['total_tests']}")
            print(f"  Passed: {stats['passed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Average Score: {stats['average_score']:.2%}")
            print(f"  Average Response Time: {stats['average_response_time']:.2f}s")
        
        print("="*60)
