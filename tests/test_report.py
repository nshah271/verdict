"""Tests for report module."""

import json
import re

import click

from verdict.report import build_scorecard, format_json, format_terminal
from verdict.types import Finding


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    """Strip ANSI escape codes from string."""
    return _ANSI_RE.sub("", s)


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
    stripped = _strip_ansi(output)

    assert "Verdict: LIED" in stripped


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



def test_build_scorecard_sorts_findings_by_confidence_desc():
    """Test that findings are sorted by confidence descending."""
    finding1: Finding = {
        "kind": "dead_function",
        "file": "src/a.py",
        "line": 10,
        "message": "low confidence",
        "confidence": 0.3,
    }
    finding2: Finding = {
        "kind": "dead_function",
        "file": "src/b.py",
        "line": 20,
        "message": "high confidence",
        "confidence": 0.9,
    }
    finding3: Finding = {
        "kind": "dead_function",
        "file": "src/c.py",
        "line": 30,
        "message": "medium confidence",
        "confidence": 0.6,
    }
    # Input order: 0.3, 0.9, 0.6
    findings = [finding1, finding2, finding3]
    summary = {"total_findings": 3}

    scorecard = build_scorecard(findings, summary)

    # Expected order: 0.9, 0.6, 0.3
    assert scorecard["findings"][0]["confidence"] == 0.9
    assert scorecard["findings"][1]["confidence"] == 0.6
    assert scorecard["findings"][2]["confidence"] == 0.3


def test_build_scorecard_tie_breaks_deterministically():
    """Test that same confidence findings sort deterministically by kind, file, line."""
    finding1: Finding = {
        "kind": "vacuous_test",
        "file": "tests/test_b.py",
        "line": 20,
        "message": "test 1",
        "confidence": 0.7,
    }
    finding2: Finding = {
        "kind": "dead_function",
        "file": "src/a.py",
        "line": 10,
        "message": "test 2",
        "confidence": 0.7,
    }
    
    # Build with both orders
    scorecard1 = build_scorecard([finding1, finding2], {"total_findings": 2})
    scorecard2 = build_scorecard([finding2, finding1], {"total_findings": 2})

    # Both should produce same order: dead_function before vacuous_test (alphabetical)
    assert scorecard1["findings"][0]["kind"] == "dead_function"
    assert scorecard1["findings"][1]["kind"] == "vacuous_test"
    assert scorecard2["findings"][0]["kind"] == "dead_function"
    assert scorecard2["findings"][1]["kind"] == "vacuous_test"


def test_format_terminal_colors_lied_verdict_red_bold():
    """Test that LIED verdict is colored red and bold."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "test",
        "confidence": 0.95,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    expected = click.style("LIED", fg="red", bold=True)
    assert expected in output


def test_format_terminal_colors_suspicious_yellow_bold():
    """Test that SUSPICIOUS verdict is colored yellow and bold."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "test",
        "confidence": 0.5,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    expected = click.style("SUSPICIOUS", fg="yellow", bold=True)
    assert expected in output


