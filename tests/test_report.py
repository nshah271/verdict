"""Tests for report module."""

import json

from verdict.report import build_scorecard, format_json, format_terminal
from verdict.types import Finding


def test_build_scorecard_empty_findings_returns_pass():
    """Test that empty findings list returns PASS verdict."""
    findings = []
    summary = {"total_findings": 0}

    scorecard = build_scorecard(findings, summary)

    assert scorecard["verdict"] == "PASS"
    assert scorecard["findings"] == []
    assert scorecard["summary"] == summary


def test_build_scorecard_low_confidence_returns_suspicious():
    """Test that low confidence finding returns SUSPICIOUS verdict."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.5,
    }
    findings = [finding]
    summary = {"total_findings": 1}

    scorecard = build_scorecard(findings, summary)

    assert scorecard["verdict"] == "SUSPICIOUS"
    assert len(scorecard["findings"]) == 1


def test_build_scorecard_high_confidence_returns_lied():
    """Test that high confidence finding returns LIED verdict."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.95,
    }
    findings = [finding]
    summary = {"total_findings": 1}

    scorecard = build_scorecard(findings, summary)

    assert scorecard["verdict"] == "LIED"
    assert len(scorecard["findings"]) == 1


def test_build_scorecard_mixed_confidence_keeps_lied():
    """Test that mixed confidence findings keep LIED verdict (worst case wins)."""
    finding1: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.9,
    }
    finding2: Finding = {
        "kind": "vacuous_test",
        "file": "tests/test_auth.py",
        "line": 15,
        "message": "test has no assertions",
        "confidence": 0.5,
    }
    findings = [finding1, finding2]
    summary = {"total_findings": 2}

    scorecard = build_scorecard(findings, summary)

    assert scorecard["verdict"] == "LIED"
    assert len(scorecard["findings"]) == 2


def test_format_json_is_deterministic():
    """Test that format_json produces byte-identical output for same input."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.9,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1})

    output1 = format_json(scorecard)
    output2 = format_json(scorecard)

    assert output1 == output2
    assert isinstance(output1, str)


def test_format_json_has_sorted_keys():
    """Test that format_json output has alphabetically sorted keys."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.9,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1})

    output = format_json(scorecard)
    parsed = json.loads(output)

    # Check that top-level keys are sorted
    keys = list(parsed.keys())
    assert keys == sorted(keys)


def test_format_terminal_includes_verdict_line():
    """Test that terminal output includes verdict line."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.9,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    assert "Verdict: LIED" in output


def test_format_terminal_includes_finding_lines():
    """Test that terminal output includes one line per finding."""
    finding1: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "validate_jwt() has 0 callers",
        "confidence": 0.9,
    }
    finding2: Finding = {
        "kind": "vacuous_test",
        "file": "tests/test_auth.py",
        "line": 15,
        "message": "test has no assertions",
        "confidence": 0.85,
    }
    scorecard = build_scorecard(
        [finding1, finding2],
        {"total_findings": 2, "diff_range": "HEAD"},
    )

    output = format_terminal(scorecard)

    # Check that both findings appear in output
    assert "src/auth.py:42" in output
    assert "validate_jwt() has 0 callers" in output
    assert "tests/test_auth.py:15" in output
    assert "test has no assertions" in output
    assert "confidence: 0.90" in output
    assert "confidence: 0.85" in output


# Made with Bob
