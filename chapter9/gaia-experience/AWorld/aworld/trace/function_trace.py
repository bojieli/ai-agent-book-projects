import inspect
import contextlib
import functools
import json
from typing import TYPE_CHECKING, Callable, Any, Union, Iterable, Sequence
from aworld.trace.base import (
    AttributeValueType
)

from aworld.trace.stack_info import get_filepath_attribute
from aworld.trace.constants import (
    ATTRIBUTES_MESSAGE_TEMPLATE_KEY
)
from aworld.utils.serialized_util import to_serializable

if TYPE_CHECKING:
    from aworld.trace.context_manager import TraceManager, ContextSpan


def trace_func(trace_manager: "TraceManager",
               msg_template: str = None,
               attributes: dict[str, AttributeValueType] = None,
               span_name: str = None,
               extract_args: Union[bool, Iterable[str]] = False):
    """A decorator that traces the execution of a function.

    Args:
        trace_manager: The trace manager to use.
        msg_template: The message template to use.
        attributes: The attributes to use.
        span_name: The span name to use.
        extract_args: Whether to extract arguments from the function call.

    Returns:
        The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        func_meta = get_function_meta(func, msg_template)
        func_meta.update(attributes or {})
        final_span_name = span_name or func_meta.get(ATTRIBUTES_MESSAGE_TEMPLATE_KEY) or func.__name__

        if inspect.isgeneratorfunction(func):
            def wrapper(*args, **kwargs):
                with open_func_span(trace_manager, func_meta, final_span_name,
                                    get_func_args(func, extract_args, *args, **kwargs)):
                    for item in func(*args, **kwargs):
                        yield item
        elif inspect.isasyncgenfunction(func):
            async def wrapper(*args, **kwargs):
                with open_func_span(trace_manager, func_meta, final_span_name,
                                    get_func_args(func, extract_args, *args, **kwargs)):
                    async for item in func(*args, **kwargs):
                        yield item
        elif inspect.iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                with open_func_span(trace_manager, func_meta, final_span_name,
                                    get_func_args(func, extract_args, *args, **kwargs)):
                    return await func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                with open_func_span(trace_manager, func_meta, final_span_name,
                                    get_func_args(func, extract_args, *args, **kwargs)):
                    return func(*args, **kwargs)

        wrapper = functools.wraps(func)(wrapper)  # type: ignore
        return wrapper

    return decorator


def open_func_span(trace_manager: "TraceManager",
                   func_meta: dict[str, AttributeValueType],
                   span_name: str,
                   func_args: dict[str, AttributeValueType]):
    """Open a function span.

    Args:
        func_meta: The function meta information.
        span_name: The span name.

    Returns:
        The function span.
    """
    func_meta.update(func_args)
    return trace_manager._create_auto_span(name=span_name, attributes=func_meta)


def get_func_args(func: Callable,
                  extract_args: Union[bool, Iterable[str]] = False,
                  *args,
                  **kwargs):
    """Get the arguments of a function.

    Args:
        func: The function to get the arguments of.
        extract_args: Whether to extract arguments from the function call.
        *args: The positional arguments.
        **kwargs: The keyword arguments.

    Returns:
        The arguments of the function.
    """
    func_sig = inspect.signature(func)
    if func_sig.parameters:
        func_args = func_sig.bind(*args, **kwargs).arguments
        if extract_args is not False:
            if isinstance(extract_args, bool):
                extract_args = func_sig.parameters.keys()
            func_args = {k: v for k, v in func_args.items() if k in extract_args}
        pre_process_func_args(func_args)
        return func_args
    return {}


def pre_process_func_args(args: dict):
    """Pre process the function arguments.
    """
    if "self" in args:
        args.pop("self")
    for k, v in args.items():
        if (v and not isinstance(v, (str, bool, int, float)) and
                not (isinstance(v, Sequence) and all(isinstance(i, (str, bool, int, float)) for i in v))):
            args[k] = json.dumps(to_serializable(v), ensure_ascii=False)


def get_function_meta(func: Any,
                      msg_template: str = None) -> dict[str, AttributeValueType]:
    """Get the meta information of a function.\

    Args:
        func: The function to get the meta information of.
        msg_template: The message template to use.

    Returns:
        The meta information of the function.
    """
    func = inspect.unwrap(func)
    if not inspect.isfunction(func) and hasattr(func, '__call__'):
        func = func.__call__
        func = inspect.unwrap(func)

    func_name = getattr(func, '__qualname__', getattr(func, '__name__', build_func_name(func)))
    if not msg_template:
        try:
            msg_template = f'Calling {inspect.getmodule(func).__name__}.{func_name}'  # type: ignore
        except Exception:  # pragma: no cover
            msg_template = f'Calling {func_name}'
    meta: dict[str, AttributeValueType] = {
        'code.function': func_name,
        ATTRIBUTES_MESSAGE_TEMPLATE_KEY: msg_template,
    }
    with contextlib.suppress(Exception):
        meta['code.lineno'] = func.__code__.co_firstlineno
    with contextlib.suppress(Exception):
        # get code.filepath
        meta.update(get_filepath_attribute(inspect.getsourcefile(func)))

    func_sig = inspect.signature(func)
    if func_sig.parameters:
        meta['func.args'] = [str(param) for param in func_sig.parameters.values()
                             if param.name != 'self']
    return meta


def build_func_name(func: Any) -> str:
    """Build the function name.

    Args:
        func: The function to build the name of.

    Returns:
        The function name.
    """
    try:
        result = repr(func)
    except Exception:
        result = f'<{type(func).__name__} object>'

    return result
