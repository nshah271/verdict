"""Tests for diff parsing functionality."""

from pathlib import Path

from verdict.diff import _parse_unified_diff


def test_parse_basic_diff():
    """Test parsing a basic unified diff with additions and deletions."""
    diff_text = Path("tests/fixtures/sample.diff").read_text()
    changed_files = _parse_unified_diff(diff_text)

    # Convert to dict for easier lookup
    files_by_path = {f["path"]: f for f in changed_files}

    # Check src/app.py
    assert "src/app.py" in files_by_path
    app_file = files_by_path["src/app.py"]
    assert app_file["added_lines"] == [11, 12, 13]
    assert app_file["removed_lines"] == [20, 21]


def test_parse_new_file():
    """Test parsing a newly created file."""
    diff_text = Path("tests/fixtures/sample.diff").read_text()
    changed_files = _parse_unified_diff(diff_text)

    files_by_path = {f["path"]: f for f in changed_files}

    # Check tests/test_feature.py (new file)
    assert "tests/test_feature.py" in files_by_path
    test_file = files_by_path["tests/test_feature.py"]
    assert test_file["added_lines"] == [1, 2, 3, 4, 5]
    assert test_file["removed_lines"] == []


def test_parse_renamed_file():
    """Test parsing a renamed file with additions."""
    diff_text = Path("tests/fixtures/sample.diff").read_text()
    changed_files = _parse_unified_diff(diff_text)

    files_by_path = {f["path"]: f for f in changed_files}

    # Check new_file.py (renamed from old_file.py, use b/ path)
    assert "new_file.py" in files_by_path
    renamed_file = files_by_path["new_file.py"]
    assert renamed_file["added_lines"] == [6, 7]
    assert renamed_file["removed_lines"] == []


def test_binary_file_skipped():
    """Test that binary files are skipped."""
    diff_text = Path("tests/fixtures/sample.diff").read_text()
    changed_files = _parse_unified_diff(diff_text)

    files_by_path = {f["path"]: f for f in changed_files}

    # Binary file should not be in results
    assert "data/image.png" not in files_by_path


def test_pure_deletion():
    """Test file with only deletions (no additions)."""
    diff_text = Path("tests/fixtures/sample.diff").read_text()
    changed_files = _parse_unified_diff(diff_text)

    files_by_path = {f["path"]: f for f in changed_files}

    # Check deleted_only.py
    assert "deleted_only.py" in files_by_path
    deleted_file = files_by_path["deleted_only.py"]
    assert deleted_file["added_lines"] == []
    assert deleted_file["removed_lines"] == [10, 11, 12]


def test_multiple_hunks():
    """Test file with multiple hunks."""
    diff_text = Path("tests/fixtures/sample.diff").read_text()
    changed_files = _parse_unified_diff(diff_text)

    files_by_path = {f["path"]: f for f in changed_files}

    # Check src/multi_hunk.py
    assert "src/multi_hunk.py" in files_by_path
    multi_hunk = files_by_path["src/multi_hunk.py"]
    # First hunk adds at lines 6-7, second hunk adds at lines 18-19
    assert multi_hunk["added_lines"] == [6, 7, 18, 19]
    assert multi_hunk["removed_lines"] == []


def test_empty_diff():
    """Test parsing an empty diff."""
    changed_files = _parse_unified_diff("")
    assert changed_files == []


def test_diff_with_no_changes():
    """Test diff with file headers but no actual changes."""
    diff_text = """diff --git a/unchanged.py b/unchanged.py
index 1234567..1234567 100644
--- a/unchanged.py
+++ b/unchanged.py
"""
    changed_files = _parse_unified_diff(diff_text)
    
    # File should still appear but with empty change lists
    assert len(changed_files) == 1
    assert changed_files[0]["path"] == "unchanged.py"
    assert changed_files[0]["added_lines"] == []
    assert changed_files[0]["removed_lines"] == []

# Made with Bob
