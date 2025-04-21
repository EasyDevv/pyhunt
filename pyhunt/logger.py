from typing import Any, Dict, Optional
import threading

from pyhunt.console import Console

from pyhunt.colors import build_indent, get_color
from pyhunt.config import LOG_LEVEL, LOG_LEVELS, MAX_REPEAT, ELAPSED
from pyhunt.context import call_depth
from pyhunt.helpers import pretty_json

# Initialize Rich Console
console = Console()
# --- Log suppression mechanism ---
_log_count_map = {}
_log_count_lock = threading.Lock()


def _should_suppress_log(key):
    """Returns True if the log for this key should be suppressed, False otherwise.
    If suppression is triggered, returns a tuple (suppress, show_ellipsis) where:
      - suppress: True if log should be suppressed
      - show_ellipsis: True if "... 생략 ..." should be shown (only once per key)
    """
    if MAX_REPEAT is None or MAX_REPEAT < 1:
        return False, False
    with _log_count_lock:
        count = _log_count_map.get(key, 0)
        if count < MAX_REPEAT:
            _log_count_map[key] = count + 1
            return False, False
        elif count == MAX_REPEAT:
            _log_count_map[key] = count + 1
            return True, True  # Suppress log, but show ellipsis
        else:
            return True, False  # Suppress log, no ellipsis


# --- End log suppression mechanism ---


def _format_truncation_message(event_type, depth):
    color = "#808080"
    msg = f"[{color}] ... Repeated logs have been omitted | MAX_REPEAT: {MAX_REPEAT}[/]"
    return format_with_tree_indent(msg, depth, event_type)


def should_log(level_name: str) -> bool:
    """
    Determine if a message at the given level should be logged.
    """
    level_value = LOG_LEVELS.get(level_name.lower(), 20)
    return level_value >= LOG_LEVEL


def format_with_tree_indent(message: str, depth: int, event_type: str) -> str:
    """
    Apply tree indentation and prefix symbols to a multi-line log message.

    Args:
        message: The pure log message without indentation.
        depth: The call depth for indentation.
        event_type: One of 'entry', 'exit', 'error'.

    Returns:
        The message decorated with tree indentation and symbols.
    """

    color = get_color(depth)
    indent = build_indent(depth)

    # Determine prefix symbols based on event type
    if event_type == "entry":
        first_prefix = f"{indent}[{color}]├─▶[/] "
        child_prefix = f"{indent}[{color}]│    [/] "
    elif event_type == "exit":
        first_prefix = f"{indent}[{color}]├──[/] "
        child_prefix = f"{indent}[{color}]│    [/] "
    elif event_type == "error":
        first_prefix = f"{indent}[{color}]└──[/] "
        child_prefix = f"{indent}[{color}]│    [/] "
    else:
        first_prefix = f"{indent}[{color}]│   [/] "
        child_prefix = f"{indent}[{color}]│   [/] "

    # Apply child prefix to log messages, filtering empty lines
    lines = message.splitlines()
    if not lines:
        return ""

    decorated_lines = [f"{first_prefix}{lines[0]}"]
    decorated_lines += [f"{child_prefix}{line}" for line in lines[1:]]
    return "\n".join(decorated_lines)


def log_entry(
    func_name: str,
    class_name: Optional[str],
    is_async: bool,
    call_args: Dict[str, Any],
    location: str,
    depth: int,
) -> None:
    color = get_color(depth)

    sync_async = "async " if is_async else ""
    name = f"{class_name}.{func_name}" if class_name else func_name
    depth_str = f"[{color}]{depth}[/]"
    colored_name = f"[bold {color}]{name}[/]"
    colored_location = f"[bold {color}]{location}[/]"

    # Suppression key: (event_type, func_name, class_name, location)
    suppress_key = ("entry", func_name, class_name, location)
    suppress, show_trunc = _should_suppress_log(suppress_key)
    if suppress:
        if show_trunc:
            trunc_msg = _format_truncation_message("entry", depth)
            try:
                if should_log("debug"):
                    console.print(trunc_msg)
            except Exception:
                pass
        return

    args_to_format = {k: v for k, v in call_args.items() if k != "self"}
    if not args_to_format:
        args_json_str = ""
    else:
        args_json_str = pretty_json(args_to_format, "", "", color)

    core_parts = [
        f"{depth_str} 🟢 Entry {sync_async}{colored_name} | {colored_location}",
        args_json_str,
    ]
    core_message = "\n".join(m for m in core_parts if m and m.strip())
    message = format_with_tree_indent(core_message, depth, "entry")

    try:
        if should_log("debug"):
            console.print(message)
    except Exception as e:
        console.print(f"[bold red]Error during logging for {name}: {e}[/]")


