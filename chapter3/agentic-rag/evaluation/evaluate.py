"""Evaluation framework for Agentic RAG system"""

import json
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import os

# ``evaluation`` is intentionally runnable both as a script directory and via
# pytest from the repository root.  Put this experiment's directory first so
# the unqualified educational imports below cannot resolve a sibling
# experiment's ``config.py``/``agent.py`` from an earlier sys.path entry.
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_DIR in sys.path:
    sys.path.remove(_PROJECT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from config import Config
from agent import AgenticRAG


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Evaluate RAG system performance"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.agent = AgenticRAG(self.config)
        self.results = {
            "agentic": [],
            "non_agentic": []
        }
        
    def load_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Load evaluation dataset"""
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_response(self, 
                         response: str, 
                         test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single response"""
        evaluation = {
            "case_id": test_case["id"],
            "question": test_case["question"],
            "response": response,
            "metrics": {}
        }
        
        # Check for expected keywords (for simple cases)
        if "expected_keywords" in test_case:
            keywords_found = []
            keywords_missing = []
            
            for keyword in test_case["expected_keywords"]:
                if keyword.lower() in response.lower():
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)
            
            evaluation["metrics"]["keyword_recall"] = len(keywords_found) / len(test_case["expected_keywords"]) if test_case["expected_keywords"] else 1.0
            evaluation["metrics"]["keywords_found"] = keywords_found
            evaluation["metrics"]["keywords_missing"] = keywords_missing
        
        # Check for analysis points (for complex cases)
        if "expected_analysis" in test_case:
            analysis_found = []
            analysis_missing = []
            
            for point in test_case["expected_analysis"]:
                if point.lower() in response.lower():
                    analysis_found.append(point)
                else:
                    analysis_missing.append(point)
            
            evaluation["metrics"]["analysis_recall"] = len(analysis_found) / len(test_case["expected_analysis"]) if test_case["expected_analysis"] else 1.0
            evaluation["metrics"]["analysis_found"] = analysis_found
            evaluation["metrics"]["analysis_missing"] = analysis_missing
        
        # Check for citations
        citation_count = response.count("[Doc:") + response.count("[Chunk:")
        evaluation["metrics"]["has_citations"] = citation_count > 0
        evaluation["metrics"]["citation_count"] = citation_count
        
        # Response length
        evaluation["metrics"]["response_length"] = len(response)
        
        # Check if response indicates no answer
        no_answer_indicators = ["无法回答", "没有找到", "知识库中没有", "cannot answer", "not found"]
        evaluation["metrics"]["gave_answer"] = not any(indicator in response.lower() for indicator in no_answer_indicators)
        
        return evaluation
    
    def run_test_case(self, test_case: Dict[str, Any], mode: str = "agentic") -> Dict[str, Any]:
        """Run a single test case"""
        logger.info(f"Running {mode} mode for case {test_case['id']}")
        
        start_time = time.time()
        
        try:
            if mode == "agentic":
                response = self.agent.query(test_case["question"], stream=False)
            else:
                response = self.agent.query_non_agentic(test_case["question"], stream=False)
            
            elapsed_time = time.time() - start_time
            
            # Clear history for next test
            self.agent.clear_history()
            
            # Evaluate response
            evaluation = self.evaluate_response(response, test_case)
            evaluation["mode"] = mode
            evaluation["elapsed_time"] = elapsed_time
            evaluation["difficulty"] = test_case.get("difficulty", "unknown")
            evaluation["success"] = True
            
        except Exception as e:
            logger.error(f"Error in test case {test_case['id']}: {e}")
            evaluation = {
                "case_id": test_case["id"],
                "question": test_case["question"],
                "mode": mode,
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }
        
        return evaluation
    
    def run_evaluation(self, dataset_path: str, output_dir: str = "results"):
        """Run full evaluation"""
        # Load dataset
        dataset = self.load_dataset(dataset_path)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Combine all test cases
        all_cases = dataset["simple_cases"] + dataset["complex_cases"]
        
        # Run agentic mode
        logger.info("=" * 60)
        logger.info("Running AGENTIC mode evaluation")
        logger.info("=" * 60)
        
        agentic_results = []
        for test_case in all_cases:
            result = self.run_test_case(test_case, mode="agentic")
            agentic_results.append(result)
            time.sleep(1)  # Rate limiting
        
        # Run non-agentic mode
        logger.info("=" * 60)
        logger.info("Running NON-AGENTIC mode evaluation")
        logger.info("=" * 60)
        
        non_agentic_results = []
        for test_case in all_cases:
            result = self.run_test_case(test_case, mode="non_agentic")
            non_agentic_results.append(result)
            time.sleep(1)  # Rate limiting
        
        # Compute aggregate metrics
        agentic_metrics = self.compute_aggregate_metrics(agentic_results)
        non_agentic_metrics = self.compute_aggregate_metrics(non_agentic_results)
        
        # Save results
        results = {
            "dataset": dataset_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "llm_provider": self.config.llm.provider,
                "llm_model": self.agent.model,
                "kb_type": self.config.knowledge_base.type.value
            },
            "agentic": {
                "results": agentic_results,
                "metrics": agentic_metrics
            },
            "non_agentic": {
                "results": non_agentic_results,
                "metrics": non_agentic_metrics
            },
            "comparison": self.compare_modes(agentic_metrics, non_agentic_metrics)
        }
        
        # Save to file
        output_file = output_path / f"evaluation_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def compute_aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute aggregate metrics from results"""
        metrics = {
            "total_cases": len(results),
            "successful_cases": sum(1 for r in results if r.get("success", False)),
            "failed_cases": sum(1 for r in results if not r.get("success", False)),
            "average_time": 0,
            "total_time": 0
        }
        
        # Separate by difficulty
        simple_results = [r for r in results if r.get("difficulty") == "easy"]
        medium_results = [r for r in results if r.get("difficulty") == "medium"]
        hard_results = [r for r in results if r.get("difficulty") == "hard"]
        
        # Compute metrics for successful cases
        successful_results = [r for r in results if r.get("success", False)]
        
        if successful_results:
            # Time metrics
            times = [r["elapsed_time"] for r in successful_results]
            metrics["average_time"] = sum(times) / len(times)
            metrics["total_time"] = sum(times)
            metrics["min_time"] = min(times)
            metrics["max_time"] = max(times)
            
            # Response quality metrics
            metrics["cases_with_citations"] = sum(1 for r in successful_results 
                                                 if r.get("metrics", {}).get("has_citations", False))
            metrics["cases_gave_answer"] = sum(1 for r in successful_results 
                                              if r.get("metrics", {}).get("gave_answer", False))
            
            # Average response length
            lengths = [r.get("metrics", {}).get("response_length", 0) for r in successful_results]
            metrics["average_response_length"] = sum(lengths) / len(lengths) if lengths else 0
            
            # Keyword/analysis recall (for cases that have them)
            keyword_recalls = [r["metrics"]["keyword_recall"] for r in successful_results 
                              if "keyword_recall" in r.get("metrics", {})]
            if keyword_recalls:
                metrics["average_keyword_recall"] = sum(keyword_recalls) / len(keyword_recalls)
            
            analysis_recalls = [r["metrics"]["analysis_recall"] for r in successful_results 
                               if "analysis_recall" in r.get("metrics", {})]
            if analysis_recalls:
                metrics["average_analysis_recall"] = sum(analysis_recalls) / len(analysis_recalls)
        
        # Metrics by difficulty
        for difficulty, diff_results in [("easy", simple_results), ("medium", medium_results), ("hard", hard_results)]:
            if diff_results:
                successful = [r for r in diff_results if r.get("success", False)]
                metrics[f"{difficulty}_success_rate"] = len(successful) / len(diff_results)
                
                if successful:
                    times = [r["elapsed_time"] for r in successful]
                    metrics[f"{difficulty}_average_time"] = sum(times) / len(times)
        
        return metrics
    
    def compare_modes(self, agentic_metrics: Dict[str, Any], non_agentic_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare agentic vs non-agentic performance"""
        comparison = {}
        
        # Success rate comparison
        comparison["success_rate_diff"] = (agentic_metrics.get("successful_cases", 0) / agentic_metrics["total_cases"] - 
                                          non_agentic_metrics.get("successful_cases", 0) / non_agentic_metrics["total_cases"])
        
        # Time comparison
        if "average_time" in agentic_metrics and "average_time" in non_agentic_metrics:
            comparison["time_ratio"] = agentic_metrics["average_time"] / non_agentic_metrics["average_time"]
            comparison["time_difference"] = agentic_metrics["average_time"] - non_agentic_metrics["average_time"]
        
        # Citation comparison
        if "cases_with_citations" in agentic_metrics and "cases_with_citations" in non_agentic_metrics:
            comparison["citation_rate_diff"] = (agentic_metrics["cases_with_citations"] / agentic_metrics["successful_cases"] - 
                                               non_agentic_metrics["cases_with_citations"] / non_agentic_metrics["successful_cases"])
        
        # Response quality comparison
        if "average_keyword_recall" in agentic_metrics and "average_keyword_recall" in non_agentic_metrics:
            comparison["keyword_recall_improvement"] = (agentic_metrics["average_keyword_recall"] - 
                                                       non_agentic_metrics["average_keyword_recall"])
        
        if "average_analysis_recall" in agentic_metrics and "average_analysis_recall" in non_agentic_metrics:
            comparison["analysis_recall_improvement"] = (agentic_metrics["average_analysis_recall"] - 
                                                        non_agentic_metrics["average_analysis_recall"])
        
        # Difficulty-specific comparison
        for difficulty in ["easy", "medium", "hard"]:
            key = f"{difficulty}_success_rate"
            if key in agentic_metrics and key in non_agentic_metrics:
                comparison[f"{difficulty}_success_improvement"] = (agentic_metrics[key] - non_agentic_metrics[key])
        
        return comparison
    
    def print_summary(self, results: Dict[str, Any]):
        """Print evaluation summary"""
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        
        print(f"\nConfiguration:")
        print(f"  LLM Provider: {results['config']['llm_provider']}")
        print(f"  LLM Model: {results['config']['llm_model']}")
        print(f"  Knowledge Base: {results['config']['kb_type']}")
        
        print(f"\n{'='*40} AGENTIC MODE {'='*40}")
        self._print_mode_summary(results["agentic"]["metrics"])
        
        print(f"\n{'='*40} NON-AGENTIC MODE {'='*40}")
        self._print_mode_summary(results["non_agentic"]["metrics"])
        
        print(f"\n{'='*40} COMPARISON {'='*40}")
        comparison = results["comparison"]
        
        print(f"Success Rate Difference: {comparison.get('success_rate_diff', 0):.2%} (Agentic better)")
        
        if "time_ratio" in comparison:
            print(f"Time Ratio: {comparison['time_ratio']:.2f}x (Agentic/Non-Agentic)")
            print(f"Time Difference: {comparison['time_difference']:.2f} seconds")
        
        if "keyword_recall_improvement" in comparison:
            print(f"Keyword Recall Improvement: {comparison['keyword_recall_improvement']:.2%}")
        
        if "analysis_recall_improvement" in comparison:
            print(f"Analysis Recall Improvement: {comparison['analysis_recall_improvement']:.2%}")
        
        print("\nDifficulty-Specific Improvements:")
        for difficulty in ["easy", "medium", "hard"]:
            key = f"{difficulty}_success_improvement"
            if key in comparison:
                print(f"  {difficulty.capitalize()}: {comparison[key]:.2%}")
        
        print("=" * 80)
    
    def _print_mode_summary(self, metrics: Dict[str, Any]):
        """Print summary for a single mode"""
        print(f"Total Cases: {metrics['total_cases']}")
        print(f"Successful: {metrics['successful_cases']} ({metrics['successful_cases']/metrics['total_cases']:.1%})")
        print(f"Failed: {metrics['failed_cases']}")
        
        if "average_time" in metrics:
            print(f"Average Time: {metrics['average_time']:.2f} seconds")
            print(f"Total Time: {metrics['total_time']:.2f} seconds")
        
        if "cases_with_citations" in metrics:
            print(f"Cases with Citations: {metrics['cases_with_citations']} ({metrics['cases_with_citations']/metrics['successful_cases']:.1%})")
        
        if "average_keyword_recall" in metrics:
            print(f"Average Keyword Recall: {metrics['average_keyword_recall']:.2%}")
        
        if "average_analysis_recall" in metrics:
            print(f"Average Analysis Recall: {metrics['average_analysis_recall']:.2%}")
        
        # Difficulty breakdown
        print("\nBy Difficulty:")
        for difficulty in ["easy", "medium", "hard"]:
            success_key = f"{difficulty}_success_rate"
            time_key = f"{difficulty}_average_time"
            if success_key in metrics:
                print(f"  {difficulty.capitalize()}: {metrics[success_key]:.1%} success", end="")
                if time_key in metrics:
                    print(f", {metrics[time_key]:.2f}s avg", end="")
                print()


def main():
    """Main evaluation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate Agentic RAG System")
    parser.add_argument("--dataset", type=str, default="legal_qa_dataset.json",
                       help="Path to evaluation dataset")
    parser.add_argument("--output", type=str, default="results",
                       help="Output directory for results")
    parser.add_argument("--provider", type=str, help="Override LLM provider")
    parser.add_argument("--model", type=str, help="Override LLM model")
    parser.add_argument("--kb-type", choices=["local", "dify"], help="Knowledge base type")
    
    args = parser.parse_args()
    
    # Configure
    config = Config.from_env()
    if args.provider:
        config.llm.provider = args.provider
    if args.model:
        config.llm.model = args.model
    if args.kb_type:
        from config import KnowledgeBaseType
        config.knowledge_base.type = KnowledgeBaseType(args.kb_type)
    
    # Run evaluation
    evaluator = RAGEvaluator(config)
    results = evaluator.run_evaluation(args.dataset, args.output)
    
    return results


if __name__ == "__main__":
    main()
