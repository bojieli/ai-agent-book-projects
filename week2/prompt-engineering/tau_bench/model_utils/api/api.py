from __future__ import annotations

import argparse
from typing import Any, TypeVar

from pydantic import BaseModel

from tau_bench.model_utils.api._model_methods import MODEL_METHODS
from tau_bench.model_utils.api.cache import cache_call_w_dedup
from tau_bench.model_utils.api.datapoint import (
    BinaryClassifyDatapoint,
    ClassifyDatapoint,
    Datapoint,
    GenerateDatapoint,
    ParseDatapoint,
    ParseForceDatapoint,
    ScoreDatapoint,
)
from tau_bench.model_utils.api.logging import log_call
from tau_bench.model_utils.api.router import RequestRouter, default_request_router
from tau_bench.model_utils.api.sample import (
    EnsembleSamplingStrategy,
    MajoritySamplingStrategy,
    SamplingStrategy,
    get_default_sampling_strategy,
)
from tau_bench.model_utils.api.types import PartialObj
from tau_bench.model_utils.model.general_model import GeneralModel
from tau_bench.model_utils.model.model import (
    AnyModel,
    BinaryClassifyModel,
    ClassifyModel,
    GenerateModel,
    ParseForceModel,
    ParseModel,
    ScoreModel,
)

T = TypeVar("T", bound=BaseModel)


