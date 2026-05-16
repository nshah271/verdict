"""Execution tracer check.

Identifies newly added functions that are never executed during test runs.
Uses pytest's sys.settrace mechanism to track which functions actually run.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from verdict.ast_utils import get_added_functions
from verdict.diff import get_changed_files
from verdict.types import AddedFunction, Finding


class TraceCheck:
    """Check for newly added functions that are never executed during tests."""

    name = "trace"
    kind = "dynamic"

    def __init__(self, test_command: str = "pytest"):
        """Initialize the trace check.

        Args:
            test_command: Command to run tests (default: "pytest")
        """
        self.test_command = test_command

    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]:
        """Run execution tracing on added functions.

        Args:
            diff_root: Root directory of the diff (workspace root)
            added_functions: List of all added functions from the diff

        Returns:
            List of findings for functions that were never executed
        """
        # Fallback: compute added_functions if empty
        if not added_functions:
            changed_files = get_changed_files(diff_range="HEAD", repo_root=diff_root)
            added_functions = get_added_functions(changed_files, repo_root=diff_root)

        # Filter to non-test functions only
        non_test_functions = [f for f in added_functions if not f["is_test"]]

        # Early exit if no non-test functions
        if not non_test_functions:
            return []

        # Build target list with absolute paths
        targets = []
        for func in non_test_functions:
            file_path = Path(diff_root) / func["file"]
            abs_path = os.path.realpath(file_path)
            targets.append({
                "abspath": abs_path,
                "name": func["name"],
                "line": func["line"],
                "end_line": func["end_line"],
            })

        # Create temp files for communication with plugin
        targets_file = None
        output_file = None

        try:
            # Write targets to temp file
            targets_file = tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".json"
            )
            json.dump(targets, targets_file)
            targets_file.close()

            # Create output file
            output_file = tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".json"
            )
            output_file.close()

            # Run pytest with tracer plugin
            env = os.environ.copy()
            env["VERDICT_TRACE_TARGETS"] = targets_file.name
            env["VERDICT_TRACE_OUTPUT"] = output_file.name
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_OPTIONAL_LOCKS"] = "0"

            try:
                # TODO: wire self.test_command through (shlex.split, then append -p verdict._tracer_plugin)
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-p", "verdict._tracer_plugin"],
                    cwd=diff_root,
                    env=env,
                    timeout=180,
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                return [
                    {
                        "kind": "trace_not_run",
                        "file": non_test_functions[0]["file"],
                        "line": 1,
                        "message": "trace check timed out after 180 seconds",
                        "confidence": 0.0,
                    }
                ]
            except Exception as e:
                return [
                    {
                        "kind": "trace_not_run",
                        "file": non_test_functions[0]["file"],
                        "line": 1,
                        "message": f"trace check failed: {type(e).__name__}",
                        "confidence": 0.0,
                    }
                ]

            # Process results based on exit code
            if exit_code == 5:
                # No tests collected
                return [
                    {
                        "kind": "trace_not_run",
                        "file": non_test_functions[0]["file"],
                        "line": 1,
                        "message": "trace check skipped: no tests collected",
                        "confidence": 0.0,
                    }
                ]
            elif exit_code in (2, 3, 4):
                # pytest internal errors
                return [
                    {
                        "kind": "trace_not_run",
                        "file": non_test_functions[0]["file"],
                        "line": 1,
                        "message": f"trace check failed: pytest exit code {exit_code}",
                        "confidence": 0.0,
                    }
                ]
            elif exit_code in (0, 1):
                # Tests ran (0 = success, 1 = test failures)
                # Read execution results
                try:
                    with open(output_file.name, "r") as f:
                        output_data = json.load(f)
                    executed = set(
                        tuple(item) for item in output_data.get("executed", [])
                    )
                except (FileNotFoundError, json.JSONDecodeError):
                    executed = set()

                # Build set of all targets for comparison
                target_set = set()
                target_map = {}  # Map (abspath, name, line) to original function
                for func in non_test_functions:
                    file_path = Path(diff_root) / func["file"]
                    abs_path = os.path.realpath(file_path)
                    key = (abs_path, func["name"], func["line"])
                    target_set.add(key)
                    target_map[key] = func

                # Find unexecuted functions
                unexecuted = target_set - executed

                # Generate findings
                findings: list[Finding] = []
                for key in unexecuted:
                    func = target_map[key]
                    findings.append({
                        "kind": "never_executed",
                        "file": func["file"],
                        "line": func["line"],
                        "message": f"{func['name']}() defined but never called during test run",
                        "confidence": 0.85,
                    })

                return findings
            else:
                # Unexpected exit code
                return [
                    {
                        "kind": "trace_not_run",
                        "file": non_test_functions[0]["file"],
                        "line": 1,
                        "message": f"trace check failed: unexpected exit code {exit_code}",
                        "confidence": 0.0,
                    }
                ]

        finally:
            # Clean up temp files
            if targets_file:
                try:
                    os.unlink(targets_file.name)
                except OSError:
                    pass
            if output_file:
                try:
                    os.unlink(output_file.name)
                except OSError:
                    pass


# Export check instance for CLI auto-discovery
check = TraceCheck()

# Made with Bob