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


# Jedi systematically resolves some receivers to a base class that's
# narrower than the real runtime type. The classic case is pathlib: any
# Path / str expression returns PurePath even though the operands are
# Path, so calls like file_path.read_text() infer as missing. Real code
# almost always means Path. When we see Jedi report one of these
# "lazy base" types, probe the upgrade target before firing.
#
# Each value names the class to probe instead. Add new entries when a
# similar systematic under-reporting shows up in another library.
_PURE_PATH_NAMES = {"PurePath", "PurePosixPath", "PureWindowsPath"}


def _upgrade_target(full_name: str) -> str | None:
    """Map a Jedi-reported type to the likely-real subclass, if any."""
    if not full_name:
        return None
    # pathlib in Python 3.13+ ships classes under pathlib._local; older
    # versions ship them under pathlib. Match the leaf class name and
    # require the module to start with "pathlib" so we don't catch
    # someone's local PurePath.
    parts = full_name.rsplit(".", 1)
    if len(parts) != 2:
        return None
    module, leaf = parts
    if leaf in _PURE_PATH_NAMES and module.split(".")[0] == "pathlib":
        return "pathlib.Path"
    return None


def _attr_exists_on_upgraded_type(
    receiver_names: list,
    attr_name: str,
    cache: dict[str, set[str] | None],
) -> bool:
    """Probe the likely runtime subclass when Jedi resolves to a too-narrow base.

    Used after the main Jedi inference has failed to find ``attr_name`` on
    the receiver. Returns True only when the attribute exists on the
    upgrade target, so legitimate typos like ``path.totaly_made_up()``
    still fire.
    """
    for name in receiver_names:
        try:
            full = name.full_name
        except Exception:
            continue
        upgraded = _upgrade_target(full)
        if not upgraded:
            continue
        attrs = _attrs_on_qualified_type(upgraded, cache)
        if attrs and attr_name in attrs:
            return True
    return False


def _collect_isinstance_targets(test_expr: ast.expr) -> dict[str, list[ast.expr]]:
    """Walk an ``if`` test expression and pull out isinstance narrowings.

    Recurses into ``and`` chains so ``isinstance(x, A) and isinstance(y, B)``
    narrows both. Skips ``or`` / ``not`` since those don't strengthen the type
    inside the if body.

    Returns ``{receiver_text: [type_expr, ...]}``. ``receiver_text`` is the
    unparsed form of the first isinstance arg (``"node"`` or ``"node.value"``).
    ``type_expr`` is the raw AST of the second arg, kept so we can later
    expand tuple forms and infer each element via Jedi.
    """
    out: dict[str, list[ast.expr]] = {}

    def _visit(e: ast.expr) -> None:
        if isinstance(e, ast.Call):
            if (
                isinstance(e.func, ast.Name)
                and e.func.id == "isinstance"
                and len(e.args) == 2
            ):
                try:
                    receiver_text = ast.unparse(e.args[0])
                except Exception:
                    return
                out.setdefault(receiver_text, []).append(e.args[1])
            return
        if isinstance(e, ast.BoolOp) and isinstance(e.op, ast.And):
            for v in e.values:
                _visit(v)

    _visit(test_expr)
    return out


def _build_narrowing_map(tree: ast.AST) -> dict[int, list[ast.expr]]:
    """Map ``id(ast.Attribute)`` to the list of isinstance type-arg expressions
    that narrow its receiver in any enclosing ``if`` block.

    Walks every ``If`` node, gathers its isinstance narrowings, then walks
    that if's body (not elif/else) and tags every Attribute whose unparsed
    receiver matches a narrowed receiver. Nested ifs naturally compose
    because the outer walk descends into the inner if's body.
    """
    narrowed: dict[int, list[ast.expr]] = {}

    for if_node in ast.walk(tree):
        if not isinstance(if_node, ast.If):
            continue
        targets_by_receiver = _collect_isinstance_targets(if_node.test)
        if not targets_by_receiver:
            continue
        for body_stmt in if_node.body:
            for sub in ast.walk(body_stmt):
                if not isinstance(sub, ast.Attribute):
                    continue
                try:
                    receiver_text = ast.unparse(sub.value)
                except Exception:
                    continue
                if receiver_text in targets_by_receiver:
                    narrowed.setdefault(id(sub), []).extend(
                        targets_by_receiver[receiver_text]
                    )

    return narrowed


