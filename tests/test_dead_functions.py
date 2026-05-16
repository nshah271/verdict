"""Tests for dead function detection."""

from pathlib import Path

from verdict.checks.dead_functions import DeadFunctionCheck
from verdict.types import AddedFunction


def test_unreferenced_function_flagged(tmp_path: Path):
    """Test that an added function with no references is flagged."""
    # Create a module with an unreferenced function
    module = tmp_path / "module.py"
    module.write_text("def unused_function():\n    return 42\n")

    added_functions = [
        AddedFunction(
            file="module.py",
            name="unused_function",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 1
    assert findings[0]["kind"] == "dead_function"
    assert findings[0]["file"] == "module.py"
    assert findings[0]["line"] == 1
    assert "unused_function() is never referenced" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.9


def test_referenced_function_not_flagged(tmp_path: Path):
    """Test that a function referenced in another file is not flagged."""
    # Create module with function
    module = tmp_path / "module.py"
    module.write_text("def used_function():\n    return 42\n")

    # Create another file that references it
    caller = tmp_path / "caller.py"
    caller.write_text("from module import used_function\n\nresult = used_function()\n")

    added_functions = [
        AddedFunction(
            file="module.py",
            name="used_function",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_referenced_in_same_file(tmp_path: Path):
    """Test that a function referenced by another function in same file is not flagged."""
    module = tmp_path / "module.py"
    module.write_text(
        "def helper():\n"
        "    return 42\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="helper",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_self_recursive_still_dead(tmp_path: Path):
    """Test that a function that only references itself is still flagged as dead."""
    module = tmp_path / "module.py"
    module.write_text(
        "def recursive_func(n):\n"
        "    if n <= 0:\n"
        "        return 1\n"
        "    return n * recursive_func(n - 1)\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="recursive_func",
            line=1,
            end_line=4,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 1
    assert findings[0]["file"] == "module.py"


def test_passed_as_callback(tmp_path: Path):
    """Test that a function passed as a callback (e.g., to map) is not flagged."""
    module = tmp_path / "module.py"
    module.write_text(
        "def transform(x):\n"
        "    return x * 2\n"
        "\n"
        "def process():\n"
        "    return list(map(transform, [1, 2, 3]))\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="transform",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_assigned_to_variable(tmp_path: Path):
    """Test that a function assigned to a variable is not flagged."""
    module = tmp_path / "module.py"
    module.write_text(
        "def handler():\n"
        "    return 'handled'\n"
        "\n"
        "callback = handler\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="handler",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_used_in_list(tmp_path: Path):
    """Test that a function used in a list literal is not flagged."""
    module = tmp_path / "module.py"
    module.write_text(
        "def func_a():\n"
        "    return 'a'\n"
        "\n"
        "def func_b():\n"
        "    return 'b'\n"
        "\n"
        "handlers = [func_a, func_b]\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="func_a",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_test_function_excluded(tmp_path: Path):
    """Test that test functions are excluded from dead code detection."""
    module = tmp_path / "test_module.py"
    module.write_text("def test_something():\n    assert True\n")

    added_functions = [
        AddedFunction(
            file="test_module.py",
            name="test_something",
            line=1,
            end_line=2,
            is_test=True,  # Marked as test
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_dunder_excluded(tmp_path: Path):
    """Test that dunder methods are excluded."""
    module = tmp_path / "module.py"
    module.write_text(
        "class MyClass:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "    def __repr__(self):\n"
        "        return 'MyClass()'\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="__init__",
            line=2,
            end_line=3,
            is_test=False,
            decorators=[],
        ),
        AddedFunction(
            file="module.py",
            name="__repr__",
            line=4,
            end_line=5,
            is_test=False,
            decorators=[],
        ),
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_fixture_excluded(tmp_path: Path):
    """Test that pytest fixtures are excluded."""
    module = tmp_path / "conftest.py"
    module.write_text(
        "import pytest\n"
        "\n"
        "@pytest.fixture\n"
        "def my_fixture():\n"
        "    return 42\n"
    )

    added_functions = [
        AddedFunction(
            file="conftest.py",
            name="my_fixture",
            line=4,
            end_line=5,
            is_test=False,
            decorators=["pytest.fixture"],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_route_excluded(tmp_path: Path):
    """Test that route handlers are excluded."""
    module = tmp_path / "app.py"
    module.write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "\n"
        "@app.route('/hello')\n"
        "def hello():\n"
        "    return 'Hello'\n"
    )

    added_functions = [
        AddedFunction(
            file="app.py",
            name="hello",
            line=5,
            end_line=6,
            is_test=False,
            decorators=["app.route"],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_click_command_excluded(tmp_path: Path):
    """Test that Click CLI commands are excluded."""
    module = tmp_path / "cli.py"
    module.write_text(
        "import click\n"
        "\n"
        "@click.command()\n"
        "def main():\n"
        "    click.echo('Hello')\n"
    )

    added_functions = [
        AddedFunction(
            file="cli.py",
            name="main",
            line=4,
            end_line=5,
            is_test=False,
            decorators=["click.command"],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_in_all_excluded(tmp_path: Path):
    """Test that functions in __all__ are not flagged."""
    module = tmp_path / "module.py"
    module.write_text(
        "__all__ = ['exported_func']\n"
        "\n"
        "def exported_func():\n"
        "    return 42\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="exported_func",
            line=3,
            end_line=4,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_init_import_excluded(tmp_path: Path):
    """Test that functions imported in __init__.py are not flagged."""
    # Create package structure
    pkg = tmp_path / "mypackage"
    pkg.mkdir()

    # Create module with function
    module = pkg / "module.py"
    module.write_text("def public_func():\n    return 42\n")

    # Import in __init__.py
    init = pkg / "__init__.py"
    init.write_text("from mypackage.module import public_func\n")

    added_functions = [
        AddedFunction(
            file="mypackage/module.py",
            name="public_func",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_attribute_reference_counts(tmp_path: Path):
    """Test that module.func references (without call) count as alive."""
    module = tmp_path / "module.py"
    module.write_text("def my_func():\n    return 42\n")

    caller = tmp_path / "caller.py"
    caller.write_text("import module\n\nhandler = module.my_func\n")

    added_functions = [
        AddedFunction(
            file="module.py",
            name="my_func",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_syntax_error_skipped(tmp_path: Path):
    """Test that files with syntax errors don't crash the check."""
    # Create a valid module
    module = tmp_path / "module.py"
    module.write_text("def good_func():\n    return 42\n")

    # Create a broken file
    broken = tmp_path / "broken.py"
    broken.write_text("def broken_func(\n    # Missing closing paren\n")

    added_functions = [
        AddedFunction(
            file="module.py",
            name="good_func",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    # Should not crash, just skip the broken file
    findings = check.run(str(tmp_path), added_functions)

    # good_func is unreferenced, so should be flagged
    assert len(findings) == 1
    assert findings[0]["file"] == "module.py"


def test_no_added_functions(tmp_path: Path):
    """Test that empty input returns empty findings."""
    module = tmp_path / "module.py"
    module.write_text("def some_func():\n    return 42\n")

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), [])

    assert findings == []


def test_class_instantiation_counts(tmp_path: Path):
    """Test that class instantiation (MyClass()) counts as alive."""
    module = tmp_path / "module.py"
    module.write_text("class MyClass:\n    pass\n")

    caller = tmp_path / "caller.py"
    caller.write_text("from module import MyClass\n\nobj = MyClass()\n")

    added_functions = [
        AddedFunction(
            file="module.py",
            name="MyClass",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        )
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 0


def test_multiple_dead_functions(tmp_path: Path):
    """Test that multiple dead functions are all flagged correctly."""
    module = tmp_path / "module.py"
    module.write_text(
        "def dead_one():\n"
        "    return 1\n"
        "\n"
        "def alive():\n"
        "    return 2\n"
        "\n"
        "def dead_two():\n"
        "    return 3\n"
        "\n"
        "result = alive()\n"
    )

    added_functions = [
        AddedFunction(
            file="module.py",
            name="dead_one",
            line=1,
            end_line=2,
            is_test=False,
            decorators=[],
        ),
        AddedFunction(
            file="module.py",
            name="alive",
            line=4,
            end_line=5,
            is_test=False,
            decorators=[],
        ),
        AddedFunction(
            file="module.py",
            name="dead_two",
            line=7,
            end_line=8,
            is_test=False,
            decorators=[],
        ),
    ]

    check = DeadFunctionCheck()
    findings = check.run(str(tmp_path), added_functions)

    assert len(findings) == 2
    dead_names = {f["message"].split("(")[0] for f in findings}
    assert "dead_one" in dead_names
    assert "dead_two" in dead_names

# Made with Bob
