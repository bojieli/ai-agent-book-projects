# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import importlib
import inspect
import os
import sys
import uuid

from typing import Callable, Any, get_type_hints, get_origin, get_args

from pydantic import create_model, Field, BaseModel
from pydantic.fields import FieldInfo

from aworld.core.common import ParamInfo
from aworld.core.tool.action import TOOL_ACTION
from aworld.core.tool.action_factory import ActionFactory
from aworld.core.tool.action_template import ACTION_TEMPLATE
from aworld.core.tool.base import ToolFactory
from aworld.core.tool.tool_template import TOOL_TEMPLATE
from aworld.logs.util import logger
from aworld.tools import LOCAL_TOOLS_ENV_VAR


def be_tool(
        tool_name: str = None,
        tool_desc: str = None,
        name: str = None,
        desc: str = None, **kwargs
) -> Callable[..., Any]:
    """Decorate a function to be a tool, auto register the tool and action with the parameters with the factory.

    Example:
        >>> @be_tool()
        >>> def example():
        >>>     return "example"

        # write name and description
        >>> @be_tool(name="param", desc="example param func")
        >>> def example_param(param: str):
        >>>     return param

        >>> @be_tool(tool_name='field_param_tool')
        >>> def example_param_field(param: str = Field(..., description="param")):
        >>>     return param

        >>> @be_tool(tool_name='field_param_tool')
        >>> def example_param_2(param: str = Field(..., description="param")):
        >>>     return param

    Args:
        tool_name: Optional name for the tool.
        tool_desc: Optional description for the tool.
        name: Optional name for the function.
        desc: Optional description of function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # converts python function into a tool with associated actions
        function_to_tool(
            func,
            tool_name=tool_name,
            tool_desc=tool_desc,
            name=name,
            desc=desc,
            **kwargs
        )
        return func

    return decorator


def function_to_tool(
        func: Callable[..., Any],
        tool_name: str = None,
        tool_desc: str = None,
        name: str = None,
        desc: str = None,
        **kwargs
) -> None:
    """Transform a python function into a tool, and register to the factory.

    Generates necessary code files dynamically and manages tool and action registration.

    Args：
        func: An executable function.
        tool_name: The name of the tool that is transformed by the function.
        tool_desc: The description of the tool what it can do, default the same as tool_name.
        name: Alias name of function.
        desc: The description of the function what it can do, default the same as name.
    """
    tool_name = tool_name or name or func.__name__
    action_name = name or func.__name__

    postfix = f"{uuid.uuid4().hex[0:6]}__tmp"

    with open(f"{tool_name}{postfix}_action.py", 'w') as write:
        write.writelines("".join(inspect.getsourcelines(func)[0][1:]))

    if tool_name == "<lambda>" or action_name == "<lambda>":
        raise ValueError("You must provide a name for lambda functions")

    # async func, will use AsyncTool
    is_async = inspect.iscoroutinefunction(func)

    name = action_name
    if not inspect.iscoroutinefunction(func):
        name = f"async_func({action_name})"

    # build action
    if action_name not in ActionFactory:
        func_import = func.__module__
        if func_import == '__main__':
            path = inspect.getsourcefile(func)
            package = path.replace(os.getcwd(), '').replace('.py', '')
            if package[0] == '/':
                package = package[1:]
            func_import = f"from {package} "
        else:
            func_import = f"from {func_import} "
        con = ACTION_TEMPLATE.format(name=action_name,
                                     desc=desc if desc else action_name,
                                     tool_name=tool_name,
                                     func_import=func_import,
                                     func=func.__name__,
                                     call_func=name)
        with open(f"{tool_name}{postfix}_action.py", 'a+') as write:
            write.writelines(con)
        module = importlib.import_module(f"{action_name}{postfix}_action")
        getattr(module, f"{action_name}Act")
    else:
        logger.warning(f"{action_name} already register to the tool.")
        raise ValueError(f"{action_name} already register to a tool.")

    # build params info
    parameters = func_params(func)

    module_name = f'{tool_name}'
    if module_name not in sys.modules:
        params = {}
        if parameters:
            for k, v in parameters['properties'].items():
                params[k] = ParamInfo(name=k,
                                      type=v.get('type', 'string'),
                                      required=False if v.get('default') else True,
                                      default_value=v.get('default'),
                                      desc=v.get('description', k))

        # ToolAction process
        with open(f"{module_name}{postfix}.py", 'w') as write:
            write.writelines(TOOL_ACTION.format(name=tool_name,
                                                action_name_upper=action_name.upper(),
                                                action_name=action_name,
                                                desc=desc if desc else action_name,
                                                params=params))
    else:
        logger.info(f"{module_name} already exists in modules, reuse the tool action.")

    # build tool
    if tool_name not in ToolFactory:
        con = TOOL_TEMPLATE.format(name=tool_name,
                                   desc=tool_desc if tool_desc else tool_name,
                                   action=f"{tool_name}Action",
                                   cls='AsyncTool' if is_async else 'Tool',
                                   async_flag='async ' if is_async else '',
                                   async_underline='async_' if is_async else '',
                                   await_flag='await ' if is_async else '')

        with open(f"{tool_name}{postfix}.py", 'a+') as write:
            write.writelines(con)
        importlib.import_module(f"{tool_name}{postfix}")

        # write to AWorld environ variables,
        val = os.environ.get(LOCAL_TOOLS_ENV_VAR, "")
        if val:
            val = val + ";"
        os.environ[LOCAL_TOOLS_ENV_VAR] = val + sys.modules[f"{tool_name}{postfix}_action"].__file__
        logger.debug(f'add {sys.modules[f"{tool_name}{postfix}_action"].__file__}')


def func_params(func: Callable[..., Any]):
    """Extracts parameter information from the function.

    Args:
        func: An executable function.

    Returns:
        JSON schema of the function input parameters.
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    filtered_params = []

    # The function must have a return value
    if sig.return_annotation == inspect.Parameter.empty:
        raise RuntimeError(f"{func} no return value, preferably a string.")

    for name, param in sig.parameters.items():
        filtered_params.append((name, param))

    fields: dict[str, Any] = {}
    param_descs = {}

    for name, param in filtered_params:
        ann = type_hints.get(name, param.annotation)
        default = param.default
        def_desc = None
        if hasattr(default, 'description'):
            def_desc = default.description
        field_description = param_descs.get(name, def_desc)
        
        if isinstance(default, FieldInfo):
            default = default.default

        # If there's no type hint, assume `Any`
        if ann == inspect.Parameter.empty:
            ann = Any

        # Handle different parameter kinds
        if param.kind == param.VAR_POSITIONAL:
            # e.g. *args: extend positional args
            if get_origin(ann) is tuple:
                # e.g. def foo(*args: tuple[int, ...]) -> treat as List[int]
                args_of_tuple = get_args(ann)
                if len(args_of_tuple) == 2 and args_of_tuple[1] is Ellipsis:
                    ann = list[args_of_tuple[0]]  # type: ignore
                else:
                    ann = list[Any]
            else:
                # If user wrote *args: int, treat as List[int]
                ann = list[ann]  # type: ignore

            # Default factory to empty list
            fields[name] = (
                ann,
                Field(default_factory=list, description=field_description),  # type: ignore
            )
        elif param.kind == param.VAR_KEYWORD:
            # **kwargs handling
            if get_origin(ann) is dict:
                # e.g. def foo(**kwargs: dict[str, int])
                dict_args = get_args(ann)
                if len(dict_args) == 2:
                    ann = dict[dict_args[0], dict_args[1]]  # type: ignore
                else:
                    ann = dict[str, Any]
            else:
                # e.g. def foo(**kwargs: int) -> Dict[str, int]
                ann = dict[str, ann]

            fields[name] = (
                ann,
                Field(default_factory=dict, description=field_description),  # type: ignore
            )
        else:
            if default == inspect.Parameter.empty:
                # Required field
                fields[name] = (ann, Field(..., description=field_description))
            else:
                # Parameter with a default value
                fields[name] = (ann, Field(default=default, description=field_description))

    dynamic_model = create_model(f"{func.__name__}".upper(), __base__=BaseModel, **fields)
    json_schema = dynamic_model.model_json_schema()
    logger.debug(f"{func} parameters schema: {json_schema}")
    return json_schema
