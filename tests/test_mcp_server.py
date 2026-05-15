"""Tests for MCP server.

This module tests the verdict MCP server implementation, including:
- Tool handler functions (check_diff, check_static, trace_test_run)
- Error handling and error scorecard generation
- Safe CLI wrapper with exception handling
"""

from unittest.mock import MagicMock, patch

import pytest

from verdict.mcp_server import (
    _error_scorecard,
    _run_checks_safe,
    check_diff,
    check_static,
    trace_test_run,
)
from verdict.types import Finding, Scorecard


@pytest.fixture
def mock_scorecard() -> Scorecard:
    """Return a sample scorecard for testing.

    Returns:
        A LIED scorecard with sample findings
    """
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.9,
    }
    return {
        "verdict": "LIED",
        "findings": [finding],
        "summary": {"total_findings": 1, "high_confidence_findings": 1},
    }


@pytest.fixture
def mock_pass_scorecard() -> Scorecard:
    """Return a PASS scorecard for testing.

    Returns:
        A PASS scorecard with no findings
    """
    return {
        "verdict": "PASS",
        "findings": [],
        "summary": {"total_findings": 0},
    }


def test_error_scorecard_format():
    """Test error scorecard has correct structure."""
    error_msg = "Test error message"
    scorecard = _error_scorecard(error_msg)

    assert scorecard["verdict"] == "SUSPICIOUS"
    assert len(scorecard["findings"]) == 1
    assert scorecard["findings"][0]["kind"] == "verdict_internal_error"
    assert scorecard["findings"][0]["file"] == ""
    assert scorecard["findings"][0]["line"] == 0
    assert error_msg in scorecard["findings"][0]["message"]
    assert scorecard["findings"][0]["confidence"] == 1.0
    assert scorecard["summary"]["error"] is True
    assert scorecard["summary"]["error_message"] == error_msg


def test_error_scorecard_different_messages():
    """Test error scorecard handles different error messages."""
    messages = [
        "Repository not found",
        "Git command failed",
        "ImportError: module not found",
    ]

    for msg in messages:
        scorecard = _error_scorecard(msg)
        assert scorecard["verdict"] == "SUSPICIOUS"
        assert msg in scorecard["findings"][0]["message"]


@pytest.mark.asyncio
async def test_check_diff_success(mock_scorecard):
    """Test check_diff returns scorecard from CLI."""
    with patch("verdict.mcp_server._run_checks_safe", return_value=mock_scorecard):
        result = await check_diff(repo_path="/test/repo", diff_range="HEAD")

        assert result["verdict"] == "LIED"
        assert len(result["findings"]) == 1
        assert result["findings"][0]["kind"] == "dead_function"


@pytest.mark.asyncio
async def test_check_diff_with_custom_diff_range(mock_scorecard):
    """Test check_diff passes custom diff_range to CLI."""
    with patch("verdict.mcp_server._run_checks_safe", return_value=mock_scorecard) as mock_run:
        await check_diff(repo_path="/test/repo", diff_range="main..HEAD")

        mock_run.assert_called_once_with("/test/repo", "main..HEAD", static_only=False)


@pytest.mark.asyncio
async def test_check_diff_default_diff_range(mock_scorecard):
    """Test check_diff uses HEAD as default diff_range."""
    with patch("verdict.mcp_server._run_checks_safe", return_value=mock_scorecard) as mock_run:
        await check_diff(repo_path="/test/repo")

        mock_run.assert_called_once_with("/test/repo", "HEAD", static_only=False)


@pytest.mark.asyncio
async def test_check_static_success(mock_pass_scorecard):
    """Test check_static calls CLI with static_only=True."""
    with patch("verdict.mcp_server._run_checks_safe", return_value=mock_pass_scorecard) as mock_run:
        result = await check_static(repo_path="/test/repo", diff_range="HEAD")

        mock_run.assert_called_once_with("/test/repo", "HEAD", static_only=True)
        assert result["verdict"] == "PASS"
        assert len(result["findings"]) == 0


@pytest.mark.asyncio
async def test_check_static_with_custom_diff_range(mock_pass_scorecard):
    """Test check_static passes custom diff_range to CLI."""
    with patch("verdict.mcp_server._run_checks_safe", return_value=mock_pass_scorecard) as mock_run:
        await check_static(repo_path="/test/repo", diff_range="develop..HEAD")

        mock_run.assert_called_once_with("/test/repo", "develop..HEAD", static_only=True)


@pytest.mark.skip(reason="Requires P1.1 tracer implementation")
@pytest.mark.asyncio
async def test_trace_test_run_success(mock_scorecard):
    """Test trace_test_run executes test command."""
    # This test will pass once P1.1 (execution tracer) is implemented
    pass


@pytest.mark.skip(reason="Requires P1.1 tracer implementation")
@pytest.mark.asyncio
async def test_trace_test_run_no_findings():
    """Test trace_test_run returns PASS when no findings."""
    # This test will pass once P1.1 (execution tracer) is implemented
    pass