def _attrs_on_qualified_type(
    full_name: str, cache: dict[str, set[str] | None]
) -> set[str] | None:
    """Return the set of instance attribute names visible on ``full_name``.

    Builds a tiny synthetic Jedi script ``import M; _v: full_name; _v.`` and
    asks Jedi to complete after ``_v.``. Catches instance attributes and
    inherited members, which the simpler ``Name.defined_names()`` misses.

    Returns ``None`` if the type can't be resolved (we then fall back to
    conservative suppression so we don't fabricate findings).
    """
    if full_name in cache:
        return cache[full_name]

    try:
        module = full_name.split(".", 1)[0]
        synthetic = f"import {module}\n_v: {full_name}\n_v."
        synth_script = jedi.Script(synthetic)
        comps = synth_script.complete(3, 3)
        attrs = {c.name for c in comps} if comps else None
    except Exception:
        attrs = None

    cache[full_name] = attrs
    return attrs


def _attr_exists_on_narrowed_types(
    script,
    narrowing_type_exprs: list[ast.expr],
    attr_name: str,
    cache: dict[str, set[str] | None],
) -> bool | None:
    """Decide if ``attr_name`` exists on every type the receiver is narrowed to.

    For each isinstance type-arg in ``narrowing_type_exprs`` (which can be a
    single class or a ``(A, B)`` tuple), resolve to one or more concrete types
    via Jedi, then check ``attr_name`` against the attribute set of each.

    Returns:
        ``True``  if ``attr_name`` is present on every type in every narrowing
                  (this is a false positive, suppress).
        ``False`` if it's missing on at least one type (real bug, fire).
        ``None``  if any type resolution failed (suppress conservatively,
                  matches the lazy fallback).
    """
    for type_expr in narrowing_type_exprs:
        # Expand `isinstance(x, (A, B))` to the individual type exprs
        if isinstance(type_expr, ast.Tuple):
            elts = type_expr.elts
        else:
            elts = [type_expr]

        for elt in elts:
            try:
                type_refs = script.infer(elt.end_lineno, elt.end_col_offset)
            except Exception:
                return None
            if not type_refs:
                return None

            elt_ok = False
            for tref in type_refs:
                try:
                    full = tref.full_name
                except Exception:
                    full = None
                if not full:
                    return None
                attrs = _attrs_on_qualified_type(full, cache)
                if attrs is None:
                    return None
                if attr_name in attrs:
                    elt_ok = True
                    break
            if not elt_ok:
                return False

    return True


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

    # Mock variants use __getattr__ to manufacture attributes on demand, so a
    # static "attribute does not exist" against them is always a false positive.
    suppressed_types = {"Any", "object", "NoneType", "Mock", "MagicMock", "AsyncMock", "NonCallableMock", "NonCallableMagicMock"}  # noqa: E501
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

                # Pre-compute isinstance narrowings for the whole file so we
                # can suppress findings on attribute accesses inside guards
                # like `if isinstance(node, ast.Assign): node.value`.
                narrowing_map = _build_narrowing_map(tree)
                attr_cache: dict[str, set[str] | None] = {}

                # Check each attribute
                for attr_node, line, _col in attributes:
                    try:
                        attr_name = attr_node.attr

                        # If the receiver is isinstance-narrowed in an
                        # enclosing if, prefer the narrowed type's
                        # attribute set over Jedi's broader inference.
                        narrowing_types = narrowing_map.get(id(attr_node))
                        if narrowing_types is not None:
                            narrowed_result = _attr_exists_on_narrowed_types(
                                script, narrowing_types, attr_name, attr_cache
                            )
                            if narrowed_result is True or narrowed_result is None:
                                # Exists on every narrowed type (FP) or we
                                # can't tell (be conservative, don't fire).
                                continue
                            # False: attribute missing on at least one type.
                            # Fall through so the existing Jedi check fires
                            # the finding the normal way.

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

                        # Jedi sometimes resolves Path as PurePath (etc.) and
                        # then can't find write_text/read_text/exists. Probe
                        # the likely subclass before firing so we don't
                        # fabricate findings on perfectly valid pathlib usage.
                        if _attr_exists_on_upgraded_type(
                            receiver_names, attr_name, attr_cache
                        ):
                            continue

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
