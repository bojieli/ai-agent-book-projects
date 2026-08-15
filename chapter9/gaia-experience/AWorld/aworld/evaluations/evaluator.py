# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from aworld.config.conf import EvaluationConfig
from aworld.core.context.base import Context


class EvaluationCriteria:
    pass


@dataclass
class EvaluationResult:
    task_id: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.
    passed: bool = False
    error_message: Optional[str] = None


class Evaluator:
    __metaclass__ = abc.ABCMeta

    def __init__(self,
                 conf: EvaluationConfig,
                 dataset: object = None,
                 file_path: str = None,
                 context: Context = None,
                 results: List[str] = None,
                 ground_truth: List[str] = None):
        self.conf = conf
        self.context = context
        self.dataset = dataset
        self.file_path = file_path
        self.results = results
        self.ground_truth = ground_truth

        self.eval_results = None

    @abc.abstractmethod
    async def run(self):
        """The evaluation complete pipeline."""

    async def evaluate(self) -> EvaluationResult:
        """Evaluate the dataset/task.

        Returns:
            EvaluationResult
        """
        await self.pre_evaluate()
        results = await self.do_evaluate()
        return await self.post_evaluate(results)

    @abc.abstractmethod
    async def do_evaluate(self) -> EvaluationResult:
        """Implement specific evaluation process."""

    async def pre_evaluate(self) -> None:
        """Can be used to perform any setup before evaluation."""

    async def post_evaluate(self, evaluate_result: EvaluationResult) -> EvaluationResult:
        """Used to perform integration testing or clean up tasks after evaluation.

        Args:
            evaluate_result: The result of the evaluate dataset.
        """
        return evaluate_result
