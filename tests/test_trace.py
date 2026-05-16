"""Tests for the trace check (execution tracer).

Covers all scenarios: unexecuted functions, all executed, no non-test functions,
fallback to diff parsing, no tests collected, subprocess timeout, pytest failures,
and plugin behavior without environment variables.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from verdict.checks.trace import TraceCheck, check
from verdict.types import AddedFunction


def _added_func(
    file: str,
    name: str,
    line: int,
    end_line: int | None = None,
    is_test: bool = False,
) -> AddedFunction:
    """Helper to create AddedFunction dict."""
    return {
        "file": file,
        "name": name,
        "line": line,
        "end_line": end_line if end_line is not None else line + 5,
        "is_test": is_test,
        "decorators": [],
    }


def _write_file(tmp_path: Path, relative_path: str, content: str) -> Path:
    """Helper to write a file in a temp directory."""
    file_path = tmp_path / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return file_path


def test_module_exports_check_instance():
    """Verify module exports check instance with correct metadata."""
    assert isinstance(check, TraceCheck)
    assert check.name == "trace"
    assert check.kind == "dynamic"


def test_emits_finding_for_unexecuted_function(tmp_path):
    """Test that unexecuted functions are detected."""
    # Create a module with two functions
    _write_file(
        tmp_path,
        "mymod.py",
        """
def used_function():
    return 42

def unused_function():
    return 99
""",
    )

    # Create a test that only calls one function
    _write_file(
        tmp_path,
        "test_mymod.py",
        """
from mymod import used_function

def test_something():
    assert used_function() == 42
""",
    )

    # Run the check
    added_functions = [
        _added_func("mymod.py", "used_function", 2, 3, is_test=False),
        _added_func("mymod.py", "unused_function", 5, 6, is_test=False),
    ]

    checker = TraceCheck()
    findings = checker.run(str(tmp_path), added_functions)

    # Should have exactly one finding for the unused function
    assert len(findings) == 1
    assert findings[0]["kind"] == "never_executed"
    assert findings[0]["file"] == "mymod.py"
    assert findings[0]["line"] == 5
    assert "unused_function" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.85


def test_returns_empty_when_all_executed(tmp_path):
    """Test that no findings are returned when all functions are executed."""
    # Create a module with one function
    _write_file(
        tmp_path,
        "mymod.py",
        """
def my_function():
    return 42
""",
    )

    # Create a test that calls the function
    _write_file(
        tmp_path,
        "test_mymod.py",
        """
from mymod import my_function

def test_something():
    assert my_function() == 42
""",
    )

    # Run the check
    added_functions = [
        _added_func("mymod.py", "my_function", 2, 3, is_test=False),
    ]

    checker = TraceCheck()
    findings = checker.run(str(tmp_path), added_functions)

    # Should have no findings
    assert findings == []


def test_returns_empty_when_no_non_test_functions(tmp_path):
    """Test that no subprocess is spawned when all functions are tests."""
    # Monkeypatch subprocess.run to fail if called
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = AssertionError("subprocess.run should not be called")

        # All functions are tests
        added_functions = [
            _added_func("test_mymod.py", "test_something", 1, 3, is_test=True),
            _added_func("test_mymod.py", "test_another", 5, 7, is_test=True),
        ]

        checker = TraceCheck()
        findings = checker.run(str(tmp_path), added_functions)

        # Should return empty without calling subprocess
        assert findings == []
        mock_run.assert_not_called()


def test_falls_back_to_diff_when_empty_added_functions(tmp_path):
    """Test fallback to diff parsing when added_functions is empty."""
    # Create a simple module
    _write_file(
        tmp_path,
        "mymod.py",
        """
def my_function():
    return 42
""",
    )

    # Create a test
    _write_file(
        tmp_path,
        "test_mymod.py",
        """
from mymod import my_function

def test_something():
    assert my_function() == 42
""",
    )

    # Mock the diff and ast_utils functions
    mock_changed_files = [
        {
            "path": "mymod.py",
            "added_lines": [2, 3],
            "removed_lines": [],
        }
    ]
    mock_added_functions = [
        _added_func("mymod.py", "my_function", 2, 3, is_test=False),
    ]

    with patch("verdict.checks.trace.get_changed_files") as mock_get_changed:
        with patch("verdict.checks.trace.get_added_functions") as mock_get_added:
            mock_get_changed.return_value = mock_changed_files
            mock_get_added.return_value = mock_added_functions

            checker = TraceCheck()
            findings = checker.run(str(tmp_path), [])

            # Verify fallback was called
            mock_get_changed.assert_called_once_with(
                diff_range="HEAD", repo_root=str(tmp_path)
            )
            mock_get_added.assert_called_once_with(
                mock_changed_files, repo_root=str(tmp_path)
            )

            # Should return empty (function is executed)
            assert findings == []


def test_no_tests_collected_emits_trace_not_run(tmp_path):
    """Test that exit code 5 (no tests) produces trace_not_run finding."""
    # Create a module but no tests
    _write_file(
        tmp_path,
        "mymod.py",
        """