def test_format_terminal_colors_pass_green_bold():
    """Test that PASS verdict is colored green and bold."""
    scorecard = build_scorecard([], {"total_findings": 0, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    expected = click.style("PASS", fg="green", bold=True)
    assert expected in output


def test_format_terminal_colors_high_confidence_red():
    """Test that high confidence (>0.8) is colored red."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "test",
        "confidence": 0.9,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    expected = click.style("(confidence: 0.90)", fg="red")
    assert expected in output


def test_format_terminal_colors_medium_confidence_yellow():
    """Test that medium confidence (0.5-0.8) is colored yellow."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "test",
        "confidence": 0.5,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    expected = click.style("(confidence: 0.50)", fg="yellow")
    assert expected in output


def test_format_terminal_colors_low_confidence_green():
    """Test that low confidence (<0.5) is colored green."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "test",
        "confidence": 0.3,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_terminal(scorecard)

    expected = click.style("(confidence: 0.30)", fg="green")
    assert expected in output


def test_format_terminal_summary_includes_kind_breakdown():
    """Test that summary includes per-kind breakdown."""
    finding1: Finding = {
        "kind": "dead_function",
        "file": "src/a.py",
        "line": 10,
        "message": "test 1",
        "confidence": 0.9,
    }
    finding2: Finding = {
        "kind": "dead_function",
        "file": "src/b.py",
        "line": 20,
        "message": "test 2",
        "confidence": 0.8,
    }
    finding3: Finding = {
        "kind": "vacuous_test",
        "file": "tests/test_a.py",
        "line": 5,
        "message": "test 3",
        "confidence": 0.7,
    }
    finding4: Finding = {
        "kind": "trace",
        "file": "src/c.py",
        "line": 15,
        "message": "test 4",
        "confidence": 0.6,
    }
    scorecard = build_scorecard(
        [finding1, finding2, finding3, finding4],
        {"total_findings": 4, "diff_range": "HEAD"},
    )

    output = format_terminal(scorecard)
    stripped = _strip_ansi(output)

    # Check for kind breakdown
    assert "dead_function: 2" in stripped
    assert "vacuous_test: 1" in stripped
    assert "trace: 1" in stripped


def test_format_terminal_kind_breakdown_sorted_by_count_desc():
    """Test that kind breakdown is sorted by count descending."""
    findings = []
    # 3 dead_function findings
    for i in range(3):
        findings.append({
            "kind": "dead_function",
            "file": f"src/{i}.py",
            "line": i,
            "message": f"test {i}",
            "confidence": 0.9,
        })
    # 1 vacuous_test finding
    findings.append({
        "kind": "vacuous_test",
        "file": "tests/test.py",
        "line": 10,
        "message": "test",
        "confidence": 0.8,
    })
    # 2 trace findings
    for i in range(2):
        findings.append({
            "kind": "trace",
            "file": f"src/t{i}.py",
            "line": i,
            "message": f"trace {i}",
            "confidence": 0.7,
        })
    
    scorecard = build_scorecard(findings, {"total_findings": 6, "diff_range": "HEAD"})
    output = format_terminal(scorecard)
    stripped = _strip_ansi(output)

    # Find positions of kind breakdown lines
    lines = stripped.split("\n")
    kind_lines = [line for line in lines if re.match(r"    \w+: \d+", line)]
    
    # Should be sorted: dead_function (3), trace (2), vacuous_test (1)
    assert len(kind_lines) == 3
    assert "dead_function: 3" in kind_lines[0]
    assert "trace: 2" in kind_lines[1]
    assert "vacuous_test: 1" in kind_lines[2]


def test_format_terminal_no_kind_breakdown_when_empty():
    """Test that no kind breakdown appears when there are no findings."""
    scorecard = build_scorecard([], {"total_findings": 0, "diff_range": "HEAD"})

    output = format_terminal(scorecard)
    stripped = _strip_ansi(output)

    # Check that no line matches the kind breakdown pattern
    lines = stripped.split("\n")
    kind_pattern = re.compile(r"    \w+: \d+")
    for line in lines:
        assert not kind_pattern.match(line)


def test_format_json_finding_order_matches_scorecard():
    """Test that JSON output preserves the finding order from scorecard."""
    finding1: Finding = {
        "kind": "dead_function",
        "file": "src/a.py",
        "line": 10,
        "message": "low",
        "confidence": 0.3,
    }
    finding2: Finding = {
        "kind": "dead_function",
        "file": "src/b.py",
        "line": 20,
        "message": "high",
        "confidence": 0.9,
    }
    findings = [finding1, finding2]
    scorecard = build_scorecard(findings, {"total_findings": 2})

    json_output = format_json(scorecard)
    parsed = json.loads(json_output)

    # JSON findings should match scorecard findings order (sorted)
    assert len(parsed["findings"]) == 2
    assert parsed["findings"][0]["confidence"] == scorecard["findings"][0]["confidence"]
    assert parsed["findings"][1]["confidence"] == scorecard["findings"][1]["confidence"]
    assert parsed["findings"][0]["confidence"] == 0.9
    assert parsed["findings"][1]["confidence"] == 0.3


def test_format_json_has_no_ansi_codes():
    """Test that JSON output contains no ANSI escape codes."""
    finding: Finding = {
        "kind": "dead_function",
        "file": "src/auth.py",
        "line": 42,
        "message": "test",
        "confidence": 0.9,
    }
    scorecard = build_scorecard([finding], {"total_findings": 1, "diff_range": "HEAD"})

    output = format_json(scorecard)

    # Check that no ANSI escape sequences are present
    assert "\x1b[" not in output


# Made with Bob
