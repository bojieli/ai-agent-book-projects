# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from abc import ABC, abstractmethod
from typing import Any, Collection
from importlib_metadata import version, PackageNotFoundError
from aworld.logs.util import logger
from aworld.utils.import_package import import_package
import_package("packaging")  # noqa
from packaging.requirements import Requirement, InvalidRequirement


class Instrumentor(ABC):
    _instance = None
    _has_instrumented = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)

        return cls._instance

    def instrument(self, **kwargs: Any):
        """
        Instrument the library.
        """
        if self._has_instrumented:
            logger.warning(
                f"Instrumentor[{self.__class__.__name__}] has already instrumented, skip")
            return

        if not self._check_dependency_conflicts():
            return

        result = self._instrument(**kwargs)
        self._has_instrumented = True
        return result

    def uninstrument(self, **kwargs: Any):
        """
        Uninstrument the library.
        """
        if not self._has_instrumented:
            logger.warning("Instrumentor has not instrumented, skip")
            return
        self._uninstrument(**kwargs)
        self._has_instrumented = False

    @abstractmethod
    def _uninstrument(self, **kwargs: Any):
        """
        Uninstrument the library.
        """

    @abstractmethod
    def _instrument(self, **kwargs: Any):
        """
        Instrument the library.
        """

    def _check_dependency_conflicts(self):
        dependencies = self.instrumentation_dependencies()
        for dependence in dependencies:
            try:
                requirement = Requirement(dependence)
            except InvalidRequirement as exc:
                logger.warning(
                    f'error parsing dependency, reporting as a conflict: "{dependence}" - {exc}')
                return False
            try:
                dist_version = version(requirement.name)
            except PackageNotFoundError as exc:
                logger.warning(
                    f'dependency not found, reporting as a conflict: "{dependence}" - {exc}')
                return False

            if requirement.specifier and not requirement.specifier.contains(dist_version):
                logger.warning(
                    f'dependency version conflict, reporting as a conflict: requested: "{self.required}" but found: "{self.found}"')
                return False

        return True

    @abstractmethod
    def instrumentation_dependencies(self) -> Collection[str]:
        """
        Return a list of dependencies that the instrumentation requires.
        """