def my_function():
    return 42
""",
    )

    # Run the check
    added_functions = [
        _added_func("mymod.py", "my_function", 2, 3, is_test=False),
    ]

    checker = TraceCheck()
    findings = checker.run(str(tmp_path), added_functions)

    # Should have one trace_not_run finding
    assert len(findings) == 1
    assert findings[0]["kind"] == "trace_not_run"
    assert findings[0]["confidence"] == 0.0
    assert "no tests collected" in findings[0]["message"]


def test_subprocess_timeout_emits_trace_not_run(tmp_path):
    """Test that subprocess timeout produces trace_not_run finding."""
    # Mock subprocess.run to raise TimeoutExpired
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=180)

        added_functions = [
            _added_func("mymod.py", "my_function", 2, 3, is_test=False),
        ]

        checker = TraceCheck()
        findings = checker.run(str(tmp_path), added_functions)

        # Should have one trace_not_run finding
        assert len(findings) == 1
        assert findings[0]["kind"] == "trace_not_run"
        assert findings[0]["confidence"] == 0.0
        assert "timed out" in findings[0]["message"]


def test_pytest_failure_still_reports_findings(tmp_path):
    """Test that pytest failures (exit 1) still report unexecuted functions."""
    # Create a module with an unused function
    _write_file(
        tmp_path,
        "mymod.py",
        """
def unused_function():
    return 42
""",
    )

    # Create a test that fails
    _write_file(
        tmp_path,
        "test_mymod.py",
        """
def test_something():
    assert False, "This test fails"
""",
    )

    # Run the check
    added_functions = [
        _added_func("mymod.py", "unused_function", 2, 3, is_test=False),
    ]

    checker = TraceCheck()
    findings = checker.run(str(tmp_path), added_functions)

    # Should still detect the unexecuted function despite test failure
    assert len(findings) == 1
    assert findings[0]["kind"] == "never_executed"
    assert findings[0]["file"] == "mymod.py"
    assert "unused_function" in findings[0]["message"]


def test_plugin_inert_without_env_vars():
    """Test that plugin is a no-op without environment variables."""
    # Import the plugin
    import verdict._tracer_plugin as plugin

    # Reset module state
    plugin._targets = {}
    plugin._hits = set()
    plugin._output_path = None
    plugin._realpath_cache = {}

    # Create a fake config
    config = MagicMock()

    # Call pytest_configure without setting env vars
    plugin.pytest_configure(config)

    # Should not raise an exception and state should remain empty
    assert plugin._targets == {}
    assert plugin._hits == set()
    assert plugin._output_path is None


def test_multiple_unexecuted_functions(tmp_path):
    """Test detection of multiple unexecuted functions."""
    # Create a module with three functions
    _write_file(
        tmp_path,
        "mymod.py",
        """
def used_function():
    return 1

def unused_function_1():
    return 2

def unused_function_2():
    return 3
""",
    )

    # Create a test that only calls one function
    _write_file(
        tmp_path,
        "test_mymod.py",
        """
from mymod import used_function

def test_something():
    assert used_function() == 1
""",
    )

    # Run the check
    added_functions = [
        _added_func("mymod.py", "used_function", 2, 3, is_test=False),
        _added_func("mymod.py", "unused_function_1", 5, 6, is_test=False),
        _added_func("mymod.py", "unused_function_2", 8, 9, is_test=False),
    ]

    checker = TraceCheck()
    findings = checker.run(str(tmp_path), added_functions)

    # Should have two findings
    assert len(findings) == 2
    finding_names = {f["message"] for f in findings}
    assert any("unused_function_1" in msg for msg in finding_names)
    assert any("unused_function_2" in msg for msg in finding_names)


def test_finding_shape_is_well_formed(tmp_path):
    """Test that findings have the correct shape."""
    # Create a module with an unused function
    _write_file(
        tmp_path,
        "mymod.py",
        """
def unused_function():
    return 42
""",
    )

    # Create an empty test file
    _write_file(tmp_path, "test_mymod.py", "")

    # Run the check
    added_functions = [
        _added_func("mymod.py", "unused_function", 2, 3, is_test=False),
    ]

    checker = TraceCheck()
    findings = checker.run(str(tmp_path), added_functions)

    # Verify finding shape
    assert len(findings) >= 1
    for finding in findings:
        assert "kind" in finding
        assert "file" in finding
        assert "line" in finding
        assert "message" in finding
        assert "confidence" in finding
        assert isinstance(finding["kind"], str)
        assert isinstance(finding["file"], str)
        assert isinstance(finding["line"], int)
        assert isinstance(finding["message"], str)
        assert isinstance(finding["confidence"], float)
        assert 0.0 <= finding["confidence"] <= 1.0


# Made with Bob