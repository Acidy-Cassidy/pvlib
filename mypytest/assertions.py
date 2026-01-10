"""
mypytest assertions

Enhanced assertions with detailed failure messages.
"""

import re
from typing import Any, Optional, Type, Callable, Pattern, Union


class AssertionError(builtins_AssertionError := AssertionError):
    """Enhanced assertion error with more details"""

    def __init__(self, message: str = "", details: str = ""):
        self.message = message
        self.details = details
        super().__init__(f"{message}\n{details}" if details else message)


def _format_value(value: Any, max_length: int = 100) -> str:
    """Format a value for display in assertion messages"""
    repr_str = repr(value)
    if len(repr_str) > max_length:
        repr_str = repr_str[:max_length] + "..."
    return repr_str


def _diff_strings(left: str, right: str) -> str:
    """Generate a diff between two strings"""
    if left == right:
        return ""

    lines = []
    lines.append(f"  Left:  {_format_value(left)}")
    lines.append(f"  Right: {_format_value(right)}")

    # Find first difference
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            lines.append(f"  First difference at index {i}: {repr(a)} != {repr(b)}")
            break
    else:
        if len(left) != len(right):
            lines.append(f"  Length difference: {len(left)} vs {len(right)}")

    return '\n'.join(lines)


def _diff_sequences(left: Any, right: Any) -> str:
    """Generate a diff between two sequences"""
    lines = []

    left_len = len(left) if hasattr(left, '__len__') else '?'
    right_len = len(right) if hasattr(right, '__len__') else '?'
    lines.append(f"  Left length:  {left_len}")
    lines.append(f"  Right length: {right_len}")

    # Find differences
    try:
        for i, (a, b) in enumerate(zip(left, right)):
            if a != b:
                lines.append(f"  First difference at index {i}:")
                lines.append(f"    Left:  {_format_value(a)}")
                lines.append(f"    Right: {_format_value(b)}")
                break
    except Exception:
        pass

    return '\n'.join(lines)


def assert_equal(left: Any, right: Any, msg: str = ""):
    """Assert that two values are equal"""
    if left != right:
        details = []
        details.append(f"  Left:  {_format_value(left)}")
        details.append(f"  Right: {_format_value(right)}")

        # Add type info if different types
        if type(left) != type(right):
            details.append(f"  Types: {type(left).__name__} vs {type(right).__name__}")

        # Add diff for strings/sequences
        if isinstance(left, str) and isinstance(right, str):
            diff = _diff_strings(left, right)
            if diff:
                details.append(diff)
        elif hasattr(left, '__iter__') and hasattr(right, '__iter__'):
            diff = _diff_sequences(left, right)
            if diff:
                details.append(diff)

        message = msg or f"assert {_format_value(left)} == {_format_value(right)}"
        raise AssertionError(message, '\n'.join(details))


def assert_not_equal(left: Any, right: Any, msg: str = ""):
    """Assert that two values are not equal"""
    if left == right:
        message = msg or f"assert {_format_value(left)} != {_format_value(right)}"
        raise AssertionError(message, f"  Both values are: {_format_value(left)}")


def assert_true(value: Any, msg: str = ""):
    """Assert that a value is truthy"""
    if not value:
        message = msg or f"assert {_format_value(value)}"
        raise AssertionError(message, f"  Value is falsy: {_format_value(value)}")


def assert_false(value: Any, msg: str = ""):
    """Assert that a value is falsy"""
    if value:
        message = msg or f"assert not {_format_value(value)}"
        raise AssertionError(message, f"  Value is truthy: {_format_value(value)}")


def assert_is(left: Any, right: Any, msg: str = ""):
    """Assert that two values are the same object"""
    if left is not right:
        message = msg or f"assert {_format_value(left)} is {_format_value(right)}"
        raise AssertionError(message,
            f"  Left id:  {id(left)}\n  Right id: {id(right)}")


def assert_is_not(left: Any, right: Any, msg: str = ""):
    """Assert that two values are not the same object"""
    if left is right:
        message = msg or f"assert {_format_value(left)} is not {_format_value(right)}"
        raise AssertionError(message, f"  Both are same object with id: {id(left)}")


def assert_is_none(value: Any, msg: str = ""):
    """Assert that a value is None"""
    if value is not None:
        message = msg or f"assert {_format_value(value)} is None"
        raise AssertionError(message, f"  Value is: {_format_value(value)}")


def assert_is_not_none(value: Any, msg: str = ""):
    """Assert that a value is not None"""
    if value is None:
        message = msg or "assert value is not None"
        raise AssertionError(message, "  Value is None")


def assert_in(member: Any, container: Any, msg: str = ""):
    """Assert that member is in container"""
    if member not in container:
        message = msg or f"assert {_format_value(member)} in {_format_value(container)}"
        raise AssertionError(message,
            f"  Member: {_format_value(member)}\n  Container: {_format_value(container)}")


def assert_not_in(member: Any, container: Any, msg: str = ""):
    """Assert that member is not in container"""
    if member in container:
        message = msg or f"assert {_format_value(member)} not in {_format_value(container)}"
        raise AssertionError(message,
            f"  Member: {_format_value(member)}\n  Found in: {_format_value(container)}")


def assert_is_instance(obj: Any, cls: Union[type, tuple], msg: str = ""):
    """Assert that obj is an instance of cls"""
    if not isinstance(obj, cls):
        message = msg or f"assert isinstance({_format_value(obj)}, {cls})"
        raise AssertionError(message,
            f"  Object type: {type(obj).__name__}\n  Expected: {cls}")


