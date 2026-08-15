from importlib import import_module
from wrapt import ObjectProxy


def unwrap(obj: object, attr: str):
    """Given a function that was wrapped by wrapt.wrap_function_wrapper, unwrap it

    The object containing the function to unwrap may be passed as dotted module path string.

    Args:
        obj: Object that holds a reference to the wrapped function or dotted import path as string
        attr (str): Name of the wrapped function
    """
    if isinstance(obj, str):
        try:
            module_path, class_name = obj.rsplit(".", 1)
        except ValueError as exc:
            raise ImportError(
                f"Cannot parse '{obj}' as dotted import path"
            ) from exc
        module = import_module(module_path)
        try:
            obj = getattr(module, class_name)
        except AttributeError as exc:
            raise ImportError(
                f"Cannot import '{class_name}' from '{module}'"
            ) from exc

    func = getattr(obj, attr, None)
    if func and isinstance(func, ObjectProxy) and hasattr(func, "__wrapped__"):
        setattr(obj, attr, func.__wrapped__)
