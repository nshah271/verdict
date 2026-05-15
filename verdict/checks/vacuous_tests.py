"""Vacuous test detection check.

Identifies test functions that don't meaningfully test anything through four heuristics:
- Empty body (pass, ..., return, or docstring only)
- No assertions (no assert statements or assertion method calls)
- Mock-only assertions (only asserts on mocks created in the test)
- Doesn't reach new code (doesn't call any newly added functions)
"""

import ast
from pathlib import Path

from verdict.types import AddedFunction, Check, Finding


def _get_assigned_mock_names(func_node: ast.FunctionDef) -> set[str]:
    """Extract names assigned from Mock(), MagicMock(), or patch() calls.
    
    Args:
        func_node: The function AST node to analyze
        
    Returns:
        Set of variable names that were assigned mock objects
    """
    mock_names = set()
    
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            # Check if the value is a call to Mock, MagicMock, or patch
            if isinstance(node.value, ast.Call):
                func_name = None
                
                # Handle simple names like Mock()
                if isinstance(node.value.func, ast.Name):
                    func_name = node.value.func.id
                # Handle attribute access like unittest.mock.Mock()
                elif isinstance(node.value.func, ast.Attribute):
                    func_name = node.value.func.attr
                
                # Check if it's a mock-related call
                if func_name in ("Mock", "MagicMock", "patch"):
                    # Extract target names from the assignment
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            mock_names.add(target.id)
                        elif isinstance(target, ast.Tuple):
                            for elt in target.elts:
                                if isinstance(elt, ast.Name):
                                    mock_names.add(elt.id)
    
    return mock_names


def _is_empty_body(func_node: ast.FunctionDef) -> bool:
    """Check if function body is effectively empty.
    
    Empty means: only pass, ..., return (no value), or a single docstring.
    """
    body = func_node.body
    
    if len(body) == 0:
        return True
    
    if len(body) == 1:
        stmt = body[0]
        
        # Check for pass
        if isinstance(stmt, ast.Pass):
            return True
        
        # Check for ... (Ellipsis)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if stmt.value.value is Ellipsis or isinstance(stmt.value.value, str):
                return True
        
        # Check for return with no value
        if isinstance(stmt, ast.Return) and stmt.value is None:
            return True
    
    return False


def _has_no_assertions(func_node: ast.FunctionDef) -> bool:
    """Check if function has no assertions.
    
    Looks for both assert statements and assertion method calls.
    """
    has_assert_stmt = False
    has_assert_call = False
    
    assertion_methods = {
        "assertEqual", "assertTrue", "assertFalse", "assertRaises",
        "assertIn", "assertIsNone", "assertIsNotNone"
    }
    
    for node in ast.walk(func_node):
        # Check for assert statements
        if isinstance(node, ast.Assert):
            has_assert_stmt = True
            break
        
        # Check for assertion method calls
        if isinstance(node, ast.Call):
            func_name = None
            
            # Handle self.assertEqual() pattern
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            # Handle assertEqual() pattern (less common but possible)
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            
            if func_name in assertion_methods:
                has_assert_call = True
                break
    
    return not (has_assert_stmt or has_assert_call)


def _get_names_from_expr(expr: ast.expr) -> set[str]:
    """Extract all Name nodes from an expression."""
    names = set()
    for node in ast.walk(expr):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _only_asserts_on_mocks(func_node: ast.FunctionDef, mock_names: set[str]) -> bool:
    """Check if all assertions operate only on mock objects.
    
    Args:
        func_node: The function AST node
        mock_names: Set of variable names that are mocks
        
    Returns:
        True if there are assertions AND all of them are on mocks only
    """
    if not mock_names:
        return False
    
    assertion_targets = []
    assertion_methods = {
        "assertEqual", "assertTrue", "assertFalse", "assertRaises",
        "assertIn", "assertIsNone", "assertIsNotNone"
    }
    
    for node in ast.walk(func_node):
        # Collect assert statement targets
        if isinstance(node, ast.Assert):
            assertion_targets.append(node.test)
        
        # Collect assertion method call targets (first argument)
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            
            if func_name in assertion_methods and node.args:
                assertion_targets.append(node.args[0])
    
    # If no assertions found, this heuristic doesn't apply
    if not assertion_targets:
        return False
    
    # Check if all assertion targets only reference mock names
    for target in assertion_targets:
        target_names = _get_names_from_expr(target)
        # If any name in the target is NOT a mock, return False
        if target_names and not target_names.issubset(mock_names):
            return False
    
    return True


