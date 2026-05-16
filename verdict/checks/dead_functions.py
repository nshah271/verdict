"""Detect functions added in a diff that are never referenced in the repo."""

import ast
from pathlib import Path

from verdict.types import AddedFunction, Finding


class DeadFunctionCheck:
    """Check for added functions that are never referenced anywhere in the repo."""

    name = "dead_function"

    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]:
        """Find added functions with no references in the repo."""
        # Step 1: Filter candidates - exclude entry points
        candidates = [f for f in added_functions if not _is_excluded(f)]

        if not candidates:
            return []

        # Step 2: Collect all referenced names in the repo (walk once)
        references, all_exports, init_imports = _collect_references(diff_root)

        # Step 3-5: Check each candidate for external references
        findings: list[Finding] = []
        for func in candidates:
            func_name = func["name"]

            # Check if name is in __all__ or imported in __init__.py
            if _is_in_all_or_init(func_name, func["file"], diff_root, all_exports, init_imports):
                continue

            # Get all references to this name
            ref_locations = references.get(func_name, set())

            # Step 3: Check for references outside function body
            if not _has_external_reference(func, ref_locations):
                findings.append(
                    Finding(
                        kind="dead_function",
                        file=func["file"],
                        line=func["line"],
                        message=f"{func_name}() is never referenced in the repo",
                        confidence=0.9,
                    )
                )

        return findings


def _has_external_reference(
    func: AddedFunction, ref_locations: set[tuple[str, int]]
) -> bool:
    """Check if function has any references outside its own body.
    
    Returns True if there's at least one reference that is either:
    - In a different file, or
    - In the same file but outside the function's line range
    """
    return any(
        ref_file != func["file"]
        or ref_line < func["line"]
        or ref_line > func["end_line"]
        for ref_file, ref_line in ref_locations
    )


def _is_excluded(func: AddedFunction) -> bool:
    """Check if function should be excluded from dead code detection."""
    # Exclude test functions (invoked by test runner)
    if func["is_test"]:
        return True

    # Exclude dunder methods (called implicitly by Python)
    if func["name"].startswith("__") and func["name"].endswith("__"):
        return True

    # Check decorators for entry points
    for decorator in func["decorators"]:
        # Pytest fixtures
        if decorator == "pytest.fixture":
            return True
        # Flask/FastAPI route handlers
        if decorator == "app.route" or decorator.endswith(('.get', '.post', '.put', '.delete', '.patch', '.route')) or 'router' in decorator:
            return True
        # Click CLI commands
        if decorator in ("click.command", "click.group"):
            return True

    return False


def _collect_references(repo_root: str) -> tuple[dict[str, set[tuple[str, int]]], dict[str, set[str]], dict[str, set[str]]]:
    """Walk all Python files and collect referenced names with locations and __all__ exports.
    
    Returns:
        A tuple of (references, all_exports, init_imports) where:
        - references: dict mapping name -> set of (file_path, line_number) tuples
        - all_exports: dict mapping file_path -> set of names in __all__
        - init_imports: dict mapping __init__.py file_path -> set of imported names
    """
    references: dict[str, set[tuple[str, int]]] = {}
    all_exports: dict[str, set[str]] = {}
    init_imports: dict[str, set[str]] = {}
    repo_path = Path(repo_root)

    # Walk all .py files
    for py_file in repo_path.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (OSError, SyntaxError):
            # Skip files that can't be read or parsed
            continue

        # Get relative path for consistent comparison
        try:
            rel_path = str(py_file.relative_to(repo_path)).replace('\\', '/')
        except ValueError:
            # File is outside repo_root, use absolute path
            rel_path = str(py_file)

        # Walk AST and collect name references, __all__ exports, and __init__.py imports
        for node in ast.walk(tree):
            name: str | None = None
            line: int | None = None

            # ast.Name covers: func, func(), x = func, [func], @func
            if isinstance(node, ast.Name):
                name = node.id
                line = node.lineno
            # ast.Attribute covers: module.func, obj.method()
            elif isinstance(node, ast.Attribute):
                name = node.attr
                line = node.lineno
            # Check for __all__ assignments
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            exported_names = set()
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    exported_names.add(elt.value)
                            if exported_names:
                                all_exports[rel_path] = exported_names
            # Collect imports in __init__.py files
            elif rel_path.endswith("__init__.py"):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != '*':
                            if rel_path not in init_imports:
                                init_imports[rel_path] = set()
                            init_imports[rel_path].add(alias.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if rel_path not in init_imports:
                            init_imports[rel_path] = set()
                        init_imports[rel_path].add(alias.name)

            if name and line:
                if name not in references:
                    references[name] = set()
                references[name].add((rel_path, line))

    return references, all_exports, init_imports


def _is_in_all_or_init(name: str, file_path: str, repo_root: str, all_exports: dict[str, set[str]], init_imports: dict[str, set[str]]) -> bool:
    """Check if name is exported via __all__ or imported in __init__.py.
    
    Args:
        name: The function name to check
        file_path: Relative path to the file containing the function
        repo_root: Root directory of the repository
        all_exports: Pre-collected __all__ exports from all files
        init_imports: Pre-collected imports from __init__.py files
    """
    # Check __all__ in the function's own module using cached data
    if file_path in all_exports and name in all_exports[file_path]:
        return True

    # Check if imported in any __init__.py file using cached data
    for init_path, imported_names in init_imports.items():
        if name in imported_names:
            return True

    return False

# Made with Bob
