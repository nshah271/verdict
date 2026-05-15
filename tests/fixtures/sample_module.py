"""Sample Python module for testing AST analysis."""

import pytest
from typing import Optional


# Line 7: Regular function
def regular_function(x: int) -> int:
    """A regular function."""
    return x * 2


# Line 13: Async function
async def async_function(name: str) -> str:
    """An async function."""
    return f"Hello, {name}"


# Line 19: Function with simple decorator
@pytest.fixture
def simple_fixture():
    """A fixture with simple decorator."""
    return {"key": "value"}


# Line 26: Function with decorator that has call args
@pytest.fixture(scope="module")
def complex_fixture():
    """A fixture with decorator call args."""
    return [1, 2, 3]


# Line 33: Function with multiple decorators
@pytest.mark.parametrize("x,y", [(1, 2), (3, 4)])
@pytest.mark.slow
def test_with_multiple_decorators(x, y):
    """Test function with multiple decorators."""
    assert x < y


# Line 41: Test function (name starts with test_)
def test_simple_case():
    """A simple test function."""
    assert 1 + 1 == 2


# Line 47: Class with methods
class SampleClass:
    """A sample class."""

    def __init__(self, value: int):
        """Initialize the class."""
        self.value = value

    def method_one(self) -> int:
        """First method."""
        return self.value * 2

    async def async_method(self) -> str:
        """An async method."""
        return f"Value: {self.value}"

    @property
    def computed_property(self) -> int:
        """A property."""
        return self.value + 10


# Line 69: Nested class
class OuterClass:
    """Outer class."""

    class InnerClass:
        """Inner class."""

        def inner_method(self):
            """Method in inner class."""
            return "inner"


# Line 81: Function with complex decorator chain
@pytest.mark.django_db
@pytest.mark.asyncio
async def test_async_with_decorators():
    """Async test with multiple decorators."""
    result = await async_function("World")
    assert result == "Hello, World"


# Line 90: Helper function (not a test)
def helper_function(data: list) -> Optional[int]:
    """A helper function."""
    return data[0] if data else None

# Made with Bob
