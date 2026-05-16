"""Tests for the coverage_delta check.

The full check spawns a pytest subprocess and is hard to unit-test directly.
These tests target the `_executable_lines` helper, which is the source of
the comment-line bug we hit when verdict scanned its own diffs.
"""

from verdict.checks.coverage_delta import _executable_lines


def test_executable_lines_skips_blank_and_comment_only(tmp_path):
    source = (
        "# top-level comment\n"
        "\n"
        "import os\n"
        "\n"
        "    # indented comment\n"
        "x = 1\n"
        "    \n"
        "y = 2  # trailing comment is still executable\n"
    )
    file_path = tmp_path / "sample.py"
    file_path.write_text(source)

    result = _executable_lines(str(file_path))

    # Lines 3 (import), 6 (x=1), 8 (y=2) are executable.
    # Lines 1, 5 are comment-only. Lines 2, 4, 7 are blank.
    assert result == {3, 6, 8}


def test_executable_lines_missing_file_returns_empty():
    """Helper returns empty set, not raises, on a path that does not exist."""
    assert _executable_lines("/no/such/file.py") == set()


def test_executable_lines_empty_file(tmp_path):
    file_path = tmp_path / "empty.py"
    file_path.write_text("")
    assert _executable_lines(str(file_path)) == set()
