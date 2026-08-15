import ast
import re
import sys
import warnings
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_loader
from types import ModuleType
from typing import TYPE_CHECKING, Sequence, Union, Callable, Iterator, TypeVar, Any, cast

from aworld.trace.base import log_trace_error
from .rewrite_ast import compile_source

if TYPE_CHECKING:
    from .context_manager import TraceManager


class AutoTraceModule:
    """A class that represents a module being imported that should maybe be traced automatically."""

    def __init__(self, module_name: str) -> None:
        self._module_name = module_name
        """Fully qualified absolute name of the module being imported."""

    def need_auto_trace(self, prefix: Union[str, Sequence[str]]) -> bool:
        """
        Check if the module name starts with the given prefix.
        """
        if isinstance(prefix, str):
            prefix = (prefix,)
        pattern = '|'.join([get_module_pattern(p) for p in prefix])
        return bool(re.match(pattern, self._module_name))


class TraceImportFinder(MetaPathFinder):
    """A class that implements the `find_spec` method of the `MetaPathFinder` protocol."""

    def __init__(self, trace_manager: "TraceManager", module_funcs: Callable[[AutoTraceModule], bool],
                 min_duration_ns: int) -> None:
        self._trace_manager = trace_manager
        self._modules_filter = module_funcs
        self._min_duration_ns = min_duration_ns

    def _find_plain_specs(
            self, fullname: str, path: Sequence[str] = None, target: ModuleType = None
    ) -> Iterator[ModuleSpec]:
        """Yield module specs returned by other finders on `sys.meta_path`."""
        for finder in sys.meta_path:
            # Skip this finder or any like it to avoid infinite recursion.
            if isinstance(finder, TraceImportFinder):
                continue

            try:
                plain_spec = finder.find_spec(fullname, path, target)
            except Exception:  # pragma: no cover
                continue

            if plain_spec:
                yield plain_spec

    def find_spec(self, fullname: str, path: Sequence[str], target=None) -> None:
        """Find the spec for the given module name."""

        for plain_spec in self._find_plain_specs(fullname, path, target):
            # Get module specs returned by other finders on `sys.meta_path`
            get_source = getattr(plain_spec.loader, 'get_source', None)
            if not callable(get_source):
                continue
            try:
                source = cast(str, get_source(fullname))
            except Exception:
                continue

            if not source:
                continue

            filename = plain_spec.origin
            if not filename:
                try:
                    filename = cast('str | None', plain_spec.loader.get_filename(fullname))
                except Exception:
                    pass
            filename = filename or f'<{fullname}>'

            if not self._modules_filter(AutoTraceModule(fullname)):
                return None

            try:
                tree = ast.parse(source)
            except Exception:
                # Invalid source code. Try another one.
                continue

            try:
                execute = compile_source(tree, filename, fullname, self._trace_manager, self._min_duration_ns)
            except Exception:  # pragma: no cover
                log_trace_error()
                return None

            loader = AutoTraceLoader(plain_spec, execute)
            return spec_from_loader(fullname, loader)


class AutoTraceLoader(Loader):
    """
    A class that implements the `exec_module` method of the `Loader` protocol.
    """

    def __init__(self, plain_spec: ModuleSpec, execute: Callable[[dict[str, Any]], None]) -> None:
        self._plain_spec = plain_spec
        self._execute = execute

    def exec_module(self, module: ModuleType):
        """Execute a modified AST of the module's source code in the module's namespace.
        """
        self._execute(module.__dict__)

    def create_module(self, spec: ModuleSpec):
        return None

    def get_code(self, _name: str):
        """`python -m` uses the `runpy` module which calls this method instead of going through the normal protocol.
        So return some code which can be executed with the module namespace.
        Here `__loader__` will be this object, i.e. `self`.
        source = '__loader__.execute(globals())'
        return compile(source, '<string>', 'exec', dont_inherit=True)
        """

    def __getattr__(self, item: str):
        """Forward some methods to the plain spec's loader (likely a `SourceFileLoader`) if they exist."""
        if item in {'get_filename', 'is_package'}:
            return getattr(self.plain_spec.loader, item)
        raise AttributeError(item)


def convert_to_modules_func(modules: Sequence[str]) -> Callable[[AutoTraceModule], bool]:
    """Convert a sequence of module names to a function that checks if a module name starts with any of the given module names.
    """
    return lambda module: module.need_auto_trace(modules)


def get_module_pattern(module: str):
    """
    Get the regex pattern for the given module name.
    """

    if not re.match(r'[\w.]+$', module, re.UNICODE):
        return module
    module = re.escape(module)
    return rf'{module}($|\.)'


def install_auto_tracing(trace_manager: "TraceManager",
                         modules: Union[Sequence[str],
                         Callable[[AutoTraceModule], bool]],
                         min_duration_seconds: float
                         ) -> None:
    """
    Automatically trace the execution of a function.
    """
    if isinstance(modules, Sequence):
        module_funcs = convert_to_modules_func(modules)
    else:
        module_funcs = modules

    if not callable(module_funcs):
        raise TypeError('modules must be a list of strings or a callable')

    for module in list(sys.modules.values()):
        try:
            auto_trace_module = AutoTraceModule(module.__name__)
        except Exception:
            continue

        if module_funcs(auto_trace_module):
            warnings.warn(f'The module {module.__name__!r} matches modules to trace, but it has already been imported. '
                          f'Call `auto_tracing` earlier',
                          stacklevel=2,
                          )

    min_duration_ns = int(min_duration_seconds * 1_000_000_000)
    trace_manager = trace_manager.new_manager('auto_tracing')
    finder = TraceImportFinder(trace_manager, module_funcs, min_duration_ns)
    sys.meta_path.insert(0, finder)


T = TypeVar('T')


def not_auto_trace(x: T) -> T:
    """Decorator to prevent a function/class from being traced by `auto_tracing`"""
    return x
