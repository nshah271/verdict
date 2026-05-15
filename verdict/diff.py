"""Parse git diffs into structured ChangedFile records."""

import re
import subprocess

from verdict.types import ChangedFile


def get_changed_files(diff_range: str = "HEAD", repo_root: str = ".") -> list[ChangedFile]:
    """Parse git diff output into structured ChangedFile records."""
    result = subprocess.run(
        ["git", "diff", "--unified=0", diff_range],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return _parse_unified_diff(result.stdout)


def _parse_unified_diff(text: str) -> list[ChangedFile]:
    """Parse unified diff text into ChangedFile records (testable without git)."""
    files: dict[str, ChangedFile] = {}
    current_file: str = ""
    current_added_line: int = 0
    current_removed_line: int = 0

    # Regex patterns
    file_header_pattern = re.compile(r"^diff --git a/.+ b/(.+)$")
    binary_pattern = re.compile(r"^Binary files .+ differ$")
    hunk_header_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for line in text.splitlines():
        # Check for binary file marker
        if binary_pattern.match(line):
            # Skip binary files - remove from tracking if already added
            if current_file in files:
                del files[current_file]
            current_file = ""
            continue

        # Check for file header
        file_match = file_header_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            if current_file not in files:
                files[current_file] = ChangedFile(
                    path=current_file,
                    added_lines=[],
                    removed_lines=[],
                )
            continue

        # Check for hunk header
        hunk_match = hunk_header_pattern.match(line)
        if hunk_match and current_file:
            current_removed_line = int(hunk_match.group(1))
            current_added_line = int(hunk_match.group(2))
            continue

        # Process diff lines (skip file markers +++ and ---)
        if current_file and line.startswith("+") and not line.startswith("+++"):
            files[current_file]["added_lines"].append(current_added_line)
            current_added_line += 1
        elif current_file and line.startswith("-") and not line.startswith("---"):
            files[current_file]["removed_lines"].append(current_removed_line)
            current_removed_line += 1

    return list(files.values())

# Made with Bob