class API(object):
    wrappers_for_main_methods = [log_call, cache_call_w_dedup]

    def __init__(
        self,
        parse_models: list[ParseModel],
        generate_models: list[GenerateModel],
        parse_force_models: list[ParseForceModel],
        score_models: list[ScoreModel],
        classify_models: list[ClassifyModel],
        binary_classify_models: list[BinaryClassifyModel] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        log_file: str | None = None,
    ) -> None:
        if sampling_strategy is None:
            sampling_strategy = get_default_sampling_strategy()
        if request_router is None:
            request_router = default_request_router()
        self.sampling_strategy = sampling_strategy
        self.request_router = request_router
        self._log_file = log_file
        self.binary_classify_models = binary_classify_models
        self.classify_models = classify_models
        self.parse_models = parse_models
        self.generate_models = generate_models
        self.parse_force_models = parse_force_models
        self.score_models = score_models

        self.__init_subclass__()

        self.__init_subclass__()

    def __init_subclass__(cls):
        for method_name in MODEL_METHODS:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                for wrapper in cls.wrappers_for_main_methods:
                    method = wrapper(method)
                setattr(cls, method_name, method)

    @classmethod
    def from_general_model(
        cls,
        model: GeneralModel,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        log_file: str | None = None,
    ) -> "API":
        return cls(
            binary_classify_models=[model],
            classify_models=[model],
            parse_models=[model],
            generate_models=[model],
            parse_force_models=[model],
            score_models=[model],
            log_file=log_file,
            sampling_strategy=sampling_strategy,
            request_router=request_router,
        )

    @classmethod
    def from_general_models(
        cls,
        models: list[GeneralModel],
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        log_file: str | None = None,
    ) -> "API":
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        return cls(
            binary_classify_models=models,
            classify_models=models,
            parse_models=models,
            generate_models=models,
            parse_force_models=models,
            score_models=models,
            log_file=log_file,
            sampling_strategy=sampling_strategy,
            request_router=request_router,
        )

    def set_default_binary_classify_models(self, models: list[BinaryClassifyModel]) -> None:
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        self.binary_classify_models = models

    def set_default_classify_models(self, models: list[BinaryClassifyModel]) -> None:
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        self.classify_models = models

    def set_default_parse_models(self, models: list[ParseModel]) -> None:
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        self.parse_models = models

    def set_default_generate_models(self, models: list[GenerateModel]) -> None:
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        self.generate_models = models

    def set_default_parse_force_models(self, models: list[ParseForceModel]) -> None:
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        self.parse_force_models = models

    def set_default_score_models(self, models: list[ScoreModel]) -> None:
        if len(models) == 0:
            raise ValueError("Must provide at least one model")
        self.score_models = models

    def set_default_sampling_strategy(self, sampling_strategy: SamplingStrategy) -> None:
        self.sampling_strategy = sampling_strategy

    def set_default_request_router(self, request_router: RequestRouter) -> None:
        self.request_router = request_router

    def _run_with_sampling_strategy(
        self,
        models: list[AnyModel],
        datapoint: Datapoint,
        sampling_strategy: SamplingStrategy,
    ) -> T:
        assert len(models) > 0

        def _run_datapoint(model: AnyModel, temp: float | None = None) -> T:
            if isinstance(datapoint, ClassifyDatapoint):
                return model.classify(
                    instruction=datapoint.instruction,
                    text=datapoint.text,
                    options=datapoint.options,
                    examples=datapoint.examples,
                    temperature=temp,
                )
            elif isinstance(datapoint, BinaryClassifyDatapoint):
                return model.binary_classify(
                    instruction=datapoint.instruction,
                    text=datapoint.text,
                    examples=datapoint.examples,
                    temperature=temp,
                )
            elif isinstance(datapoint, ParseForceDatapoint):
                return model.parse_force(
                    instruction=datapoint.instruction,
                    typ=datapoint.typ,
                    text=datapoint.text,
                    examples=datapoint.examples,
                    temperature=temp,
                )
            elif isinstance(datapoint, GenerateDatapoint):
                return model.generate(
                    instruction=datapoint.instruction,
                    text=datapoint.text,
                    examples=datapoint.examples,
                    temperature=temp,
                )
            elif isinstance(datapoint, ParseDatapoint):
                return model.parse(
                    text=datapoint.text,
                    typ=datapoint.typ,
                    examples=datapoint.examples,
                    temperature=temp,
                )
            elif isinstance(datapoint, ScoreDatapoint):
                return model.score(
                    instruction=datapoint.instruction,
                    text=datapoint.text,
                    min=datapoint.min,
                    max=datapoint.max,
                    examples=datapoint.examples,
                    temperature=temp,
                )
            else:
                raise ValueError(f"Unknown datapoint type: {type(datapoint)}")

        if isinstance(sampling_strategy, EnsembleSamplingStrategy):
            return sampling_strategy.execute(
                [lambda x=model: _run_datapoint(x, 0.0) for model in models]
            )
        return sampling_strategy.execute(
            lambda: _run_datapoint(
                models[0], 0.2 if isinstance(sampling_strategy, MajoritySamplingStrategy) else None
            )
        )

    def _api_call(
        self, models: list[AnyModel], datapoint: Datapoint, sampling_strategy: SamplingStrategy
    ) -> T:
        if isinstance(sampling_strategy, EnsembleSamplingStrategy):
            return self._run_with_sampling_strategy(models, datapoint, sampling_strategy)
        model = self.request_router.route(dp=datapoint, available_models=models)
        return self._run_with_sampling_strategy(
            models=[model], datapoint=datapoint, sampling_strategy=sampling_strategy
        )

    def classify(
        self,
        instruction: str,
        text: str,
        options: list[str],
        examples: list[ClassifyDatapoint] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        models: list[ClassifyModel] | None = None,
    ) -> int:
        if models is None:
            models = self.classify_models
        if sampling_strategy is None:
            sampling_strategy = self.sampling_strategy
        if request_router is None:
            request_router = self.request_router

        return self._api_call(
            models=models,
            datapoint=ClassifyDatapoint(
                instruction=instruction, text=text, options=options, examples=examples
            ),
            sampling_strategy=sampling_strategy,
        )

    def binary_classify(
        self,
        instruction: str,
        text: str,
        examples: list[BinaryClassifyDatapoint] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        models: list[BinaryClassifyModel] | None = None,
    ) -> bool:
        if models is None:
            models = (
                self.binary_classify_models
                if self.binary_classify_models is not None
                else self.classify_models
            )
        if sampling_strategy is None:
            sampling_strategy = self.sampling_strategy
        if request_router is None:
            request_router = self.request_router

        return self._api_call(
            models=models,
            datapoint=BinaryClassifyDatapoint(
                instruction=instruction, text=text, examples=examples
            ),
            sampling_strategy=sampling_strategy,
        )

    def parse(
        self,
        text: str,
        typ: type[T] | dict[str, Any],
        examples: list[ParseDatapoint] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        models: list[ParseModel] | None = None,
    ) -> T | PartialObj | dict[str, Any]:
        if models is None:
            models = self.parse_models
        if sampling_strategy is None:
            sampling_strategy = self.sampling_strategy
        if request_router is None:
            request_router = self.request_router

        return self._api_call(
            models=models,
            datapoint=ParseDatapoint(text=text, typ=typ, examples=examples),
            sampling_strategy=sampling_strategy,
        )

    def generate(
        self,
        instruction: str,
        text: str,
        examples: list[GenerateDatapoint] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        models: list[GenerateModel] | None = None,
    ) -> str:
        if models is None:
            models = self.generate_models
        if sampling_strategy is None:
            sampling_strategy = self.sampling_strategy
        if request_router is None:
            request_router = self.request_router

        return self._api_call(
            models=models,
            datapoint=GenerateDatapoint(instruction=instruction, text=text, examples=examples),
            sampling_strategy=sampling_strategy,
        )

    def parse_force(
        self,
        instruction: str,
        typ: type[T] | dict[str, Any],
        text: str | None = None,
        examples: list[ParseForceDatapoint] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        models: list[ParseForceModel] | None = None,
    ) -> T | dict[str, Any]:
        if models is None:
            models = self.parse_force_models
        if sampling_strategy is None:
            sampling_strategy = self.sampling_strategy
        if request_router is None:
            request_router = self.request_router

        return self._api_call(
            models=models,
            datapoint=ParseForceDatapoint(
                instruction=instruction, typ=typ, text=text, examples=examples
            ),
            sampling_strategy=sampling_strategy,
        )

    def score(
        self,
        instruction: str,
        text: str,
        min: int,
        max: int,
        examples: list[ScoreDatapoint] | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        request_router: RequestRouter | None = None,
        models: list[ScoreModel] | None = None,
    ) -> int:
        if models is None:
            models = self.score_models
        if sampling_strategy is None:
            sampling_strategy = self.sampling_strategy
        if request_router is None:
            request_router = self.request_router

        return self._api_call(
            models=models,
            datapoint=ScoreDatapoint(
                instruction=instruction, text=text, min=min, max=max, examples=examples
            ),
            sampling_strategy=sampling_strategy,
        )


