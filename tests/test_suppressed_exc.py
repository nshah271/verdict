"""Tests for suppressed exception detection."""

from pathlib import Path

from verdict.checks.suppressed_exc import find_suppressed_exceptions, check
from verdict.types import ChangedFile


# Helper to construct ChangedFile for testing
def _make_changed_file(path: str, added_lines: list[int]) -> ChangedFile:
    """Create a ChangedFile dict for testing."""
    return ChangedFile(
        path=path,
        added_lines=added_lines,
        removed_lines=[],
    )


def test_broad_exception_pass_flagged():
    """Test that except Exception: pass is flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # broad_exception_pass function: try at line 10, except at line 12
    changed_files = [_make_changed_file(fixture_path, [10, 11, 12, 13])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["kind"] == "suppressed_exception"
    assert findings[0]["file"] == fixture_path
    assert findings[0]["line"] == 12  # except handler line
    assert "except Exception" in findings[0]["message"]
    assert "pass" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.85  # broad exception


def test_bare_except_ellipsis_flagged():
    """Test that bare except: ... is flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # bare_except_ellipsis function: try at line 18, except at line 20
    changed_files = [_make_changed_file(fixture_path, [18, 19, 20, 21])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["kind"] == "suppressed_exception"
    assert findings[0]["line"] == 20
    assert "except:" in findings[0]["message"]
    assert "..." in findings[0]["message"]
    assert findings[0]["confidence"] == 0.9  # bare except


def test_narrow_exception_pass_flagged():
    """Test that except KeyError: pass is flagged with lower confidence."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # narrow_exception_pass function: try at line 26, except at line 29
    changed_files = [_make_changed_file(fixture_path, [26, 27, 28, 29, 30])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["kind"] == "suppressed_exception"
    assert findings[0]["line"] == 29
    assert "except KeyError" in findings[0]["message"]
    assert "pass" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.5  # narrow exception


def test_logger_only_handler_flagged():
    """Test that except with only logger call is flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # logger_only_handler function: try at line 36, except at line 38
    changed_files = [_make_changed_file(fixture_path, [36, 37, 38, 39])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["kind"] == "suppressed_exception"
    assert findings[0]["line"] == 38
    assert "except Exception" in findings[0]["message"]
    assert "logger.error" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.85


def test_continue_in_loop_flagged():
    """Test that except with continue is flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # continue_in_loop function: try at line 46, except at line 48
    changed_files = [_make_changed_file(fixture_path, [46, 47, 48, 49])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["kind"] == "suppressed_exception"
    assert findings[0]["line"] == 48
    assert "except Exception" in findings[0]["message"]
    assert "continue" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.85


def test_reraise_handler_not_flagged():
    """Test that except with raise is NOT flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # reraise_handler function: try at line 54, except at line 56
    changed_files = [_make_changed_file(fixture_path, [54, 55, 56, 57])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 0


def test_return_handler_not_flagged():
    """Test that except with return is NOT flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # return_handler function: try at line 62, except at line 64
    changed_files = [_make_changed_file(fixture_path, [62, 63, 64, 65])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 0


def test_multi_statement_handler_not_flagged():
    """Test that except with multiple statements is NOT flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # multi_statement_handler function: try at line 71, except at line 73
    changed_files = [_make_changed_file(fixture_path, [71, 72, 73, 74, 75])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 0


def test_clean_function_not_flagged():
    """Test that function without try/except is NOT flagged."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # clean_function: lines 78-80
    changed_files = [_make_changed_file(fixture_path, [78, 79, 80])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 0


def test_confidence_bare_except():
    """Test that bare except has confidence 0.9."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    changed_files = [_make_changed_file(fixture_path, [18, 19, 20, 21])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["confidence"] == 0.9


def test_confidence_broad_exception():
    """Test that except Exception has confidence 0.85."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    changed_files = [_make_changed_file(fixture_path, [10, 11, 12, 13])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["confidence"] == 0.85


def test_confidence_narrow_exception():
    """Test that narrow exception has confidence 0.5."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    changed_files = [_make_changed_file(fixture_path, [26, 27, 28, 29, 30])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["confidence"] == 0.5


def test_long_try_body_boosts_confidence():
    """Test that long try body (>10 lines) boosts confidence by 0.05."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # long_try_body function: try at line 85, except at line 99
    # Try body spans lines 85-98 (14 lines)
    changed_files = [_make_changed_file(fixture_path, list(range(85, 101)))]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["confidence"] == 0.9  # 0.85 + 0.05 boost


def test_confidence_capped_at_95():
    """Test that confidence is capped at 0.95 even with boost."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # bare_except_long_body function: try at line 127, except at line 141
    # Bare except (0.9) + long try body (>10 lines, +0.05) = 0.95 (capped)
    changed_files = [_make_changed_file(fixture_path, list(range(127, 143)))]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 1
    assert findings[0]["confidence"] == 0.95


def test_non_python_files_skipped():
    """Test that non-Python files are skipped."""
    changed_files = [_make_changed_file("README.md", [1, 2, 3])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 0


def test_no_added_lines_skipped():
    """Test that files with no added lines are skipped."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    changed_files = [_make_changed_file(fixture_path, [])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    assert len(findings) == 0


def test_syntax_error_handled(tmp_path: Path):
    """Test that files with syntax errors don't crash the check."""
    # Create a file with syntax error
    broken_file = tmp_path / "broken.py"
    broken_file.write_text("def broken(\n    # Missing closing paren\n")
    
    changed_files = [_make_changed_file("broken.py", [1, 2])]
    
    # Should not crash, just skip the broken file
    findings = find_suppressed_exceptions(changed_files, str(tmp_path))
    
    assert len(findings) == 0


def test_nested_try_blocks():
    """Test that nested try blocks are both analyzed if added."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # nested_try_blocks function: outer try at 105, inner try at 107
    # Both handlers should be flagged
    changed_files = [_make_changed_file(fixture_path, list(range(105, 113)))]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    # Should flag both the outer and inner handlers
    assert len(findings) == 2
    # Inner handler at line 109
    inner = [f for f in findings if f["line"] == 109]
    assert len(inner) == 1
    assert "except KeyError" in inner[0]["message"]
    # Outer handler at line 111
    outer = [f for f in findings if f["line"] == 111]
    assert len(outer) == 1
    assert "except Exception" in outer[0]["message"]


def test_try_not_in_added_lines_skipped():
    """Test that try blocks not in added_lines are skipped."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # Only mark the except handler as added, not the try
    changed_files = [_make_changed_file(fixture_path, [12, 13])]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    # Should not flag because try line (10) is not in added_lines
    assert len(findings) == 0


def test_multiple_handlers_in_one_try():
    """Test that multiple handlers in one try block are analyzed separately."""
    fixture_path = "tests/fixtures/suppressed_exc_sample.py"
    # multiple_handlers function: try at line 117, KeyError at 119, ValueError at 121
    # Should flag only the KeyError handler (pass), not ValueError (raise)
    changed_files = [_make_changed_file(fixture_path, list(range(117, 123)))]
    
    findings = find_suppressed_exceptions(changed_files, ".")
    
    # Should flag exactly 1 finding (KeyError with pass)
    assert len(findings) == 1
    assert findings[0]["line"] == 119
    assert "except KeyError" in findings[0]["message"]
    assert "pass" in findings[0]["message"]


def test_check_module_attributes():
    """Test that the module-level check has correct attributes."""
    from verdict.checks import suppressed_exc
    
    # Check that module-level check exists
    assert hasattr(suppressed_exc, "check")
    assert suppressed_exc.check.name == "suppressed_exception"
    assert suppressed_exc.check.kind == "static"
    
    # Check that it has the run method
    assert hasattr(suppressed_exc.check, "run")
    assert callable(suppressed_exc.check.run)


def test_check_class_attributes():
    """Test that SuppressedExceptionCheck class has correct attributes."""
    from verdict.checks.suppressed_exc import SuppressedExceptionCheck
    
    check_instance = SuppressedExceptionCheck()
    assert check_instance.name == "suppressed_exception"
    assert check_instance.kind == "static"
    assert hasattr(check_instance, "run")
    assert callable(check_instance.run)


def test_empty_changed_files():
    """Test that empty changed_files list returns empty findings."""
    findings = find_suppressed_exceptions([], ".")
    assert findings == []


def test_file_not_found_handled(tmp_path: Path):
    """Test that missing files don't crash the check."""
    changed_files = [_make_changed_file("nonexistent.py", [1, 2, 3])]
    
    # Should not crash, just skip the missing file
    findings = find_suppressed_exceptions(changed_files, str(tmp_path))
    
    assert len(findings) == 0

# Made with Bob
