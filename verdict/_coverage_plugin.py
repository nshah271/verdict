"""Pytest plugin for line-level coverage tracking.

This plugin is loaded by the coverage_delta check to monitor which specific lines
are executed during test execution. It uses sys.settrace to track line-level hits
on target lines and reports back which lines were actually executed.

Environment variables:
    VERDICT_COVERAGE_TARGETS: Path to JSON file with target lines per file
    VERDICT_COVERAGE_OUTPUT: Path to JSON file for writing coverage results
"""

import json
import os
import sys
import threading
from typing import Any

# Module-level state
_targets: dict[str, set[int]] = {}
_hits: set[tuple[str, int]] = set()
_output_path: str | None = None
_realpath_cache: dict[str, str] = {}


def pytest_configure(config: Any) -> None:
    """Load target lines and initialize coverage tracking state.

    Args:
        config: pytest config object
    """
    global _targets, _hits, _output_path, _realpath_cache

    # Check for required environment variables
    targets_path = os.environ.get("VERDICT_COVERAGE_TARGETS")
    output_path = os.environ.get("VERDICT_COVERAGE_OUTPUT")

    # If either is missing, plugin is a silent no-op
    if not targets_path or not output_path:
        return

    _output_path = output_path

    # Load targets from JSON file
    try:
        with open(targets_path, "r") as f:
            targets_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    # Build targets dict keyed by absolute path with set of line numbers
    _targets = {k: set(v) for k, v in targets_data.get("files", {}).items()}

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
    """Write coverage results and remove trace function.

    Args:
        session: pytest session object
        exitstatus: pytest exit status
    """
    # Remove tracer
    sys.settrace(None)

    # Write results if we have an output path
    if _output_path and _targets:
        try:
            # Convert hits set to dict of lists for JSON serialization
            hits_dict: dict[str, list[int]] = {}
            for abspath, line_num in _hits:
                if abspath not in hits_dict:
                    hits_dict[abspath] = []
                hits_dict[abspath].append(line_num)
            
            # Sort line numbers for consistent output
            for abspath in hits_dict:
                hits_dict[abspath].sort()
            
            with open(_output_path, "w") as f:
                json.dump({"hits": hits_dict}, f)
        except OSError:
            pass


def _trace(frame: Any, event: str, arg: Any) -> Any:
    """Trace function to track line execution.

    Args:
        frame: Current stack frame
        event: Event type (call, line, return, etc.)
        arg: Event-specific argument

    Returns:
        The trace function itself to continue tracing
    """
    # Process both call and line events
    if event not in ("call", "line"):
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

    # For line events, check if the current line is a target
    if event == "line":
        line_num = frame.f_lineno
        if line_num in _targets[abspath]:
            _hits.add((abspath, line_num))

    return _trace


# Made with Bob