def assert_not_is_instance(obj: Any, cls: Union[type, tuple], msg: str = ""):
    """Assert that obj is not an instance of cls"""
    if isinstance(obj, cls):
        message = msg or f"assert not isinstance({_format_value(obj)}, {cls})"
        raise AssertionError(message,
            f"  Object type: {type(obj).__name__}\n  Should not be: {cls}")


def assert_raises(exc_type: Type[Exception], func: Optional[Callable] = None,
                  *args, **kwargs):
    """
    Assert that a function raises an exception.

    Usage:
        with pytest.raises(ValueError):
            raise ValueError("boom")

        # or
        pytest.raises(ValueError, func, arg1, arg2)
    """
    if func is not None:
        try:
            func(*args, **kwargs)
        except exc_type:
            return
        except Exception as e:
            raise AssertionError(
                f"Expected {exc_type.__name__}, got {type(e).__name__}",
                f"  Exception: {e}"
            )
        raise AssertionError(
            f"Expected {exc_type.__name__} but no exception was raised"
        )

    # Context manager mode
    return RaisesContext(exc_type)


class RaisesContext:
    """Context manager for pytest.raises()"""

    def __init__(self, exc_type: Type[Exception], match: Optional[str] = None):
        self.exc_type = exc_type
        self.match = match
        self.value: Optional[Exception] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(
                f"Expected {self.exc_type.__name__} but no exception was raised"
            )

        if not issubclass(exc_type, self.exc_type):
            return False  # Re-raise the exception

        self.value = exc_val

        if self.match:
            if not re.search(self.match, str(exc_val)):
                raise AssertionError(
                    f"Exception message did not match pattern",
                    f"  Pattern: {self.match}\n  Message: {exc_val}"
                )

        return True  # Suppress the exception


def assert_warns(warn_type: Type[Warning], func: Optional[Callable] = None,
                 *args, **kwargs):
    """Assert that a warning is raised"""
    import warnings

    if func is not None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            func(*args, **kwargs)

            for warning in w:
                if issubclass(warning.category, warn_type):
                    return

            raise AssertionError(f"Expected {warn_type.__name__} warning")

    return WarnsContext(warn_type)


class WarnsContext:
    """Context manager for pytest.warns()"""

    def __init__(self, warn_type: Type[Warning], match: Optional[str] = None):
        self.warn_type = warn_type
        self.match = match
        self.warnings = []

    def __enter__(self):
        import warnings
        self._catch = warnings.catch_warnings(record=True)
        self.warnings = self._catch.__enter__()
        warnings.simplefilter("always")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._catch.__exit__(exc_type, exc_val, exc_tb)

        for w in self.warnings:
            if issubclass(w.category, self.warn_type):
                if self.match and not re.search(self.match, str(w.message)):
                    continue
                return False

        raise AssertionError(f"Expected {self.warn_type.__name__} warning")


def assert_almost_equal(left: float, right: float, places: int = 7, msg: str = ""):
    """Assert that two floats are almost equal"""
    if round(abs(left - right), places) != 0:
        message = msg or f"assert {left} ~= {right} (to {places} places)"
        raise AssertionError(message,
            f"  Difference: {abs(left - right)}\n  Tolerance: {10**(-places)}")


def assert_greater(left: Any, right: Any, msg: str = ""):
    """Assert that left > right"""
    if not left > right:
        message = msg or f"assert {_format_value(left)} > {_format_value(right)}"
        raise AssertionError(message)


def assert_greater_equal(left: Any, right: Any, msg: str = ""):
    """Assert that left >= right"""
    if not left >= right:
        message = msg or f"assert {_format_value(left)} >= {_format_value(right)}"
        raise AssertionError(message)


def assert_less(left: Any, right: Any, msg: str = ""):
    """Assert that left < right"""
    if not left < right:
        message = msg or f"assert {_format_value(left)} < {_format_value(right)}"
        raise AssertionError(message)


def assert_less_equal(left: Any, right: Any, msg: str = ""):
    """Assert that left <= right"""
    if not left <= right:
        message = msg or f"assert {_format_value(left)} <= {_format_value(right)}"
        raise AssertionError(message)


def assert_regex(text: str, pattern: Union[str, Pattern], msg: str = ""):
    """Assert that text matches regex pattern"""
    if not re.search(pattern, text):
        message = msg or f"assert regex {pattern} matches {_format_value(text)}"
        raise AssertionError(message,
            f"  Pattern: {pattern}\n  Text: {_format_value(text)}")


def assert_not_regex(text: str, pattern: Union[str, Pattern], msg: str = ""):
    """Assert that text does not match regex pattern"""
    if re.search(pattern, text):
        message = msg or f"assert regex {pattern} does not match {_format_value(text)}"
        raise AssertionError(message)


# Aliases
raises = assert_raises
warns = assert_warns


def approx(expected: float, rel: Optional[float] = None,
           abs: Optional[float] = None) -> 'ApproxValue':
    """
    Assert that a value is approximately equal.

    Usage:
        assert 0.1 + 0.2 == pytest.approx(0.3)
    """
    return ApproxValue(expected, rel=rel, abs=abs)


class ApproxValue:
    """Approximate value for floating point comparisons"""

    def __init__(self, expected: float, rel: Optional[float] = None,
                 abs: Optional[float] = None):
        self.expected = expected
        self.rel = rel if rel is not None else 1e-6
        self.abs = abs if abs is not None else 1e-12

    def __eq__(self, actual: float) -> bool:
        tolerance = max(self.rel * builtins_abs(self.expected), self.abs)
        return builtins_abs(self.expected - actual) <= tolerance

    def __repr__(self):
        return f"approx({self.expected})"


# Keep reference to builtin abs
builtins_abs = abs