def _doesnt_call_new_functions(
    func_node: ast.FunctionDef, new_function_names: set[str]
) -> bool:
    """Check if test doesn't call any newly added functions.
    
    Args:
        func_node: The test function AST node
        new_function_names: Set of names of newly added functions
        
    Returns:
        True if the test makes zero calls to new functions
    """
    if not new_function_names:
        return False
    
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            called_name = None
            
            # Handle simple function calls: foo()
            if isinstance(node.func, ast.Name):
                called_name = node.func.id
            # Handle method calls: obj.foo()
            elif isinstance(node.func, ast.Attribute):
                called_name = node.func.attr
            
            if called_name in new_function_names:
                return False
    
    return True


class VacuousTestCheck:
    """Check for vacuous test functions that don't meaningfully test anything."""
    
    name = "vacuous_tests"
    kind = "static"
    
    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]:
        """Run vacuous test detection on added test functions.
        
        Args:
            diff_root: Root directory of the diff (workspace root)
            added_functions: List of all added functions from the diff
            
        Returns:
            List of findings, one per heuristic that fires per test function
        """
        findings: list[Finding] = []
        
        # Filter to only test functions
        test_functions = [f for f in added_functions if f["is_test"]]
        
        # Build set of all new function names for heuristic D
        new_function_names = {f["name"] for f in added_functions}
        
        for test_func in test_functions:
            try:
                # Read and parse the source file
                source_path = Path(diff_root) / test_func["file"]
                content = source_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(source_path))
                
                # Find the matching function node by name and line number
                func_node = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if (node.name == test_func["name"] and 
                            node.lineno == test_func["line"]):
                            func_node = node
                            break
                
                if func_node is None:
                    continue
                
                # Run heuristic checks
                file_path = test_func["file"]
                line = test_func["line"]
                
                # Heuristic A: Empty body
                if _is_empty_body(func_node):
                    findings.append({
                        "kind": "vacuous_test",
                        "file": file_path,
                        "line": line,
                        "message": "test body is empty",
                        "confidence": 1.0,
                    })
                
                # Heuristic B: No assertions
                if _has_no_assertions(func_node):
                    findings.append({
                        "kind": "vacuous_test",
                        "file": file_path,
                        "line": line,
                        "message": "test has no assertions",
                        "confidence": 0.9,
                    })
                
                # Heuristic C: Mock-only assertions
                mock_names = _get_assigned_mock_names(func_node)
                if _only_asserts_on_mocks(func_node, mock_names):
                    findings.append({
                        "kind": "vacuous_test",
                        "file": file_path,
                        "line": line,
                        "message": "test only asserts on mocks",
                        "confidence": 0.8,
                    })
                
                # Heuristic D: Doesn't reach new code
                if _doesnt_call_new_functions(func_node, new_function_names):
                    findings.append({
                        "kind": "vacuous_test",
                        "file": file_path,
                        "line": line,
                        "message": "test does not call any new function",
                        "confidence": 0.7,
                    })
                
            except (FileNotFoundError, PermissionError, SyntaxError, UnicodeDecodeError):
                # Skip files that can't be read or parsed
                continue
        
        return findings

# Made with Bob


# Export check instance for CLI auto-discovery
check = VacuousTestCheck()
