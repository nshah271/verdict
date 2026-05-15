"""Extract and analyze functions from Python AST."""

import ast
from pathlib import Path, PurePosixPath

from verdict.types import AddedFunction, ChangedFile


def get_added_functions(
    changed_files: list[ChangedFile], repo_root: str = "."
) -> list[AddedFunction]:
    """Extract added functions/classes from Python files in the diff."""
    added_functions: list[AddedFunction] = []
    repo_path = Path(repo_root)

    for changed_file in changed_files:
        # Only process Python files
        if not changed_file["path"].endswith(".py"):
            continue

        # Skip if no added lines
        if not changed_file["added_lines"]:
            continue

        file_path = repo_path / changed_file["path"]
        
        # Read and parse the file
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (OSError, SyntaxError):
            # Skip files that can't be read or parsed
            continue

        # Determine if this is a test file. Use path parts and the filename
        # so a directory called "test_foo/" doesn't get flagged just because
        # the path string starts with "test_".
        path_obj = PurePosixPath(changed_file["path"])
        is_test_file = (
            "tests" in path_obj.parts
            or path_obj.name.startswith("test_")
            or path_obj.name.endswith("_test.py")
        )

        # Walk the AST and find added functions/classes
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            # Check if this node was added (check if any line of the node is in added_lines)
            if node.lineno not in changed_file["added_lines"]:
                continue

            # Determine if this specific function is a test
            # A function is a test if its name starts with test_ OR if it's in a test file
            is_test = node.name.startswith("test_") or is_test_file

            # Extract decorators
            decorators = [_extract_decorator_name(dec) for dec in node.decorator_list]

            # Calculate end line
            end_line = node.end_lineno if node.end_lineno is not None else node.lineno

            added_functions.append(
                AddedFunction(
                    file=changed_file["path"],
                    name=node.name,
                    line=node.lineno,
                    end_line=end_line,
                    is_test=is_test,
                    decorators=decorators,
                )
            )

    return added_functions


def get_added_tests(added_functions: list[AddedFunction]) -> list[AddedFunction]:
    """Filter added functions to only test functions."""
    return [f for f in added_functions if f["is_test"]]


def _extract_decorator_name(decorator_node: ast.expr) -> str:
    """Convert decorator AST node to dotted string (e.g., 'pytest.fixture')."""
    # Handle @decorator (Name node)
    if isinstance(decorator_node, ast.Name):
        return decorator_node.id

    # Handle @module.decorator or @module.submodule.decorator (Attribute node)
    if isinstance(decorator_node, ast.Attribute):
        parts: list[str] = []
        current: ast.expr = decorator_node
        
        # Walk backwards through the attribute chain
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        # Add the base name
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        # Reverse to get correct order
        return ".".join(reversed(parts))

    # Handle @decorator(...) (Call node) - extract just the function name
    if isinstance(decorator_node, ast.Call):
        return _extract_decorator_name(decorator_node.func)

    # Fallback: PEP 614 allows arbitrary expressions as decorators. ast.unparse
    # gives a readable source form for anything we don't explicitly handle.
    try:
        return ast.unparse(decorator_node)
    except Exception:
        return "unknown"

# Made with Bob
