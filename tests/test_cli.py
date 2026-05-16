"""Tests for CLI module."""

import time
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from verdict.cli import cli, run_checks
from verdict.types import Finding


def test_run_no_checks_returns_pass_exit_0():
    """Test that CLI with no checks returns PASS and exits 0."""
    runner = CliRunner()

    with patch("verdict.cli.discover_checks", return_value=[]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", "."])

    assert result.exit_code == 0
    assert "Verdict: PASS" in result.output


def test_run_fail_on_lied_exits_1_on_lied():
    """Test that --fail-on lied exits 1 when verdict is LIED."""
    runner = CliRunner()

    # Create a fake check that returns high-confidence finding
    fake_check = MagicMock()
    fake_check.name = "fake_check"
    fake_check.kind = "static"
    finding: Finding = {
        "kind": "dead_function",
        "file": "test.py",
        "line": 1,
        "message": "test",
        "confidence": 0.95,
    }
    fake_check.run.return_value = [finding]

    with patch("verdict.cli.discover_checks", return_value=[fake_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--fail-on", "lied"])

    assert result.exit_code == 1
    assert "Verdict: LIED" in result.output


def test_run_fail_on_lied_exits_0_on_pass():
    """Test that --fail-on lied exits 0 when verdict is PASS."""
    runner = CliRunner()

    with patch("verdict.cli.discover_checks", return_value=[]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--fail-on", "lied"])

    assert result.exit_code == 0
    assert "Verdict: PASS" in result.output


def test_run_fail_on_suspicious_exits_1_on_suspicious():
    """Test that --fail-on suspicious exits 1 when verdict is SUSPICIOUS."""
    runner = CliRunner()

    # Create a fake check that returns medium-confidence finding
    fake_check = MagicMock()
    fake_check.name = "fake_check"
    fake_check.kind = "static"
    finding: Finding = {
        "kind": "dead_function",
        "file": "test.py",
        "line": 1,
        "message": "test",
        "confidence": 0.5,
    }
    fake_check.run.return_value = [finding]

    with patch("verdict.cli.discover_checks", return_value=[fake_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--fail-on", "suspicious"])

    assert result.exit_code == 1
    assert "Verdict: SUSPICIOUS" in result.output


def test_run_fail_on_suspicious_exits_1_on_lied():
    """Test that --fail-on suspicious exits 1 when verdict is LIED (worse)."""
    runner = CliRunner()

    # Create a fake check that returns high-confidence finding
    fake_check = MagicMock()
    fake_check.name = "fake_check"
    fake_check.kind = "static"
    finding: Finding = {
        "kind": "dead_function",
        "file": "test.py",
        "line": 1,
        "message": "test",
        "confidence": 0.95,
    }
    fake_check.run.return_value = [finding]

    with patch("verdict.cli.discover_checks", return_value=[fake_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--fail-on", "suspicious"])

    assert result.exit_code == 1
    assert "Verdict: LIED" in result.output


def test_run_json_flag_prints_json_to_stdout():
    """Test that --json flag prints JSON to stdout."""
    runner = CliRunner()

    with patch("verdict.cli.discover_checks", return_value=[]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--json"])

    assert result.exit_code == 0
    # Output should be valid JSON
    import json

    parsed = json.loads(result.output)
    assert "verdict" in parsed
    assert parsed["verdict"] == "PASS"


def test_run_check_exception_doesnt_crash_cli():
    """Test that a check raising an exception doesn't crash the CLI."""
    runner = CliRunner()

    # Create a fake check that raises an exception
    fake_check = MagicMock()
    fake_check.name = "broken_check"
    fake_check.kind = "static"
    fake_check.run.side_effect = RuntimeError("Check failed")

    with patch("verdict.cli.discover_checks", return_value=[fake_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", "."])

    # CLI should complete successfully
    assert result.exit_code == 0
    # Should print warning to stderr
    assert "Warning: Check 'broken_check' failed" in result.output


def test_run_static_only_filters_checks():
    """Test that --static-only filters out dynamic checks."""
    runner = CliRunner()

    # Create one static and one dynamic check
    static_check = MagicMock()
    static_check.name = "static_check"
    static_check.kind = "static"
    static_check.run.return_value = []

    dynamic_check = MagicMock()
    dynamic_check.name = "dynamic_check"
    dynamic_check.kind = "dynamic"
    dynamic_check.run.return_value = []

    with patch("verdict.cli.discover_checks", return_value=[static_check, dynamic_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--static-only"])

    assert result.exit_code == 0
    # Static check should have been called
    static_check.run.assert_called_once()
    # Dynamic check should NOT have been called
    dynamic_check.run.assert_not_called()


def test_run_dynamic_only_filters_checks():
    """Test that --dynamic-only filters out static checks."""
    runner = CliRunner()

    # Create one static and one dynamic check
    static_check = MagicMock()
    static_check.name = "static_check"
    static_check.kind = "static"
    static_check.run.return_value = []

    dynamic_check = MagicMock()
    dynamic_check.name = "dynamic_check"
    dynamic_check.kind = "dynamic"
    dynamic_check.run.return_value = []

    with patch("verdict.cli.discover_checks", return_value=[static_check, dynamic_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--dynamic-only"])

    assert result.exit_code == 0
    # Static check should NOT have been called
    static_check.run.assert_not_called()
    # Dynamic check should have been called
    dynamic_check.run.assert_called_once()


def test_run_both_flags_raises_error():
    """Test that using both --static-only and --dynamic-only raises an error."""
    runner = CliRunner()

    with patch("verdict.cli.discover_checks", return_value=[]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                result = runner.invoke(cli, ["run", ".", "--static-only", "--dynamic-only"])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "both static_only and dynamic_only" in result.output


def test_per_check_timeout_emits_finding_for_slow_check():
    """A check that exceeds per_check_timeout produces a check_timed_out finding."""
    slow_check = MagicMock()
    slow_check.name = "slow_check"
    slow_check.kind = "static"

    def slow_run(*args, **kwargs):
        time.sleep(1.5)
        return []

    slow_check.run.side_effect = slow_run

    with patch("verdict.cli.discover_checks", return_value=[slow_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                scorecard = run_checks(".", per_check_timeout=0.5)

    assert scorecard["summary"]["checks_timed_out"] == 1
    timeout_findings = [f for f in scorecard["findings"] if f["kind"] == "check_timed_out"]
    assert len(timeout_findings) == 1
    assert "slow_check" in timeout_findings[0]["message"]


def test_per_check_timeout_doesnt_block_other_checks():
    """One slow check timing out must not prevent other checks from running."""
    slow_check = MagicMock()
    slow_check.name = "slow"
    slow_check.kind = "static"

    def slow_run(*args, **kwargs):
        time.sleep(1.5)
        return []

    slow_check.run.side_effect = slow_run

    fast_check = MagicMock()
    fast_check.name = "fast"
    fast_check.kind = "static"
    fast_finding: Finding = {
        "kind": "fast_finding",
        "file": "f.py",
        "line": 1,
        "message": "fast check fired",
        "confidence": 0.5,
    }
    fast_check.run.return_value = [fast_finding]

    with patch("verdict.cli.discover_checks", return_value=[slow_check, fast_check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                scorecard = run_checks(".", per_check_timeout=0.5)

    assert scorecard["summary"]["checks_timed_out"] == 1
    kinds = {f["kind"] for f in scorecard["findings"]}
    assert "check_timed_out" in kinds
    assert "fast_finding" in kinds


def test_per_check_timeout_none_disables_timeout():
    """per_check_timeout=None preserves the original no-timeout behavior."""
    check = MagicMock()
    check.name = "slow_but_finishes"
    check.kind = "static"
    finding: Finding = {
        "kind": "real_finding",
        "file": "f.py",
        "line": 1,
        "message": "found something",
        "confidence": 0.5,
    }

    def slow_run(*args, **kwargs):
        time.sleep(0.1)
        return [finding]

    check.run.side_effect = slow_run

    with patch("verdict.cli.discover_checks", return_value=[check]):
        with patch("verdict.cli.get_changed_files", return_value=[]):
            with patch("verdict.cli.get_added_functions", return_value=[]):
                scorecard = run_checks(".", per_check_timeout=None)

    assert scorecard["summary"]["checks_timed_out"] == 0
    assert any(f["kind"] == "real_finding" for f in scorecard["findings"])


# Made with Bob
