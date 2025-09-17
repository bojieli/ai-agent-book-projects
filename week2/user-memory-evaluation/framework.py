"""Main framework for User Memory Evaluation."""

import os
import yaml
from typing import List, Dict, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from config import Config
from models import (
    TestCase, ConversationHistory, ConversationMessage,
    EvaluationResult, TestSuite, MessageRole
)
from evaluator import LLMEvaluator, BatchEvaluator


console = Console()


class UserMemoryEvaluationFramework:
    """Framework for evaluating user memory capabilities of AI agents."""
    
    def __init__(self, test_cases_dir: Optional[str] = None):
        """
        Initialize the framework.
        
        Args:
            test_cases_dir: Directory containing test case YAML files
        """
        self.test_cases_dir = Path(test_cases_dir or Config.TEST_CASES_DIR)
        self.test_suite = None
        self.evaluator = None
        self._load_test_cases()
    
    def _load_test_cases(self) -> None:
        """Load all test cases from YAML files."""
        test_cases = []
        
        for category in ["layer1", "layer2", "layer3"]:
            category_dir = self.test_cases_dir / category
            if not category_dir.exists():
                console.print(f"[yellow]Warning: Category directory {category_dir} does not exist[/yellow]")
                continue
            
            for yaml_file in category_dir.glob("*.yaml"):
                try:
                    test_case = self._load_single_test_case(yaml_file)
                    if test_case and test_case.validate():
                        test_cases.append(test_case)
                    else:
                        console.print(f"[red]Invalid test case: {yaml_file}[/red]")
                except Exception as e:
                    console.print(f"[red]Error loading {yaml_file}: {e}[/red]")
        
        self.test_suite = TestSuite(
            name="User Memory Evaluation Suite",
            version="1.0.0",
            test_cases=test_cases
        )
        
        console.print(f"[green]Loaded {len(test_cases)} test cases[/green]")
    
    def _load_single_test_case(self, yaml_file: Path) -> Optional[TestCase]:
        """Load a single test case from a YAML file."""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return None
        
        # Parse conversation histories
        conversation_histories = []
        for conv_data in data.get('conversation_histories', []):
            messages = []
            # Handle both 'messages' and 'conversation' fields for backwards compatibility
            msg_list = conv_data.get('messages') or conv_data.get('conversation', [])
            for msg in msg_list:
                # Handle both dictionary format and simple format
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    messages.append(ConversationMessage(
                        role=MessageRole(msg['role']),
                        content=msg['content']
                    ))
                elif isinstance(msg, dict):
                    # Handle format like {user: "...", representative: "..."}
                    for role, content in msg.items():
                        if role in ['user', 'assistant', 'representative', 'agent']:
                            # Normalize role names
                            role_name = 'assistant' if role in ['representative', 'agent'] else role
                            messages.append(ConversationMessage(
                                role=MessageRole(role_name),
                                content=content
                            ))
            
            # Handle both 'id' and 'conversation_id' fields for backwards compatibility
            conv_id = conv_data.get('conversation_id') or conv_data.get('id')
            if not conv_id:
                raise KeyError("Conversation must have either 'conversation_id' or 'id' field")
            
            conversation_histories.append(ConversationHistory(
                conversation_id=conv_id,
                timestamp=conv_data['timestamp'],
                messages=messages,
                metadata=conv_data.get('metadata')
            ))
        
        # Parse evaluation criteria - now just a text field
        evaluation_criteria = data.get('evaluation_criteria', '')
        if isinstance(evaluation_criteria, dict):
            # Handle old format with description, required_information, etc.
            # Convert to text format for backward compatibility
            criteria_text = evaluation_criteria.get('description', '')
            if 'required_information' in evaluation_criteria:
                criteria_text += "\n\nRequired Information:\n"
                for info in evaluation_criteria['required_information']:
                    criteria_text += f"- {info}\n"
            if 'success_indicators' in evaluation_criteria:
                criteria_text += "\nSuccess Indicators:\n"
                for indicator in evaluation_criteria['success_indicators']:
                    criteria_text += f"- {indicator}\n"
            if 'failure_indicators' in evaluation_criteria and evaluation_criteria['failure_indicators']:
                criteria_text += "\nFailure Indicators:\n"
                for indicator in evaluation_criteria['failure_indicators']:
                    criteria_text += f"- {indicator}\n"
            evaluation_criteria = criteria_text
        
        return TestCase(
            test_id=data['test_id'],
            category=data['category'],
            title=data['title'],
            description=data['description'],
            conversation_histories=conversation_histories,
            user_question=data['user_question'],
            evaluation_criteria=evaluation_criteria,
            expected_behavior=data.get('expected_behavior')  # Optional field
        )
    
    def list_test_cases(self, category: Optional[str] = None) -> List[TestCase]:
        """
        List all available test cases.
        
        Args:
            category: Optional filter by category (layer1, layer2, layer3)
            
        Returns:
            List of test cases sorted by test_id
        """
        if not self.test_suite:
            return []
        
        if category:
            test_cases = self.test_suite.get_by_category(category)
        else:
            test_cases = self.test_suite.test_cases
        
        # Return sorted by test_id
        return sorted(test_cases, key=lambda tc: tc.test_id)
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """
        Get a specific test case by ID.
        
        Args:
            test_id: The test case ID
            
        Returns:
            TestCase or None if not found
        """
        if not self.test_suite:
            return None
        return self.test_suite.get_by_id(test_id)
    
    def get_conversation_histories(self, test_id: str) -> List[ConversationHistory]:
        """
        Get conversation histories for a test case.
        
        Args:
            test_id: The test case ID
            
        Returns:
            List of conversation histories
        """
        test_case = self.get_test_case(test_id)
        if not test_case:
            return []
        return test_case.conversation_histories
    
    def get_user_question(self, test_id: str) -> Optional[str]:
        """
        Get the user question for a test case.
        
        Args:
            test_id: The test case ID
            
        Returns:
            User question string or None
        """
        test_case = self.get_test_case(test_id)
        if not test_case:
            return None
        return test_case.user_question
    
    def submit_and_evaluate(
        self,
        test_id: str,
        agent_response: str,
        extracted_memory: Optional[str] = None,
        evaluator_type: Optional[str] = None
    ) -> Optional[EvaluationResult]:
        """
        Submit an agent's response and get evaluation result.
        
        Args:
            test_id: The test case ID
            agent_response: The agent's response to the user question
            extracted_memory: Optional extracted memory from the agent
            evaluator_type: Optional evaluator type (defaults to config)
            
        Returns:
            EvaluationResult or None if test case not found
        """
        test_case = self.get_test_case(test_id)
        if not test_case:
            console.print(f"[red]Test case {test_id} not found[/red]")
            return None
        
        if not self.evaluator or evaluator_type:
            self.evaluator = LLMEvaluator(evaluator_type)
        
        result = self.evaluator.evaluate(
            test_case,
            agent_response,
            extracted_memory
        )
        
        return result
    
    def evaluate_batch(
        self,
        agent_responses: Dict[str, str],
        extracted_memories: Optional[Dict[str, str]] = None,
        category: Optional[str] = None,
        evaluator_type: Optional[str] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple test cases in batch.
        
        Args:
            agent_responses: Dictionary mapping test_id to agent response
            extracted_memories: Optional dictionary mapping test_id to extracted memory
            category: Optional filter by category
            evaluator_type: Optional evaluator type
            
        Returns:
            Dictionary mapping test_id to evaluation result
        """
        batch_evaluator = BatchEvaluator(evaluator_type)
        test_cases = self.list_test_cases(category)
        
        return batch_evaluator.evaluate_test_suite(
            test_cases,
            agent_responses,
            extracted_memories
        )
    
    def generate_report(
        self,
        results: Dict[str, EvaluationResult],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate evaluation report.
        
        Args:
            results: Dictionary of evaluation results
            output_file: Optional file to save report
            
        Returns:
            Report string
        """
        batch_evaluator = BatchEvaluator()
        report = batch_evaluator.generate_report(
            results,
            self.test_suite.test_cases
        )
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            console.print(f"[green]Report saved to {output_file}[/green]")
        
        return report
    
    def display_test_case_summary(self, show_full_titles: bool = True, by_category: bool = True) -> None:
        """Display a summary of all test cases.
        
        Args:
            show_full_titles: If True, show complete titles without truncation
            by_category: If True, organize display by category
        """
        if not self.test_suite:
            console.print("[red]No test cases loaded[/red]")
            return
        
        if by_category:
            # Display by category
            categories = ['layer1', 'layer2', 'layer3']
            for category in categories:
                test_cases = self.test_suite.get_by_category(category)
                if test_cases:
                    # Sort test cases by ID
                    test_cases = sorted(test_cases, key=lambda tc: tc.test_id)
                    console.print(f"\n[bold cyan]{category.upper()}: {len(test_cases)} test cases[/bold cyan]")
                    for tc in test_cases:
                        if show_full_titles:
                            console.print(f"  - {tc.test_id}: {tc.title}")
                        else:
                            title = tc.title[:60] + "..." if len(tc.title) > 60 else tc.title
                            console.print(f"  - {tc.test_id}: {title}")
        else:
            # Display as table
            table = Table(title="Test Case Summary", show_header=True)
            table.add_column("Category", style="cyan")
            table.add_column("Test ID", style="magenta")
            table.add_column("Title", style="green")
            table.add_column("Conversations", justify="center")
            table.add_column("Rounds", justify="center")
            
            # Sort test cases by ID
            sorted_test_cases = sorted(self.test_suite.test_cases, key=lambda tc: tc.test_id)
            for test_case in sorted_test_cases:
                total_rounds = sum(h.rounds for h in test_case.conversation_histories)
                title = test_case.title if show_full_titles else (test_case.title[:40] + "..." if len(test_case.title) > 40 else test_case.title)
                table.add_row(
                    test_case.category,
                    test_case.test_id,
                    title,
                    str(len(test_case.conversation_histories)),
                    str(total_rounds)
                )
            
            console.print(table)
    
    def display_test_case_detail(self, test_id: str) -> None:
        """Display detailed information about a test case."""
        test_case = self.get_test_case(test_id)
        if not test_case:
            console.print(f"[red]Test case {test_id} not found[/red]")
            return
        
        panel_content = f"""[bold cyan]Title:[/bold cyan] {test_case.title}
[bold cyan]Category:[/bold cyan] {test_case.category}
[bold cyan]Description:[/bold cyan] {test_case.description}

[bold yellow]User Question:[/bold yellow]
{test_case.user_question}"""

        if test_case.expected_behavior:
            panel_content += f"""

[bold yellow]Expected Behavior:[/bold yellow]
{test_case.expected_behavior}"""
        
        panel_content += f"""

[bold yellow]Evaluation Criteria:[/bold yellow]
{test_case.evaluation_criteria}

[bold cyan]Conversation Histories:[/bold cyan]
  Count: {len(test_case.conversation_histories)}
  Total Rounds: {sum(h.rounds for h in test_case.conversation_histories)}
"""
        
        console.print(Panel(panel_content, title=f"Test Case: {test_id}", expand=False))


class TestCaseExporter:
    """Export test cases to different formats."""
    
    @staticmethod
    def export_to_json(test_cases: List[TestCase], output_file: str) -> None:
        """Export test cases to JSON format."""
        import json
        data = []
        for tc in test_cases:
            tc_dict = tc.model_dump()
            # Convert message objects to dicts
            for hist in tc_dict['conversation_histories']:
                hist['messages'] = [
                    {'role': msg['role'], 'content': msg['content']}
                    for msg in hist['messages']
                ]
            data.append(tc_dict)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_to_markdown(test_cases: List[TestCase], output_file: str) -> None:
        """Export test cases to Markdown format."""
        content = "# User Memory Evaluation Test Cases\n\n"
        
        for category in ["layer1", "layer2", "layer3"]:
            category_cases = [tc for tc in test_cases if tc.category == category]
            if not category_cases:
                continue
            
            # Sort by test_id for consistent ordering
            category_cases = sorted(category_cases, key=lambda tc: tc.test_id)
            
            content += f"## {category.upper()}\n\n"
            for tc in category_cases:
                content += f"### {tc.test_id}: {tc.title}\n\n"
                content += f"**Description:** {tc.description}\n\n"
                content += f"**User Question:** {tc.user_question}\n\n"
                if tc.expected_behavior:
                    content += f"**Expected Behavior:** {tc.expected_behavior}\n\n"
                content += f"**Conversations:** {len(tc.conversation_histories)} "
                content += f"(Total {sum(h.rounds for h in tc.conversation_histories)} rounds)\n\n"
                content += "---\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
