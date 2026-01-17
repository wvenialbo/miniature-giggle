---
applyTo: "**/*.py"
---

# Project coding standards for Python

## Style Guide (PEP 8)

Apply the [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008) to all code.

### Naming Conventions

- Use **PascalCase** for class names.
- Use **snake_case** for variables, functions, methods, and module names.
- Use **SCREAMING_SNAKE_CASE** for constants.
- Prefix internal/private class members and functions with a single underscore (`_`).

## Documentation Standards (PEP 257)

Apply the [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257) to all code.

### Docstring Conventions

- Every public module, class, and function must have a docstring.
- Use **strictly [numpydoc style](https://numpydoc.readthedocs.io)** for all docstrings.
- Ensure the docstring includes sections like `Parameters`, `Attributes`, `Methods`, `Returns`, and `Raises` where applicable.
- Up to 72 characters per line.
- Use single space after a full-stop.

## Implementation Example

```python
def calculate_velocity(initial_distance, time_delta):
    """
    Calculate the velocity of an object. (Must be single line, up to 72 characters)

    Divide the length over the time spend to travel that length
    (Can have multiple lines, each line up to 72 characters).

    Parameters
    ----------
    initial_distance : float
        The starting distance in meters.
    time_delta : float
        The time elapsed in seconds.

    Returns
    -------
    float
        The calculated velocity in m/s.
    """
    return initial_distance / time_delta
```
