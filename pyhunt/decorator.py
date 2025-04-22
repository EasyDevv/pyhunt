import functools
import inspect
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Callable, List, Optional, Type, Union

from pyhunt.config import LOG_LEVEL, ROOT_DIR
from pyhunt.context import call_depth, current_function_context
from pyhunt.helpers import format_call_args
from pyhunt.logger import log_entry, log_error, log_exit, warning
from pyhunt.utils import extract_first_traceback


def trace(
    _obj: Optional[Union[Callable, Type]] = None,
    *,
    include_init: bool = False,
    exclude_methods: Optional[List[str]] = None,
) -> Union[Callable, Type]:
    """
    Decorator to trace function or class method calls.

    Args:
        _obj: Function or class to decorate.
        include_init: If True, trace __init__ method (class decorator only).
        exclude_methods: List of method names to exclude (class decorator only).

    Returns:
        Decorated function or class.
    """
    exclude = exclude_methods or []

    def decorator(obj: Union[Callable, Type]) -> Union[Callable, Type]:
        # Disable tracing if global LOG_LEVEL is higher than debug
        if LOG_LEVEL != 10:
            return obj
        if isinstance(obj, type):
            # --- Class Decorator Logic (unchanged) ---
            cls = obj
            current_exclude = list(exclude)
            if not include_init:
                current_exclude.append("__init__")

            methods_to_trace = {}
            for base_cls in reversed(cls.__mro__):
                if base_cls is object:
                    continue
                for name, method in base_cls.__dict__.items():
                    if name in current_exclude:
                        continue
                    is_special = name.startswith("__") and name.endswith("__")
                    if is_special and name != "__init__":
                        continue
                    if name.startswith("_") and not is_special:
                        continue
                    if callable(method):
                        if name in methods_to_trace:
                            continue
                        if inspect.isfunction(method) or inspect.iscoroutinefunction(
                            method
                        ):
                            if name == "__init__" and include_init:
                                methods_to_trace[name] = method
                            elif name != "__init__":
                                methods_to_trace[name] = method

            for name, method in methods_to_trace.items():
                try:
                    # Use the new _wrap_function which returns the appropriate wrapper
                    traced_method = _wrap_function(method)
                    setattr(cls, name, traced_method)
                except Exception as e:
                    warning(
                        None, f"Failed to apply trace to {cls.__name__}.{name}: {e}"
                    )
            return cls
            # --- End Class Decorator Logic ---

        elif callable(obj):
            # Apply wrapper to a single function
            return _wrap_function(obj)

        else:
            warning(
                None,
                f"Trace decorator applied to non-callable, non-class object: {type(obj)}",
            )
            return obj

    def _wrap_function(func: Callable) -> Callable:
        func_name = func.__name__
        is_async = inspect.iscoroutinefunction(func)

        class_name: Optional[str] = None
        try:
            qualname_parts = func.__qualname__.split(".")
            if len(qualname_parts) > 1:
                class_name = qualname_parts[-2]
        except AttributeError:
            pass

        # _invoke sets up context, calls original func, logs entry/error
        # It returns the result (for sync) or awaitable (for async)
        # It raises exceptions upward without filtering traceback
        def _invoke(is_async_func_flag, *args, **kwargs):
            parent_ctx = current_function_context.get()
            current_ctx_name = f"{class_name}.{func_name}" if class_name else func_name
            full_ctx = (
                f"{parent_ctx} -> {current_ctx_name}"
                if parent_ctx
                else current_ctx_name
            )
            token_ctx = current_function_context.set(full_ctx)

            parent_depth = call_depth.get()
            current_depth = parent_depth + 1
            token_depth = call_depth.set(current_depth)

            start = time.perf_counter()  # Start time needed for error logging
            call_args = {}

            try:
                call_args = format_call_args(func, args, kwargs)

                # Location of the function
                try:
                    filename = inspect.getfile(func)
                    lines, lineno = inspect.getsourcelines(func)

                    p = Path(filename)
                    path_prefix = (
                        p.name
                        if p.parent == Path(ROOT_DIR)
                        else f"{p.parent.name}/{p.name}"
                    )
                    line_offset = (
                        0 if class_name is not None else 1
                    )  # For class methods, do not add 1
                    location = f"{path_prefix}:{lineno + line_offset}"
                except (TypeError, OSError):
                    location = f"{p.parent.name}/{p.name}:{lineno}"

                log_entry(
                    func_name,
                    class_name,
                    is_async_func_flag,
                    call_args,
                    location,
                    current_depth,
                )

                if is_async_func_flag:
                    result = func(*args, **kwargs)  # Get the awaitable
                    if not inspect.isawaitable(result):
                        raise TypeError(
                            f"Expected awaitable from async func {func_name}, got {type(result)}"
                        )
                    # For async, return tokens for context reset
                    return result, token_ctx, token_depth
                else:
                    result = func(*args, **kwargs)  # Execute sync func
                    return result

            except Exception as e:
                elapsed = time.perf_counter() - start
                if (
                    not call_args
                ):  # Ensure args are captured even if formatting failed earlier
                    try:
                        call_args = format_call_args(func, args, kwargs)
                    except Exception:
                        call_args = {
                            "args": repr(args),
                            "kwargs": repr(kwargs),
                            "error": "Failed to format arguments",
                        }

                # Error traceback location
                tb = e.__traceback__
                extracted_tb = traceback.extract_tb(tb)
                if extracted_tb:
                    last_frame = extracted_tb[-1]
                    try:
                        p = Path(last_frame.filename)
                        if p.parent == Path(ROOT_DIR):
                            location = f"{p.name}:{last_frame.lineno}"
                        else:
                            location = f"{p.parent.name}/{p.name}:{last_frame.lineno}"
                    except Exception:
                        location = f"{last_frame.filename}:{last_frame.lineno}"

                log_error(
                    func_name,
                    class_name,
                    is_async_func_flag,
                    elapsed,
                    e,
                    call_args,
                    location,
                    current_depth,
                )
                # Re-raise without filtering here
                raise e
            finally:
                # Only reset context for sync functions here
                if not is_async_func_flag:
                    call_depth.reset(token_depth)
                    current_function_context.reset(token_ctx)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            parent_depth = call_depth.get()  # Need depth for exit log
            current_depth = parent_depth + 1
            # Prepare for context reset after await
            token_ctx = None
            token_depth = None
            try:
                # _invoke returns (awaitable, token_ctx, token_depth)
                awaitable, token_ctx, token_depth = _invoke(True, *args, **kwargs)
                result = await awaitable
                # Log exit after successful await
                elapsed = time.perf_counter() - start_time
                log_exit(
                    func_name,
                    class_name,
                    True,  # is_async
                    elapsed,
                    current_depth,
                )
                return result
            except Exception as e:
                full_tb_str = "".join(traceback.format_exception(e))
                first_tb_str = extract_first_traceback(full_tb_str)

                os.write(1, first_tb_str.encode())
                sys.exit(1)
            finally:
                # Reset context after await completes
                if token_ctx is not None and token_depth is not None:
                    call_depth.reset(token_depth)
                    current_function_context.reset(token_ctx)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            parent_depth = call_depth.get()  # Need depth for exit log
            current_depth = parent_depth + 1
            try:
                # _invoke executes the function and returns result
                result = _invoke(False, *args, **kwargs)
                # Log exit after successful execution
                elapsed = time.perf_counter() - start_time
                log_exit(
                    func_name,
                    class_name,
                    False,  # is_async
                    elapsed,
                    current_depth,
                )
                return result
            except Exception as e:
                full_tb_str = "".join(traceback.format_exception(e))
                first_tb_str = extract_first_traceback(full_tb_str)

                os.write(1, first_tb_str.encode())
                sys.exit(1)

        return async_wrapper if is_async else wrapper

    # Entry point for the decorator
    if _obj is None:
        # Called as @trace() or @trace(...)
        return decorator
    else:
        # Called as @trace
        return decorator(_obj)
