"""Hallucinated API check.

Detects calls to non-existent methods and attributes on objects, such as:
- requests.get_json() instead of .json()
- my_list.add(x) instead of .append(x)

Uses Jedi for static type inference to validate attribute access.
"""

import ast
from collections import defaultdict
from pathlib import Path

from verdict.types import AddedFunction, Finding

# Try to import jedi, but gracefully handle if not installed
try:
    import jedi

    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False


def _group_functions_by_file(
    added_functions: list[AddedFunction],
) -> dict[str, list[AddedFunction]]:
    """Group added functions by their file path.

    Args:
        added_functions: List of all added functions

    Returns:
        Dictionary mapping file paths to lists of functions in that file
    """
    grouped: dict[str, list[AddedFunction]] = defaultdict(list)
    for func in added_functions:
        grouped[func["file"]].append(func)
    return dict(grouped)


def _collect_attributes_in_range(
    tree: ast.AST, line_ranges: list[tuple[int, int]]
) -> list[tuple[ast.Attribute, int, int]]:
    """Collect all Attribute nodes within specified line ranges.

    Args:
        tree: Parsed AST of the file
        line_ranges: List of (start_line, end_line) tuples for added functions

    Returns:
        List of (attribute_node, line, column) tuples for attributes in range
    """
    attributes = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue

        # Skip dunder attributes
        if node.attr.startswith("__"):
            continue

        # Check if this attribute is within any of the line ranges
        node_line = node.lineno
        for start_line, end_line in line_ranges:
            if start_line <= node_line <= end_line:
                # Store the attribute node with its position
                attributes.append((node, node_line, node.col_offset))
                break

    return attributes


def _should_suppress(receiver_names: list, attr_name: str) -> bool:
    """Check if an attribute should be suppressed from checking.

    Suppression cases:
    - No receiver type inferred (unresolved)
    - Receiver is Any, object, or NoneType
    - Attribute name starts with __ (dunder)

    Args:
        receiver_names: List of Jedi Name objects for the receiver
        attr_name: Name of the attribute being accessed

    Returns:
        True if this attribute should be suppressed
    """
    # Unresolved receiver
    if not receiver_names:
        return True

    # Dunder attributes
    if attr_name.startswith("__"):
        return True

    # Check for suppressed type names
    suppressed_types = {"Any", "object", "NoneType"}
    for name in receiver_names:
        try:
            type_name = name.name
            if type_name in suppressed_types:
                return True
        except Exception:
            # If we can't get the name, continue checking others
            continue

    return False


def _calculate_confidence(receiver_name, diff_root: str) -> float:
    """Calculate confidence score based on receiver type origin.

    Args:
        receiver_name: Jedi Name object for the receiver type
        diff_root: Root directory of the diff

    Returns:
        Confidence score: 0.9 (first-party), 0.85 (third-party), 0.75 (builtin)
    """
    try:
        module_path = receiver_name.module_path

        # Builtin types (no module path)
        if module_path is None:
            return 0.75

        # First-party (inside diff_root)
        try:
            if Path(module_path).is_relative_to(diff_root):
                return 0.9
        except (ValueError, TypeError):
            pass

        # Third-party (outside diff_root)
        return 0.85

    except Exception:
        # Default to lowest confidence if we can't determine
        return 0.6


def _get_receiver_type_name(receiver_names: list) -> str:
    """Extract a readable type name from receiver inferences.

    Args:
        receiver_names: List of Jedi Name objects

    Returns:
        String representation of the receiver type
    """
    if not receiver_names:
        return "unknown"

    try:
        # Use the first inferred type
        return receiver_names[0].name
    except Exception:
        return "unknown"


class HallucinatedApiCheck:
    """Check for hallucinated method and attribute calls."""

    name = "hallucinated_api"
    kind = "static"

    def run(self, diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]:
        """Run hallucinated API detection on added functions.

        Args:
            diff_root: Root directory of the diff (workspace root)
            added_functions: List of all added functions from the diff

        Returns:
            List of findings for hallucinated API calls
        """
        # If Jedi is not available, return empty list
        if not JEDI_AVAILABLE:
            return []

        findings: list[Finding] = []

        # Group functions by file for efficient processing
        grouped = _group_functions_by_file(added_functions)

        for file_path, functions in grouped.items():
            try:
                # Read and parse the source file once
                source_path = Path(diff_root) / file_path
                content = source_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(source_path))

                # Create Jedi Script with project context for cross-file imports
                try:
                    project = jedi.Project(diff_root)
                    script = jedi.Script(content, path=str(source_path), project=project)
                except Exception:
                    # If Jedi setup fails, skip this file
                    continue

                # Collect line ranges for all added functions in this file
                line_ranges = [(f["line"], f["end_line"]) for f in functions]

                # Collect all Attribute nodes within added function ranges
                attributes = _collect_attributes_in_range(tree, line_ranges)

                # Check each attribute
                for attr_node, line, _col in attributes:
                    try:
                        attr_name = attr_node.attr

                        # Resolve receiver type at the end of the receiver expression
                        receiver_line = attr_node.value.end_lineno
                        receiver_col = attr_node.value.end_col_offset

                        # Jedi uses 1-based line numbers, 0-based columns
                        receiver_names = script.infer(receiver_line, receiver_col)

                        # Apply suppression filter
                        if _should_suppress(receiver_names, attr_name):
                            continue

                        # Calculate the column position of the attribute name itself
                        # The attribute ends at end_col_offset, so subtract its length
                        attr_col = attr_node.end_col_offset - len(attr_name)

                        # Try to infer the attribute itself
                        # If it resolves to something, the attribute exists
                        attr_inferences = script.infer(attr_node.end_lineno, attr_col)
                        if attr_inferences:
                            continue  # attribute exists, no finding

                        # Attribute doesn't exist, emit a finding
                        receiver_type = _get_receiver_type_name(receiver_names)
                        confidence = (
                            max(_calculate_confidence(name, diff_root) for name in receiver_names)
                            if receiver_names
                            else 0.6
                        )

                        findings.append(
                            {
                                "kind": "hallucinated_api",
                                "file": file_path,
                                "line": line,
                                "message": f"no attribute '{attr_name}' on {receiver_type}",
                                "confidence": confidence,
                            }
                        )

                    except Exception:
                        # Swallow per-attribute exceptions and continue
                        continue

            except (FileNotFoundError, PermissionError, SyntaxError, UnicodeDecodeError):
                # Skip files that can't be read or parsed
                continue
            except Exception:
                # Catch any other unexpected errors and continue
                continue

        return findings


# Export check instance for CLI auto-discovery
check = HallucinatedApiCheck()

# Made with Bob