def default_api(
    log_file: str | None = None,
    sampling_strategy: SamplingStrategy | None = None,
    request_router: RequestRouter | None = None,
) -> API:
    from tau_bench.model_utils.model.general_model import default_model

    model = default_model()
    return API(
        binary_classify_models=[model],
        classify_models=[model],
        parse_models=[model],
        generate_models=[model],
        parse_force_models=[model],
        score_models=[model],
        sampling_strategy=sampling_strategy,
        request_router=request_router,
        log_file=log_file,
    )

def default_api_from_args(args: argparse.Namespace) -> API:
    from tau_bench.model_utils.model.general_model import model_factory
    model = model_factory(model_id=args.model, platform=args.platform, base_url=args.base_url)
    return API.from_general_model(model=model)


def default_quick_api(
    log_file: str | None = None,
    sampling_strategy: SamplingStrategy | None = None,
    request_router: RequestRouter | None = None,
) -> API:
    from tau_bench.model_utils.model.general_model import default_quick_model

    model = default_quick_model()
    return API(
        binary_classify_models=[model],
        classify_models=[model],
        parse_models=[model],
        generate_models=[model],
        parse_force_models=[model],
        score_models=[model],
        sampling_strategy=sampling_strategy,
        request_router=request_router,
        log_file=log_file,
    )