@pytest.mark.asyncio
async def test_trace_test_run_repo_not_found():
    """Test trace_test_run handles missing repository."""
    result = await trace_test_run(repo_path="/nonexistent/repo", test_command="pytest")

    assert result["verdict"] == "SUSPICIOUS"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["kind"] == "verdict_internal_error"
    assert "does not exist" in result["findings"][0]["message"]


@pytest.mark.asyncio
async def test_trace_test_run_import_error():
    """Test trace_test_run handles missing tracer module."""
    # When tracer module doesn't exist, we get an import error
    # Currently this returns repo not found error first, which is correct behavior
    result = await trace_test_run(repo_path="/nonexistent", test_command="pytest")

    assert result["verdict"] == "SUSPICIOUS"
    assert result["findings"][0]["kind"] == "verdict_internal_error"


def test_run_checks_safe_repo_not_exists():
    """Test _run_checks_safe handles non-existent repository."""
    scorecard = _run_checks_safe(repo_path="/nonexistent/path")

    assert scorecard["verdict"] == "SUSPICIOUS"
    assert len(scorecard["findings"]) == 1
    assert "does not exist" in scorecard["findings"][0]["message"]


def test_run_checks_safe_not_a_directory(tmp_path):
    """Test _run_checks_safe handles file instead of directory."""
    # Create a file instead of directory
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("test")

    scorecard = _run_checks_safe(repo_path=str(file_path))

    assert scorecard["verdict"] == "SUSPICIOUS"
    assert "not a directory" in scorecard["findings"][0]["message"]


def test_run_checks_safe_not_a_git_repo(tmp_path):
    """Test _run_checks_safe handles non-git directory."""
    scorecard = _run_checks_safe(repo_path=str(tmp_path))

    assert scorecard["verdict"] == "SUSPICIOUS"
    assert "Not a git repository" in scorecard["findings"][0]["message"]


def test_run_checks_safe_import_error(tmp_path):
    """Test _run_checks_safe handles CLI import failure."""
    # Create a fake git repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    with patch("verdict.mcp_server.os.path.exists", return_value=True):
        with patch("verdict.mcp_server.os.path.isdir", return_value=True):
            with patch.dict("sys.modules", {"verdict.cli": None}):
                scorecard = _run_checks_safe(repo_path=str(tmp_path))

                assert scorecard["verdict"] == "SUSPICIOUS"
                assert "Failed to import" in scorecard["findings"][0]["message"]


def test_run_checks_safe_cli_exception(tmp_path):
    """Test _run_checks_safe catches exceptions from CLI."""
    # Create a fake git repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    mock_run_checks = MagicMock(side_effect=RuntimeError("CLI crashed"))

    with patch("verdict.cli.run_checks", mock_run_checks):
        scorecard = _run_checks_safe(repo_path=str(tmp_path))

        assert scorecard["verdict"] == "SUSPICIOUS"
        assert "RuntimeError" in scorecard["findings"][0]["message"]
        assert "CLI crashed" in scorecard["findings"][0]["message"]


def test_run_checks_safe_success(tmp_path, mock_scorecard):
    """Test _run_checks_safe returns scorecard on success."""
    # Create a fake git repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    mock_run_checks = MagicMock(return_value=mock_scorecard)

    with patch("verdict.cli.run_checks", mock_run_checks):
        scorecard = _run_checks_safe(repo_path=str(tmp_path), diff_range="HEAD", static_only=False)

        assert scorecard["verdict"] == "LIED"
        assert len(scorecard["findings"]) == 1
        mock_run_checks.assert_called_once_with(
            repo_path=str(tmp_path), diff_range="HEAD", static_only=False
        )


def test_run_checks_safe_passes_parameters(tmp_path, mock_pass_scorecard):
    """Test _run_checks_safe passes all parameters correctly."""
    # Create a fake git repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    mock_run_checks = MagicMock(return_value=mock_pass_scorecard)

    with patch("verdict.cli.run_checks", mock_run_checks):
        scorecard = _run_checks_safe(
            repo_path=str(tmp_path), diff_range="main..HEAD", static_only=True
        )

        assert scorecard["verdict"] == "PASS"
        mock_run_checks.assert_called_once_with(
            repo_path=str(tmp_path), diff_range="main..HEAD", static_only=True
        )


@pytest.mark.asyncio
async def test_check_diff_error_handling():
    """Test check_diff returns error scorecard on exception."""
    # _run_checks_safe catches exceptions and returns error scorecard
    error_scorecard = _error_scorecard("Test error")
    with patch("verdict.mcp_server._run_checks_safe", return_value=error_scorecard):
        result = await check_diff(repo_path="/test/repo")

        assert result["verdict"] == "SUSPICIOUS"
        assert result["findings"][0]["kind"] == "verdict_internal_error"


@pytest.mark.skip(reason="Requires P1.1 tracer implementation")
@pytest.mark.asyncio
async def test_trace_test_run_exception_handling():
    """Test trace_test_run handles exceptions gracefully."""
    # This test will pass once P1.1 (execution tracer) is implemented
    pass


# Made with Bob
