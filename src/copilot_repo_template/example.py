"""Example module demonstrating Python coding standards.

This module provides simple example functions that demonstrate:
- Type hints for function parameters and return values
- Proper docstrings with Args, Returns, and Raises sections
- Basic error handling patterns

This is a TEMPLATE FILE. Replace this with your actual project code when
using this template repository.
"""


def greet(name: str) -> str:
    """Generate a greeting message for the given name.

    This is an example function demonstrating proper type hints and docstrings.
    Replace this with your actual project functionality.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting string in the format "Hello, {name}!".

    Raises:
        ValueError: If name is empty or contains only whitespace.

    Examples:
        >>> greet("World")
        'Hello, World!'
        >>> greet("Copilot")
        'Hello, Copilot!'
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty or whitespace")
    return f"Hello, {name}!"


def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.

    This is another example function demonstrating numeric type hints. Per the
    PEP 484 numeric tower, a ``float`` annotation also accepts ``int`` values.
    Replace this with your actual project functionality.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of a and b.

    Examples:
        >>> add_numbers(2, 3)
        5
        >>> add_numbers(2.5, 3.5)
        6.0
    """
    return a + b
