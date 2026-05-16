"""Pytest plugin for tracing function execution.

This plugin is loaded by the trace check to monitor which functions are called
during test execution. It uses sys.settrace to track function calls and reports
back which target functions were executed.

Environment variables:
    VERDICT_TRACE_TARGETS: Path to JSON file with target functions
    VERDICT_TRACE_OUTPUT: Path to JSON file for writing execution results
"""

import json
import os
import sys
import threading
from typing import Any

# Module-level state
_targets: dict[str, list[tuple[str, int, int]]] = {}
_hits: set[tuple[str, str, int]] = set()
_output_path: str | None = None
_realpath_cache: dict[str, str] = {}


def pytest_configure(config: Any) -> None:
    """Load target functions and initialize tracing state.

    Args:
        config: pytest config object
    """
    global _targets, _hits, _output_path, _realpath_cache

    # Check for required environment variables
    targets_path = os.environ.get("VERDICT_TRACE_TARGETS")
    output_path = os.environ.get("VERDICT_TRACE_OUTPUT")

    # If either is missing, plugin is a silent no-op
    if not targets_path or not output_path:
        return

    _output_path = output_path

    # Load targets from JSON file
    try:
        with open(targets_path, "r") as f:
            targets_list = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    # Build targets dict keyed by absolute path
    _targets = {}
    for target in targets_list:
        abspath = target["abspath"]
        if abspath not in _targets:
            _targets[abspath] = []
        _targets[abspath].append(
            (target["name"], target["line"], target["end_line"])
        )

    # Initialize empty hits set and realpath cache
    _hits = set()
    _realpath_cache = {}


def pytest_sessionstart(session: Any) -> None:
    """Install trace function at session start.

    Args:
        session: pytest session object
    """
    # Only install tracer if we have targets
    if _targets:
        sys.settrace(_trace)
        threading.settrace(_trace)


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Write execution results and remove trace function.

    Args:
        session: pytest session object
        exitstatus: pytest exit status
    """
    # Remove tracer
    sys.settrace(None)

    # Write results if we have an output path
    if _output_path and _targets:
        try:
            # Convert hits set to list of lists for JSON serialization
            executed = [list(hit) for hit in _hits]
            with open(_output_path, "w") as f:
                json.dump({"executed": executed}, f)
        except OSError:
            pass


def _trace(frame: Any, event: str, arg: Any) -> Any:
    """Trace function to track function calls.

    Args:
        frame: Current stack frame
        event: Event type (call, line, return, etc.)
        arg: Event-specific argument

    Returns:
        The trace function itself to continue tracing
    """
    # Only process call events
    if event != "call":
        return _trace

    # Get code object
    co = frame.f_code

    # Resolve filename to absolute path with caching
    filename = co.co_filename
    if filename not in _realpath_cache:
        _realpath_cache[filename] = os.path.realpath(filename)
    abspath = _realpath_cache[filename]

    # Check if this file has any targets
    if abspath not in _targets:
        return _trace

    # Check if this function matches any target
    func_name = co.co_name
    func_line = co.co_firstlineno

    for target_name, target_line, target_end_line in _targets[abspath]:
        if func_name == target_name and target_line <= func_line <= target_end_line:
            _hits.add((abspath, func_name, target_line))
            break

    return _trace


# Made with Bob