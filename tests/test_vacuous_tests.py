"""Tests for the vacuous_tests check (Alexie's P0.3 work).

Covers each of the four heuristics (empty body, no assertions, mock-only,
doesn't reach new code) plus edge cases (non-test functions skipped,
SyntaxError tolerated, missing file tolerated, contract metadata).
"""

from pathlib import Path

from verdict.checks.vacuous_tests import VacuousTestCheck, check
from verdict.types import AddedFunction


def _added_func(
    file: str,
    name: str,
    line: int,
    end_line: int | None = None,
    is_test: bool = True,
) -> AddedFunction:
    return {
        "file": file,
        "name": name,
        "line": line,
        "end_line": end_line if end_line is not None else line + 5,
        "is_test": is_test,
        "decorators": [],
    }


def _write(tmp_path: Path, source: str, name: str = "test_sample.py") -> Path:
    file_path = tmp_path / name
    file_path.write_text(source)
    return file_path


def test_module_exports_check_instance():
    assert isinstance(check, VacuousTestCheck)
    assert check.name == "vacuous_tests"
    assert check.kind == "static"


def test_empty_pass_body_is_flagged(tmp_path):
    source = "def test_thing():\n    pass\n"
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    kinds = [f["message"] for f in findings]
    assert "test body is empty" in kinds


def test_docstring_only_body_is_flagged(tmp_path):
    source = 'def test_thing():\n    """does nothing yet"""\n'
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    messages = [f["message"] for f in findings]
    assert "test body is empty" in messages


def test_no_assertions_is_flagged(tmp_path):
    source = "def test_thing():\n    x = 1 + 2\n    y = x * 3\n    print(y)\n"
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    messages = [f["message"] for f in findings]
    assert "test has no assertions" in messages


def test_assert_statement_satisfies_assertions_check(tmp_path):
    source = "def test_thing():\n    x = 1 + 2\n    assert x == 3\n"
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    messages = [f["message"] for f in findings]
    assert "test has no assertions" not in messages


def test_unittest_assertion_method_satisfies_assertions_check(tmp_path):
    source = "class TestThing:\n    def test_thing(self):\n        self.assertEqual(1, 1)\n"
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 2)])

    messages = [f["message"] for f in findings]
    assert "test has no assertions" not in messages


def test_mock_only_assertions_is_flagged(tmp_path):
    source = (
        "from unittest.mock import Mock\n"
        "\n"
        "def test_thing():\n"
        "    m = Mock()\n"
        "    m.do()\n"
        "    assert m.called\n"
    )
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 3)])

    messages = [f["message"] for f in findings]
    assert "test only asserts on mocks" in messages


def test_real_assertion_alongside_mock_is_not_flagged_as_mock_only(tmp_path):
    source = (
        "from unittest.mock import Mock\n"
        "\n"
        "def test_thing():\n"
        "    m = Mock()\n"
        "    real_value = 42\n"
        "    assert real_value == 42\n"
        "    assert m.called\n"
    )
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 3)])

    messages = [f["message"] for f in findings]
    assert "test only asserts on mocks" not in messages


def test_doesnt_call_new_function_is_flagged(tmp_path):
    source = "def test_thing():\n    assert 1 == 1\n"
    _write(tmp_path, source)
    # added_functions includes a new non-test function the test should call but doesn't
    funcs = [
        _added_func("test_sample.py", "test_thing", 1),
        _added_func("src/auth.py", "validate_jwt", 10, is_test=False),
    ]
    findings = check.run(str(tmp_path), funcs)

    messages = [f["message"] for f in findings]
    assert "test does not call any new function" in messages


def test_calls_new_function_is_not_flagged_for_reach(tmp_path):
    source = (
        "from src.auth import validate_jwt\n"
        "\n"
        "def test_thing():\n"
        "    assert validate_jwt('token') is True\n"
    )
    _write(tmp_path, source)
    funcs = [
        _added_func("test_sample.py", "test_thing", 3),
        _added_func("src/auth.py", "validate_jwt", 10, is_test=False),
    ]
    findings = check.run(str(tmp_path), funcs)

    messages = [f["message"] for f in findings]
    assert "test does not call any new function" not in messages


def test_non_test_function_is_skipped(tmp_path):
    source = "def helper():\n    pass\n"
    _write(tmp_path, source)
    findings = check.run(
        str(tmp_path),
        [_added_func("test_sample.py", "helper", 1, is_test=False)],
    )

    assert findings == []


def test_syntax_error_in_file_is_tolerated(tmp_path):
    _write(tmp_path, "def test_thing(:\n    not python\n")
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    assert findings == []


def test_missing_file_is_tolerated(tmp_path):
    findings = check.run(
        str(tmp_path),
        [_added_func("does_not_exist.py", "test_thing", 1)],
    )

    assert findings == []


def test_multiple_heuristics_fire_together(tmp_path):
    # Empty body satisfies both heuristic A (empty) and B (no assertions)
    source = "def test_thing():\n    pass\n"
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    messages = [f["message"] for f in findings]
    assert "test body is empty" in messages
    assert "test has no assertions" in messages


def test_empty_added_functions_returns_no_findings(tmp_path):
    assert check.run(str(tmp_path), []) == []


def test_finding_shape_is_well_formed(tmp_path):
    source = "def test_thing():\n    pass\n"
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("test_sample.py", "test_thing", 1)])

    assert findings, "expected at least one finding"
    for f in findings:
        assert f["kind"] == "vacuous_test"
        assert f["file"] == "test_sample.py"
        assert f["line"] == 1
        assert isinstance(f["message"], str)
        assert 0.0 <= f["confidence"] <= 1.0
