from __future__ import annotations

import ast
import uuid
import time
from pathlib import Path
from collections import deque
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, ContextManager, cast

from aworld.trace.base import AttributeValueType
from aworld.trace.constants import ATTRIBUTES_MESSAGE_TEMPLATE_KEY

if TYPE_CHECKING:
    from .context_manager import TraceManager
    from .auto_trace import not_auto_trace


def compile_source(
        tree: ast.AST, filename: str, module_name: str, trace_manager: TraceManager, min_duration_ns: int
) -> Callable[[dict[str, Any]], None]:
    """Compile a modified AST of the module's source code in the module's namespace.

    Returns a function which accepts module globals and executes the compiled code.

    The modified AST wraps the body of every function definition in `with context_factories[index]():`.
    `context_factories` is added to the module's namespace as `aworld_<uuid>`.
    `index` is a different constant number for each function definition.
    """

    context_factories_var_name = f'aworld_{uuid.uuid4().hex}'
    # The variable name for storing context_factors in the module's namespace.

    context_factories: list[Callable[[], ContextManager[Any]]] = []
    tree = rewrite_ast(tree, filename, context_factories_var_name, module_name, trace_manager, context_factories,
                       min_duration_ns)
    assert isinstance(tree, ast.Module)  # for type checking
    # dont_inherit=True is necessary to prevent the module from inheriting the __future__ import from this module.
    code = compile(tree, filename, 'exec', dont_inherit=True)

    def execute(globs: dict[str, Any]):
        globs[context_factories_var_name] = context_factories
        exec(code, globs, globs)

    return execute


def rewrite_ast(
        tree: ast.AST,
        filename: str,
        context_factories_var_name: str,
        module_name: str,
        trace_manager: TraceManager,
        context_factories: list[Callable[[], ContextManager[Any]]],
        min_duration_ns: int,
) -> ast.AST:
    transformer = AutoTraceTransformer(
        context_factories_var_name, filename, module_name, trace_manager, context_factories, min_duration_ns
    )
    return transformer.visit(tree)


class AutoTraceTransformer(ast.NodeTransformer):
    """Trace all encountered functions except those explicitly marked with `@no_auto_trace`."""

    def __init__(
            self,
            context_factories_var_name: str,
            filename: str,
            module_name: str,
            trace_manager: TraceManager,
            context_factories: list[Callable[[], ContextManager[Any]]],
            min_duration_ns: int,
    ):
        self._context_factories_var_name = context_factories_var_name
        self._filename = filename
        self._module_name = module_name
        self._trace_manager = trace_manager
        self._context_factories = context_factories
        self._min_duration_ns = min_duration_ns
        self._qualname_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit a class definition and rewrite its methods."""

        if self.check_not_auto_trace(node):
            return node

        self._qualname_stack.append(node.name)
        node = cast(ast.ClassDef, self.generic_visit(node))
        self._qualname_stack.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Visit a function definition and rewrite it."""

        if self.check_not_auto_trace(node):
            return node

        self._qualname_stack.append(node.name)
        qualname = '.'.join(self._qualname_stack)
        self._qualname_stack.append('<locals>')
        self.generic_visit(node)
        self._qualname_stack.pop()  # <locals>
        self._qualname_stack.pop()  # node.name
        return self.rewrite_function(node, qualname)

    def check_not_auto_trace(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> bool:
        """Return true if the node has a `@not_auto_trace` decorator."""
        return any(
            (
                    isinstance(node, ast.Name)
                    and node.id == not_auto_trace.__name__
                # or (
                #     isinstance(node, ast.Attribute)
                #     and node.attr == not_auto_trace.__name__
                #     and isinstance(node.value, ast.Name)
                #     and node.value.id == xxx.__name__
                # )
            )
            for node in node.decorator_list
        )

    def rewrite_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str) -> ast.AST:
        """Rewrite a function definition to trace its execution."""

        if has_yield(node):
            return node

        body = node.body.copy()
        new_body: list[ast.stmt] = []
        if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
        ):
            new_body.append(body.pop(0))

        if not body or (
                len(body) == 1
                and (
                        isinstance(body[0], ast.Pass)
                        or (isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant))
                )
        ):
            return node

        span = ast.With(
            items=[
                ast.withitem(
                    context_expr=self.trace_context_method_call_node(node, qualname),
                )
            ],
            body=body,
            type_comment=node.type_comment,
        )
        new_body.append(span)

        return ast.fix_missing_locations(
            ast.copy_location(
                type(node)(  # type: ignore
                    name=node.name,
                    args=node.args,
                    body=new_body,
                    decorator_list=node.decorator_list,
                    returns=node.returns,
                    type_comment=node.type_comment,
                ),
                node,
            )
        )

    def trace_context_method_call_node(self, node: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str) -> ast.Call:
        """Return a method call to `context_factories[index]()`."""

        index = len(self._context_factories)
        span_factory = partial(
            self._trace_manager._create_auto_span,  # type: ignore
            *self.build_create_auto_span_args(qualname, node.lineno),
        )
        if self._min_duration_ns > 0:

            timer = time.time_ns
            min_duration = self._min_duration_ns

            # This needs to be as fast as possible since it's the cost of auto-tracing a function
            # that never actually gets instrumented because its calls are all faster than `min_duration`.
            class MeasureTime:
                __slots__ = 'start'

                def __enter__(_self):
                    _self.start = timer()

                def __exit__(_self, *_):
                    # the first call exceeding min_ruration will not be tracked, and subsequent calls will only be tracked
                    if timer() - _self.start >= min_duration:
                        self._context_factories[index] = span_factory

            self._context_factories.append(MeasureTime)
        else:
            self._context_factories.append(span_factory)

        # This node means:
        #   context_factories[index]()
        # where `context_factories` is a global variable with the name `self._context_factories_var_name`
        # pointing to the `self.context_factories` list.
        return ast.Call(
            func=ast.Subscript(
                value=ast.Name(id=self._context_factories_var_name, ctx=ast.Load()),
                slice=ast.Index(value=ast.Constant(value=index)),  # type: ignore
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[],
        )

    def build_create_auto_span_args(self, qualname: str, lineno: int) -> tuple[str, dict[str, AttributeValueType]]:
        """Build the arguments for `create_auto_span`."""

        stack_info = {
            'code.filepath': get_filepath(self._filename),
            'code.lineno': lineno,
            'code.function': qualname,
        }
        attributes: dict[str, AttributeValueType] = {**stack_info}  # type: ignore

        msg_template = f'Calling {self._module_name}.{qualname}'
        attributes[ATTRIBUTES_MESSAGE_TEMPLATE_KEY] = msg_template

        span_name = msg_template

        return span_name, attributes


def has_yield(node: ast.AST):
    """Return true if the node has a yield statement."""

    queue = deque([node])
    while queue:
        node = queue.popleft()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                queue.append(child)


def get_filepath(file: str):
    """Return a dict with the filepath attribute."""

    path = Path(file)
    if path.is_absolute():
        try:
            path = path.relative_to(Path('.').resolve())
        except ValueError:  # pragma: no cover
            # happens if filename path is not within CWD
            pass
    return str(path)
