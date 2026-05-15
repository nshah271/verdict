"""Tests for AST analysis functionality."""

import tempfile
from pathlib import Path

from verdict.ast_utils import get_added_functions, get_added_tests
from verdict.types import ChangedFile


def test_get_added_functions_basic():
    """Test extracting added functions from a Python file."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [8, 14, 21, 48, 51, 55],  # regular_function, async_function, simple_fixture, SampleClass, __init__, method_one
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    # Convert to dict for easier lookup
    funcs_by_name = {f["name"]: f for f in added_functions}

    # Check regular function
    assert "regular_function" in funcs_by_name
    regular = funcs_by_name["regular_function"]
    assert regular["file"] == "tests/fixtures/sample_module.py"
    assert regular["line"] == 8
    assert regular["end_line"] == 10
    assert regular["is_test"] is True  # In tests/ directory
    assert regular["decorators"] == []

    # Check async function
    assert "async_function" in funcs_by_name
    async_func = funcs_by_name["async_function"]
    assert async_func["line"] == 14
    assert async_func["is_test"] is True  # In tests/ directory

    # Check function with decorator
    assert "simple_fixture" in funcs_by_name
    fixture = funcs_by_name["simple_fixture"]
    assert fixture["line"] == 21
    assert fixture["decorators"] == ["pytest.fixture"]

    # Check class
    assert "SampleClass" in funcs_by_name
    cls = funcs_by_name["SampleClass"]
    assert cls["line"] == 48
    assert cls["is_test"] is True  # In tests/ directory

    # Check method
    assert "method_one" in funcs_by_name
    method = funcs_by_name["method_one"]
    assert method["line"] == 55
    assert method["is_test"] is True  # In tests/ directory


def test_decorator_with_call_args():
    """Test that decorators with call args are extracted correctly."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [28],  # complex_fixture function def line
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}
    assert "complex_fixture" in funcs_by_name
    fixture = funcs_by_name["complex_fixture"]
    # Should extract just the decorator name, not the call args
    assert fixture["decorators"] == ["pytest.fixture"]


def test_multiple_decorators():
    """Test function with multiple decorators."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [36],  # test_with_multiple_decorators function def line
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}
    assert "test_with_multiple_decorators" in funcs_by_name
    test_func = funcs_by_name["test_with_multiple_decorators"]
    assert test_func["is_test"] is True  # name starts with test_
    assert "pytest.mark.parametrize" in test_func["decorators"]
    assert "pytest.mark.slow" in test_func["decorators"]


def test_is_test_detection_by_name():
    """Test that functions starting with test_ are marked as tests."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [42],  # test_simple_case
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}
    assert "test_simple_case" in funcs_by_name
    test_func = funcs_by_name["test_simple_case"]
    assert test_func["is_test"] is True


def test_is_test_detection_by_path():
    """Test that functions in test files are marked as tests."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",  # Contains "tests/"
        "added_lines": [91],  # helper_function (not named test_*)
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}
    assert "helper_function" in funcs_by_name
    helper = funcs_by_name["helper_function"]
    # Should be marked as test because path contains "tests/"
    assert helper["is_test"] is True


def test_class_and_methods_both_appear():
    """Test that both class and its methods appear as separate entries."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [48, 51, 55, 59],  # SampleClass, __init__, method_one, async_method
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}

    # Class should appear
    assert "SampleClass" in funcs_by_name

    # Methods should also appear as separate entries
    assert "__init__" in funcs_by_name
    assert "method_one" in funcs_by_name
    assert "async_method" in funcs_by_name


def test_async_function_detected():
    """Test that async functions are properly detected."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [14, 59, 84],  # async_function, async_method, test_async_with_decorators
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}

    # All three async functions should be detected
    assert "async_function" in funcs_by_name
    assert "async_method" in funcs_by_name
    assert "test_async_with_decorators" in funcs_by_name


def test_syntax_error_skipped():
    """Test that files with syntax errors are skipped without crashing."""
    # Create a temporary file with invalid Python syntax
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def broken_function(\n    # Missing closing paren and body\n")
        temp_path = f.name

    try:
        changed_file: ChangedFile = {
            "path": temp_path,
            "added_lines": [1],
            "removed_lines": [],
        }

        # Should not crash, just skip the file
        added_functions = get_added_functions([changed_file], repo_root=".")
        assert added_functions == []
    finally:
        Path(temp_path).unlink()


def test_non_python_file_skipped():
    """Test that non-Python files are skipped."""
    changed_file: ChangedFile = {
        "path": "README.md",
        "added_lines": [1, 2, 3],
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")
    assert added_functions == []


def test_empty_added_lines():
    """Test that files with no added lines return no functions."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [],  # No added lines
        "removed_lines": [1, 2, 3],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")
    assert added_functions == []


def test_get_added_tests_filter():
    """Test that get_added_tests correctly filters test functions."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [8, 42, 91],  # regular_function, test_simple_case, helper_function
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")
    test_functions = get_added_tests(added_functions)

    # Should only include test functions
    test_names = {f["name"] for f in test_functions}
    assert "test_simple_case" in test_names
    assert "helper_function" in test_names  # In tests/ directory
    assert "regular_function" in test_names  # Also a test because in tests/ directory


def test_nested_class():
    """Test that nested classes are detected."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [70, 73, 76],  # OuterClass, InnerClass, inner_method
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}

    # Both outer and inner classes should appear
    assert "OuterClass" in funcs_by_name
    assert "InnerClass" in funcs_by_name
    assert "inner_method" in funcs_by_name


def test_property_decorator():
    """Test that property decorators are extracted correctly."""
    changed_file: ChangedFile = {
        "path": "tests/fixtures/sample_module.py",
        "added_lines": [64],  # computed_property with @property
        "removed_lines": [],
    }

    added_functions = get_added_functions([changed_file], repo_root=".")

    funcs_by_name = {f["name"]: f for f in added_functions}
    assert "computed_property" in funcs_by_name
    prop = funcs_by_name["computed_property"]
    assert "property" in prop["decorators"]

# Made with Bob
