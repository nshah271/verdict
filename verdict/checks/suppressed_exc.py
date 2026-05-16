"""Detect try/except blocks that silently swallow exceptions."""

import ast
from pathlib import Path

from verdict.diff import get_changed_files
from verdict.types import AddedFunction, ChangedFile, Finding

# Logger method names that indicate logging-only exception handling
_LOGGER_METHODS = frozenset({
    "debug", "info", "warning", "warn", "error",
    "critical", "exception", "log"
})

# Broad exception types that catch almost everything
_BROAD_EXCEPTIONS = frozenset({"Exception", "BaseException"})


class SuppressedExceptionCheck:
    """Check for exception handlers that silently swallow errors."""

    name = "suppressed_exception"
    kind = "static"

    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]:
        """Find exception handlers that suppress errors in added code."""
        changed_files = get_changed_files("HEAD", repo_root=diff_root)
        return find_suppressed_exceptions(changed_files, diff_root)


def find_suppressed_exceptions(
    changed_files: list[ChangedFile], repo_root: str
) -> list[Finding]:
    """Analyze changed files for suppressed exception handlers.
    
    Args:
        changed_files: List of files changed in the diff with line numbers
        repo_root: Root directory of the repository
        
    Returns:
        List of findings for suppressed exception handlers
    """
    findings: list[Finding] = []
    repo_path = Path(repo_root)

    for cf in changed_files:
        # Only process Python files
        if not cf["path"].endswith(".py"):
            continue

        # Skip if no added lines
        if not cf["added_lines"]:
            continue

        file_path = repo_path / cf["path"]

        # Read and parse the file
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (OSError, SyntaxError):
            # Skip files that can't be read or parsed
            continue

        # Convert added_lines to set for O(1) lookup
        added_lines_set = set(cf["added_lines"])

        # Walk AST and find Try nodes in added lines
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue

            # Check if this try block was added
            if node.lineno not in added_lines_set:
                continue

            # Calculate try body size for confidence boost
            try_body_lines = _get_try_body_lines(node)

            # Analyze each exception handler
            for handler in node.handlers:
                suppression_info = _is_suppressed_handler(handler)
                if not suppression_info:
                    continue

                body_desc, is_suppressed = suppression_info
                if not is_suppressed:
                    continue

                # Classify exception type and get base confidence
                exc_type_name, base_confidence = _classify_exception_type(handler)

                # Boost confidence for long try bodies
                confidence = base_confidence
                if try_body_lines > 10:
                    confidence = min(0.95, confidence + 0.05)

                # Format exception type for message
                if exc_type_name:
                    exc_display = f"except {exc_type_name}"
                else:
                    exc_display = "except"

                findings.append(
                    Finding(
                        kind="suppressed_exception",
                        file=cf["path"],
                        line=handler.lineno,
                        message=f"{exc_display}: body is `{body_desc}` — exception silently swallowed",
                        confidence=confidence,
                    )
                )

    return findings


def _is_suppressed_handler(handler: ast.ExceptHandler) -> tuple[str, bool] | None:
    """Check if exception handler suppresses errors.
    
    Returns:
        Tuple of (body_description, is_suppressed) if handler has exactly 1 statement,
        None otherwise.
        
    A handler is suppressed if its body contains exactly 1 statement that is:
    - pass
    - ... (Ellipsis)
    - continue
    - Single bare logger call
    
    NOT suppressed if body contains:
    - raise (re-raises exception)
    - return (returns from function)
    - Multiple statements (doing real work)
    """
    # Must have exactly 1 statement
    if len(handler.body) != 1:
        return None

    stmt = handler.body[0]

    # Check for pass
    if isinstance(stmt, ast.Pass):
        return ("pass", True)

    # Check for raise (NOT suppressed)
    if isinstance(stmt, ast.Raise):
        return ("raise", False)

    # Check for return (NOT suppressed)
    if isinstance(stmt, ast.Return):
        return ("return", False)

    # Check for continue
    if isinstance(stmt, ast.Continue):
        return ("continue", True)

    # Check for expression statements (could be ... or logger call)
    if isinstance(stmt, ast.Expr):
        # Check for Ellipsis (...)
        if isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
            return ("...", True)

        # Check for bare logger call
        if isinstance(stmt.value, ast.Call):
            if _is_logger_call(stmt.value):
                # Extract logger method name for message
                if isinstance(stmt.value.func, ast.Attribute):
                    method_name = stmt.value.func.attr
                    return (f"logger.{method_name}(...)", True)

    return None


def _is_logger_call(call_node: ast.Call) -> bool:
    """Check if a Call node is a bare logger method call.
    
    Matches patterns like:
    - logger.error(...)
    - logging.error(...)
    - self.logger.error(...)
    """
    # Must be an attribute call (e.g., obj.method())
    if not isinstance(call_node.func, ast.Attribute):
        return False

    # Check if attribute name is a logger method
    return call_node.func.attr in _LOGGER_METHODS


def _classify_exception_type(handler: ast.ExceptHandler) -> tuple[str, float]:
    """Classify exception type and return base confidence.
    
    Returns:
        Tuple of (type_name, base_confidence)
        
    Confidence levels:
    - Bare except: 0.9
    - Exception/BaseException: 0.85
    - Narrow typed exception: 0.5
    """
    # Bare except (no type specified)
    if handler.type is None:
        return ("", 0.9)

    # Get exception type name
    try:
        type_name = ast.unparse(handler.type)
    except Exception:
        type_name = "Exception"

    # Check for broad exception types
    if type_name in _BROAD_EXCEPTIONS:
        return (type_name, 0.85)

    # Narrow exception type
    return (type_name, 0.5)


def _get_try_body_lines(try_node: ast.Try) -> int:
    """Calculate number of lines spanned by try body.
    
    Returns:
        Number of lines in the try body, or 0 if cannot determine.
    """
    if not try_node.body:
        return 0

    # Get the last statement in the try body
    last_stmt = try_node.body[-1]

    # If we have end_lineno, calculate span
    if hasattr(last_stmt, "end_lineno") and last_stmt.end_lineno is not None:
        return last_stmt.end_lineno - try_node.lineno

    # Fallback: count statements as approximation
    return len(try_node.body)


# Module-level check instance for auto-discovery
check = SuppressedExceptionCheck()

# Made with Bob
