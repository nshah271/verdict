"""Coverage delta check.

Identifies newly added lines that are not exercised by tests. Uses pytest's
sys.settrace mechanism to track which specific lines are executed during test runs.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from verdict.diff import get_changed_files
from verdict.types import AddedFunction, Finding


class CoverageDeltaCheck:
    """Check for newly added lines with low test coverage."""

    name = "coverage_delta"
    kind = "dynamic"
    threshold = 0.5  # Below 50% coverage on new lines → finding

    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]:
        """Run line-level coverage tracking on added lines.

        Args:
            diff_root: Root directory of the diff (workspace root)
            added_functions: List of all added functions from the diff (unused)

        Returns:
            List of findings for files with low coverage on new lines
        """
        # Get changed files with added lines
        changed_files = get_changed_files(diff_range="HEAD", repo_root=diff_root)

        # Filter to Python files with added lines, skip test files
        targets: dict[str, list[int]] = {}
        for changed_file in changed_files:
            file_path = changed_file["path"]
            added_lines = changed_file["added_lines"]

            # Skip if not a Python file
            if not file_path.endswith(".py"):
                continue

            # Skip if no added lines
            if not added_lines:
                continue

            # Skip test files (path contains "tests/" or name starts with "test_")
            if "tests/" in file_path or Path(file_path).name.startswith("test_"):
                continue

            # Build absolute path and add to targets
            abs_path = os.path.realpath(Path(diff_root) / file_path)
            targets[abs_path] = added_lines

        # Early exit if no targets
        if not targets:
            return []

        # Extract first target file for error reporting
        first_target_file = next(
            (
                cf["path"]
                for cf in changed_files
                if cf["path"].endswith(".py")
                and cf["added_lines"]
                and "tests/" not in cf["path"]
                and not Path(cf["path"]).name.startswith("test_")
            ),
            "unknown",
        )

        # Create temp files for communication with plugin
        targets_file = None
        output_file = None

        try:
            # Write targets to temp file
            targets_file = tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".json"
            )
            json.dump({"files": targets}, targets_file)
            targets_file.close()

            # Create output file
            output_file = tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".json"
            )
            output_file.close()

            # Run pytest with coverage plugin
            env = os.environ.copy()
            env["VERDICT_COVERAGE_TARGETS"] = targets_file.name
            env["VERDICT_COVERAGE_OUTPUT"] = output_file.name

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-p", "verdict._coverage_plugin"],
                    cwd=diff_root,
                    env=env,
                    timeout=180,
                    capture_output=True,
                    text=True,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                return [
                    {
                        "kind": "coverage_not_run",
                        "file": first_target_file,
                        "line": 1,
                        "message": "coverage check timed out after 180 seconds",
                        "confidence": 0.0,
                    }
                ]
            except Exception as e:
                return [
                    {
                        "kind": "coverage_not_run",
                        "file": first_target_file,
                        "line": 1,
                        "message": f"coverage check failed: {type(e).__name__}",
                        "confidence": 0.0,
                    }
                ]

            # Process results based on exit code
            if exit_code == 5:
                # No tests collected
                return [
                    {
                        "kind": "coverage_not_run",
                        "file": first_target_file,
                        "line": 1,
                        "message": "coverage check skipped: no tests collected",
                        "confidence": 0.0,
                    }
                ]
            elif exit_code in (2, 3, 4):
                # pytest internal errors
                return [
                    {
                        "kind": "coverage_not_run",
                        "file": first_target_file,
                        "line": 1,
                        "message": f"coverage check failed: pytest exit code {exit_code}",
                        "confidence": 0.0,
                    }
                ]
            elif exit_code in (0, 1):
                # Tests ran (0 = success, 1 = test failures)
                # Read coverage results
                try:
                    with open(output_file.name, "r") as f:
                        output_data = json.load(f)
                    hits_dict = output_data.get("hits", {})
                except (FileNotFoundError, json.JSONDecodeError):
                    hits_dict = {}

                # Build reverse mapping from absolute path to relative path
                abs_to_rel: dict[str, str] = {}
                for changed_file in changed_files:
                    file_path = changed_file["path"]
                    if file_path.endswith(".py") and changed_file["added_lines"]:
                        if "tests/" not in file_path and not Path(file_path).name.startswith("test_"):
                            abs_path = os.path.realpath(Path(diff_root) / file_path)
                            abs_to_rel[abs_path] = file_path

                # Calculate coverage per file and generate findings
                findings: list[Finding] = []
                for abs_path, target_lines in targets.items():
                    hit_lines = set(hits_dict.get(abs_path, []))
                    total = len(target_lines)
                    hit_count = len([line for line in target_lines if line in hit_lines])
                    pct = hit_count / total if total > 0 else 0.0

                    # Emit finding if coverage is below threshold
                    if pct < self.threshold:
                        rel_path = abs_to_rel.get(abs_path, abs_path)
                        findings.append({
                            "kind": "low_coverage_delta",
                            "file": rel_path,
                            "line": 1,
                            "message": f"of {total} new lines, {hit_count} ({pct:.0%}) were exercised by tests",
                            "confidence": round(1.0 - pct, 2),
                        })

                return findings
            else:
                # Unexpected exit code
                return [
                    {
                        "kind": "coverage_not_run",
                        "file": first_target_file,
                        "line": 1,
                        "message": f"coverage check failed: unexpected exit code {exit_code}",
                        "confidence": 0.0,
                    }
                ]

        finally:
            # Clean up temp files
            if targets_file:
                try:
                    os.unlink(targets_file.name)
                except OSError:
                    pass
            if output_file:
                try:
                    os.unlink(output_file.name)
                except OSError:
                    pass


# Export check instance for CLI auto-discovery
check = CoverageDeltaCheck()

# Made with Bob