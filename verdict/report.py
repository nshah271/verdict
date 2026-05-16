"""Scorecard construction and formatting for verdict."""

import json

from verdict.types import Finding, Scorecard, VerdictLevel


def build_scorecard(findings: list[Finding], summary: dict) -> Scorecard:
    """Build scorecard from findings list.

    Rules:
    - LIED if any finding.confidence > 0.8
    - SUSPICIOUS if findings is non-empty
    - PASS otherwise

    Args:
        findings: List of Finding dicts
        summary: Dict with metadata (total_findings, static_only, etc.)

    Returns:
        Scorecard with verdict, findings, summary
    """
    # Determine verdict based on confidence thresholds
    verdict: VerdictLevel = "PASS"
    if findings:
        verdict = "SUSPICIOUS"
        if any(f["confidence"] > 0.8 for f in findings):
            verdict = "LIED"

    return {
        "verdict": verdict,
        "findings": findings,
        "summary": summary,
    }


def format_terminal(scorecard: Scorecard) -> str:
    """Format scorecard for terminal output (plain text, no colors yet).

    Layout:
    - Verdict line: "Verdict: LIED" / "SUSPICIOUS" / "PASS"
    - Summary stats from scorecard["summary"]
    - One line per finding: "file:line - message (confidence: X.XX)"

    Args:
        scorecard: Scorecard dict with verdict, findings, summary

    Returns:
        Multi-line string for terminal display
    """
    lines = []

    # Verdict line
    lines.append(f"Verdict: {scorecard['verdict']}")
    lines.append("")

    # Summary section
    summary = scorecard["summary"]
    lines.append("Summary:")
    lines.append(f"  Total findings: {summary.get('total_findings', 0)}")
    if "checks_run" in summary:
        lines.append(f"  Checks run: {summary['checks_run']}")
    if "checks_failed" in summary:
        lines.append(f"  Checks failed: {summary['checks_failed']}")
    lines.append(f"  Diff range: {summary.get('diff_range', 'HEAD')}")
    lines.append("")

    # Findings section
    if scorecard["findings"]:
        lines.append("Findings:")
        for finding in scorecard["findings"]:
            file_loc = f"{finding['file']}:{finding['line']}"
            confidence = f"(confidence: {finding['confidence']:.2f})"
            lines.append(f"  {file_loc} - {finding['message']} {confidence}")
    else:
        lines.append("No findings.")

    return "\n".join(lines)


def format_json(scorecard: Scorecard) -> str:
    """Format scorecard as JSON with deterministic key order.

    Uses json.dumps(scorecard, indent=2, sort_keys=True)
    for stable output (CI diffs, screenshots).

    Args:
        scorecard: Scorecard dict

    Returns:
        JSON string
    """
    return json.dumps(scorecard, indent=2, sort_keys=True)


# Made with Bob
