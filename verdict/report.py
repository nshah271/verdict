"""Scorecard construction and formatting for verdict."""

import json
from collections import Counter

import click

from verdict.types import Finding, Scorecard, VerdictLevel


# ============================================================================
# Known weaknesses of the current scoring rule, post-hackathon work
# ============================================================================
#
# The current build_scorecard rule (LIED if any finding.confidence > 0.8,
# SUSPICIOUS if any findings exist, else PASS) is brittle:
#
#   1. Cliff at 0.8. A 0.80 finding gives SUSPICIOUS, a 0.81 gives LIED.
#      The threshold is arbitrary and unstable to small confidence tweaks.
#   2. No aggregation. Ten findings at 0.7 each stay SUSPICIOUS, one
#      finding at 0.81 jumps straight to LIED. Many independent weak
#      signals should beat one moderate signal, not the other way around.
#   3. Confidences are uncalibrated guesses, not probabilities. "0.85"
#      was picked by a check author's intuition. Each check assigned its
#      numbers independently, so they are not directly comparable.
#   4. No quorum requirement. One buggy check emitting confidence > 0.8
#      escalates the whole verdict to LIED with no corroboration.
#   5. No context. "New function never executed" is much weaker evidence
#      if the project has no tests at all than if it has a robust suite.
#
# Proposed robust replacement (sketch for if we get time):
#
#   a. Per-check declared priors. Each check exposes two numbers:
#        precision_prior: P(actual lie | this check fires)
#        recall_prior:    P(this check fires | actual lie)
#      Both tuned against a small labeled fixture corpus, not picked
#      by feel. Lives on the check class alongside name and kind.
#
#   b. Probabilistic combination. Treat each finding's calibrated
#      confidence as a Bernoulli signal. Combine across distinct
#      (file, function) sites via 1 - product(1 - p_i) since those
#      are roughly independent. Within a single site, use max (not
#      product) since multiple checks firing on the same function
#      are correlated, not independent.
#
#   c. Corroboration bonus. When two or more checks fire on the
#      same (file, function_name), boost the aggregate score for
#      that function above the simple combination above.
#      Independent agreement is the strongest signal verdict has.
#
#   d. Verdict bands on the aggregate score instead of a hard cliff:
#        PASS:        aggregate < 0.30
#        SUSPICIOUS:  0.30 <= aggregate < 0.70
#        LIED:        aggregate >= 0.70
#      Soft enough that small confidence tweaks do not flip the
#      verdict.
#
#   e. Context modifiers. If trace_not_run fired (no tests, broken
#      collection), suppress never_executed findings since they are
#      expected. If the diff is docs / config only, suppress
#      code-quality findings. These are multipliers on the per-site
#      score, not separate booleans.
#
#   f. Calibration loop. Build a small labeled corpus of
#      agent-generated diffs (known lies and known fine cases) and
#      fit per-check priors via logistic regression treating each
#      check as a feature. This is the part that turns the priors
#      from vibes into actual probabilities.
#
# Changing this means coordinating with every existing check
# (vacuous_tests, phantom_files, dead_functions, trace) since they
# all assigned confidences against the current rule.
# ============================================================================


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

    # Sort findings: confidence descending, then kind, file, line ascending
    sorted_findings = sorted(
        findings,
        key=lambda f: (-f["confidence"], f["kind"], f["file"], f["line"]),
    )

    return {
        "verdict": verdict,
        "findings": sorted_findings,
        "summary": summary,
    }


def format_terminal(scorecard: Scorecard) -> str:
    """Format scorecard for terminal output with colors and kind breakdown.

    Layout:
    - Verdict line: "Verdict: LIED" / "SUSPICIOUS" / "PASS" (colored)
    - Summary stats from scorecard["summary"] with per-kind breakdown
    - One line per finding: "file:line - message (confidence: X.XX)" (confidence colored)

    Args:
        scorecard: Scorecard dict with verdict, findings, summary

    Returns:
        Multi-line string for terminal display
    """
    lines = []

    # Verdict line with colored verdict word
    verdict = scorecard["verdict"]
    if verdict == "LIED":
        colored_verdict = click.style("LIED", fg="red", bold=True)
    elif verdict == "SUSPICIOUS":
        colored_verdict = click.style("SUSPICIOUS", fg="yellow", bold=True)
    else:  # PASS
        colored_verdict = click.style("PASS", fg="green", bold=True)
    lines.append(f"Verdict: {colored_verdict}")
    lines.append("")

    # Summary section
    summary = scorecard["summary"]
    lines.append("Summary:")
    lines.append(f"  Total findings: {summary.get('total_findings', 0)}")
    
    # Add per-kind breakdown if findings exist
    findings = scorecard["findings"]
    if findings:
        kind_counts = Counter(f["kind"] for f in findings)
        # Sort by count descending, then alphabetically
        sorted_kinds = sorted(kind_counts.items(), key=lambda x: (-x[1], x[0]))
        for kind, count in sorted_kinds:
            lines.append(f"    {kind}: {count}")
    
    if "checks_run" in summary:
        lines.append(f"  Checks run: {summary['checks_run']}")
    if "checks_failed" in summary:
        lines.append(f"  Checks failed: {summary['checks_failed']}")
    lines.append(f"  Diff range: {summary.get('diff_range', 'HEAD')}")
    lines.append("")

    # Findings section with colored confidence
    if findings:
        lines.append("Findings:")
        for finding in findings:
            file_loc = f"{finding['file']}:{finding['line']}"
            conf_value = finding["confidence"]
            conf_text = f"(confidence: {conf_value:.2f})"
            
            # Color confidence by band
            if conf_value > 0.8:
                colored_conf = click.style(conf_text, fg="red")
            elif conf_value >= 0.5:
                colored_conf = click.style(conf_text, fg="yellow")
            else:
                colored_conf = click.style(conf_text, fg="green")
            
            lines.append(f"  {file_loc} - {finding['message']} {colored_conf}")
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
