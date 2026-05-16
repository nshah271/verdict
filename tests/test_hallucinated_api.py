"""Tests for the hallucinated_api check.

Covers detection of non-existent methods and attributes on objects,
including user-defined classes, builtins, and third-party libraries.
"""

import textwrap
from pathlib import Path

from verdict.checks.hallucinated_api import HallucinatedApiCheck, check
from verdict.types import AddedFunction


def _added_func(
    file: str,
    name: str,
    line: int,
    end_line: int | None = None,
    is_test: bool = False,
) -> AddedFunction:
    """Helper to create AddedFunction records for testing."""
    return {
        "file": file,
        "name": name,
        "line": line,
        "end_line": end_line if end_line is not None else line + 5,
        "is_test": is_test,
        "decorators": [],
    }


def _write(tmp_path: Path, source: str, name: str = "sample.py") -> Path:
    """Helper to write source code to a temporary file."""
    file_path = tmp_path / name
    dedented = textwrap.dedent(source)
    file_path.write_text(dedented)
    return file_path


def test_module_exports_check_instance():
    """Verify the check module exports the correct instance."""
    assert isinstance(check, HallucinatedApiCheck)
    assert check.name == "hallucinated_api"
    assert check.kind == "static"


def test_real_method_no_finding(tmp_path):
    """Real method calls should not produce findings."""
    source = """class Foo:
    def bar(self):
        pass

def use_foo():
    obj = Foo()
    obj.bar()
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "use_foo", 5, 7)])

    assert len(findings) == 0


def test_missing_method_user_class_emits_high_confidence(tmp_path):
    """Hallucinated method on user-defined class should emit high-confidence finding."""
    source = """class Foo:
    def bar(self):
        pass

def use_foo():
    obj = Foo()
    obj.baz()
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "use_foo", 5, 7)])

    assert len(findings) == 1
    finding = findings[0]
    assert finding["kind"] == "hallucinated_api"
    assert finding["file"] == "sample.py"
    assert finding["line"] == 7
    assert "baz" in finding["message"]
    assert "Foo" in finding["message"]
    assert finding["confidence"] >= 0.85


def test_missing_method_on_str_builtin(tmp_path):
    """Hallucinated method on str builtin should emit finding."""
    source = """def process_string():
    text = "hello"
    result = text.uppercase()
    return result
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "process_string", 1, 4)])

    assert len(findings) == 1
    finding = findings[0]
    assert finding["kind"] == "hallucinated_api"
    assert "uppercase" in finding["message"]
    assert finding["confidence"] >= 0.7


def test_missing_method_on_list_builtin(tmp_path):
    """Hallucinated method on list builtin (Java-brain case) should emit finding."""
    source = """def process_list():
    items = []
    items.add(1)
    return items
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "process_list", 1, 4)])

    assert len(findings) == 1
    finding = findings[0]
    assert finding["kind"] == "hallucinated_api"
    assert "add" in finding["message"]


def test_any_type_suppressed(tmp_path):
    """Attributes on Any type should be suppressed."""
    source = """from typing import Any

def use_any():
    x: Any = something()
    x.whatever()
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "use_any", 3, 5)])

    # Should be suppressed because x is typed as Any
    assert len(findings) == 0


def test_unresolved_import_suppressed(tmp_path):
    """Attributes on unresolved imports should be suppressed."""
    source = """from nonexistent_module import SomeClass

def use_unresolved():
    obj = SomeClass()
    obj.whatever()
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "use_unresolved", 3, 5)])

    # Should be suppressed because SomeClass can't be resolved
    assert len(findings) == 0


def test_dunder_attr_suppressed(tmp_path):
    """Dunder attributes should be suppressed."""
    source = """def use_dunder():
    obj = object()
    obj.__weird__
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "use_dunder", 1, 3)])

    # Dunder attributes are suppressed
    assert len(findings) == 0


def test_only_added_functions_scanned(tmp_path):
    """Only functions in added_functions list should be scanned."""
    source = """class Foo:
    def bar(self):
        pass

def not_added():
    obj = Foo()
    obj.hallucinated()

def added_func():
    obj = Foo()
    obj.bar()
"""
    _write(tmp_path, source)
    # Only scan added_func, not not_added
    findings = check.run(str(tmp_path), [_added_func("sample.py", "added_func", 9, 11)])

    # Should find no issues in added_func (bar is real)
    # Should NOT scan not_added (even though it has hallucinated call)
    assert len(findings) == 0


def test_bare_attribute_read_also_flags(tmp_path):
    """Bare attribute reads (not calls) should also be flagged."""
    source = """class Foo:
    def bar(self):
        pass

def read_attr():
    obj = Foo()
    result = obj.nonexistent
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "read_attr", 5, 7)])

    assert len(findings) == 1
    finding = findings[0]
    assert "nonexistent" in finding["message"]


def test_finding_shape_is_well_formed(tmp_path):
    """Verify Finding structure has all required fields with correct types."""
    source = """def bad_call():
    items = []
    items.add(1)
"""
    _write(tmp_path, source)
    findings = check.run(str(tmp_path), [_added_func("sample.py", "bad_call", 1, 3)])

    assert len(findings) == 1
    finding = findings[0]

    # Check all required keys are present
    assert "kind" in finding
    assert "file" in finding
    assert "line" in finding
    assert "message" in finding
    assert "confidence" in finding

    # Check types
    assert isinstance(finding["kind"], str)
    assert isinstance(finding["file"], str)
    assert isinstance(finding["line"], int)
    assert isinstance(finding["message"], str)
    assert isinstance(finding["confidence"], float)

    # Check value constraints
    assert finding["kind"] == "hallucinated_api"
    assert 0.0 <= finding["confidence"] <= 1.0
    assert len(finding["message"]) > 0


def test_real_library_smoke(tmp_path):
    """End-to-end test with real stdlib library (pathlib)."""
    source = """from pathlib import Path

def good_path():
    p = Path("/tmp")
    return p.exists()

def bad_path():
    p = Path("/tmp")
    return p.doesnotexist()
"""
    _write(tmp_path, source)

    # Test both functions
    findings = check.run(
        str(tmp_path),
        [
            _added_func("sample.py", "good_path", 3, 5),
            _added_func("sample.py", "bad_path", 7, 9),
        ],
    )

    # Should find one issue in bad_path, none in good_path
    assert len(findings) == 1
    finding = findings[0]
    assert finding["line"] == 9  # Line with doesnotexist()
    assert "doesnotexist" in finding["message"]
    assert finding["confidence"] >= 0.7


# Made with Bob
