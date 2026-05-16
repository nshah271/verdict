"""Phantom file detection check.

Identifies files that appear in the diff as added or are claimed in transcripts
but don't actually exist on disk. This catches cases where an AI agent claims
to have created a file but the file is missing.

Two signal sources:
1. Files referenced in added_functions that don't exist on disk
2. Files claimed in transcript patterns that don't exist on disk
"""

import re
from pathlib import Path

from verdict.types import AddedFunction, Check, Finding


def _extract_paths_from_transcript(transcript: str) -> set[str]:
    """Extract file paths from transcript using common agent patterns.
    
    Looks for patterns like:
    - "created file: path/to/file.py"
    - "created path/to/file.py"
    - "wrote path/to/file.py"
    
    Args:
        transcript: The agent's transcript text
        
    Returns:
        Set of file paths mentioned in creation claims
    """
    paths = set()
    
    # Pattern 1: "created file: <path>"
    pattern1 = r'created\s+file:\s+([^\s\n]+)'
    paths.update(re.findall(pattern1, transcript, re.IGNORECASE))
    
    # Pattern 2: "created <path>" (where path looks like a file)
    pattern2 = r'created\s+([^\s\n]+\.[a-zA-Z0-9]+)'
    paths.update(re.findall(pattern2, transcript, re.IGNORECASE))
    
    # Pattern 3: "wrote <path>"
    pattern3 = r'wrote\s+([^\s\n]+\.[a-zA-Z0-9]+)'
    paths.update(re.findall(pattern3, transcript, re.IGNORECASE))
    
    # Pattern 4: "writing <path>"
    pattern4 = r'writing\s+([^\s\n]+\.[a-zA-Z0-9]+)'
    paths.update(re.findall(pattern4, transcript, re.IGNORECASE))
    
    # Pattern 5: "added file: <path>"
    pattern5 = r'added\s+file:\s+([^\s\n]+)'
    paths.update(re.findall(pattern5, transcript, re.IGNORECASE))
    
    # Pattern 6: "added <path>" (where path looks like a file)
    pattern6 = r'added\s+([^\s\n]+\.[a-zA-Z0-9]+)'
    paths.update(re.findall(pattern6, transcript, re.IGNORECASE))
    
    return paths


class PhantomFileCheck:
    """Check for files claimed to exist but missing from disk."""
    
    name = "phantom_files"
    kind = "static"
    
    def __init__(self, transcript: str | None = None):
        """Initialize the phantom file check.
        
        Args:
            transcript: Optional agent transcript to extract claimed file paths from
        """
        self.transcript = transcript
    
    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]:
        """Run phantom file detection.
        
        Args:
            diff_root: Root directory of the diff (workspace root)
            added_functions: List of all added functions from the diff
            
        Returns:
            List of findings for files that don't exist on disk
        """
        findings: list[Finding] = []
        diff_root_path = Path(diff_root)
        
        # Signal source 1: Files from added_functions
        # Extract unique file paths from added functions
        function_files = {f["file"] for f in added_functions}
        
        for file_path in function_files:
            try:
                full_path = diff_root_path / file_path
                if not full_path.exists():
                    findings.append({
                        "kind": "phantom_file",
                        "file": file_path,
                        "line": 1,  # Use line 1 for file-level findings
                        "message": "file referenced in diff does not exist on disk",
                        "confidence": 1.0,
                    })
            except (OSError, ValueError):
                # Skip paths that raise unexpected errors (e.g., invalid path chars)
                continue
        
        # Signal source 2: Files from transcript (if provided)
        if self.transcript:
            transcript_paths = _extract_paths_from_transcript(self.transcript)
            
            for file_path in transcript_paths:
                try:
                    # Normalize path separators for cross-platform compatibility
                    normalized_path = file_path.replace('\\', '/')
                    full_path = diff_root_path / normalized_path
                    
                    if not full_path.exists():
                        findings.append({
                            "kind": "phantom_file",
                            "file": normalized_path,
                            "line": 1,
                            "message": "file claimed in transcript does not exist on disk",
                            "confidence": 0.9,
                        })
                except (OSError, ValueError):
                    # Skip paths that raise unexpected errors
                    continue
        
        return findings


# Export check instance for CLI auto-discovery
check = PhantomFileCheck()

# Made with Bob