def log_exit(
    func_name: str,
    class_name: Optional[str],
    is_async: bool,
    elapsed: float,
    depth: int,
) -> None:
    color = get_color(depth)

    sync_async = "async " if is_async else ""
    name = f"{class_name}.{func_name}" if class_name else func_name
    depth_str = f"[{color}]{depth}[/]"
    colored_name = f"[{color}]{name}[/]"

    # Suppression key: (event_type, func_name, class_name)
    suppress_key = ("exit", func_name, class_name)
    suppress, _ = _should_suppress_log(suppress_key)
    if suppress:
        return

    elapsed_str = f" | {elapsed:.4f}s" if ELAPSED else ""
    core_message = f"{depth_str} 🔳 Exit {sync_async}{colored_name}{elapsed_str}"
    message = format_with_tree_indent(core_message, depth, "exit")

    try:
        if should_log("debug"):
            console.print(message)
    except Exception as e:
        console.print(f"[bold red]Error during logging for {name}: {e}[/]")


def log_error(
    func_name: str,
    class_name: Optional[str],
    is_async: bool,
    elapsed: float,
    exception: Exception,
    call_args: Dict[str, Any],
    location: str,
    depth: int,
) -> None:
    color = get_color(depth)

    sync_async = "async " if is_async else ""
    name = f"{class_name}.{func_name}" if class_name else func_name
    depth_str = f"[{color}]{depth}[/]"
    colored_name = f"[bold {color}]{name}[/]"
    colored_location = f"[bold {color}]{location}[/]"

    # Suppression key: (event_type, func_name, class_name, precise_location)
    suppress_key = ("error", func_name, class_name, location)
    suppress, show_trunc = _should_suppress_log(suppress_key)
    if suppress:
        if show_trunc:
            trunc_msg = _format_truncation_message("error", depth)
            try:
                if should_log("debug"):
                    console.print(trunc_msg)
            except Exception:
                pass
        return

    args_to_format = {k: v for k, v in call_args.items() if k != "self"}
    if not args_to_format:
        args_json_str = ""
    else:
        args_json_str = pretty_json(args_to_format, "", "", color)

    core_parts = [
        f"{depth_str} 🟥 Error {sync_async} {colored_name} | {colored_location}{f' | {elapsed:.4f}s' if ELAPSED else ''}",
        f"[bold #E32636]{type(exception).__name__}: {exception}[/]",
        args_json_str,
    ]
    core_message = "\n".join(m for m in core_parts if m and m.strip())
    message = format_with_tree_indent(core_message, depth, "error")

    try:
        if should_log("debug"):
            console.print(message)
    except Exception as e:
        console.print(f"[bold red]Error during error logging for {name}: {e}[/]")


def styled_log(level_name: str, message: str, depth: int = 0) -> None:
    color = get_color(depth)
    depth_str = f" [{color}]{depth}[/]"

    # Suppression key: (level_name, message)
    suppress_key = ("styled", level_name, message)
    suppress, show_trunc = _should_suppress_log(suppress_key)
    if suppress:
        if show_trunc:
            trunc_msg = _format_truncation_message("", depth)
            if should_log(level_name):
                console.print(trunc_msg)
        return

    if level_name.lower() in ("debug", "info"):
        label = f"[cyan]{level_name.upper()}[/cyan]"
    elif level_name.lower() == "warning":
        label = f"[yellow]{level_name.upper()}[/yellow]"
    elif level_name.lower() in ("error", "critical"):
        label = f"[bold red]{level_name.upper()}[/bold red]"
    else:
        label = level_name.upper()

    core_message = f"{depth_str} {label} {message}"
    formatted_message = format_with_tree_indent(core_message, depth, "")
    if should_log(level_name):
        console.print(formatted_message)


def debug(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("debug", message, current_depth)


def info(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("info", message, current_depth)


def warning(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("warning", message, current_depth)


def critical(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("critical", message, current_depth)
