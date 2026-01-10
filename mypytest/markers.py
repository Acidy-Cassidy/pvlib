"""
mypytest markers

Provides test markers like skip, xfail, parametrize.
"""

import functools
from typing import Callable, List, Optional, Any, Tuple, Union


class Mark:
    """Represents a test marker"""

    def __init__(self, name: str, args: Tuple = (), kwargs: dict = None):
        self.name = name
        self.args = args
        self.kwargs = kwargs or {}

    def __repr__(self):
        return f"<Mark {self.name}>"

    def __call__(self, func: Callable) -> Callable:
        """Apply marker to a function"""
        # Get or create markers list
        if not hasattr(func, '_pytest_markers'):
            func._pytest_markers = []
        func._pytest_markers.append(self)
        return func


class MarkDecorator:
    """Decorator factory for creating marks"""

    def __init__(self, name: str):
        self.name = name
        self._mark = None

    def __call__(self, *args, **kwargs) -> Union[Mark, Callable]:
        """Create a mark or apply it to a function"""
        # If first arg is a function, apply mark directly
        if len(args) == 1 and callable(args[0]) and not kwargs:
            func = args[0]
            mark = Mark(self.name)
            return mark(func)

        # Otherwise, return a mark to be applied later
        return Mark(self.name, args, kwargs)

    def __getattr__(self, name: str) -> 'MarkDecorator':
        """Support pytest.mark.custom_marker syntax"""
        return MarkDecorator(name)


class MarkGenerator:
    """Generator for creating mark decorators (pytest.mark)"""

    def __getattr__(self, name: str) -> MarkDecorator:
        return MarkDecorator(name)

    # Pre-defined markers
    @property
    def skip(self):
        """Skip marker - skip a test"""
        return MarkDecorator('skip')

    @property
    def skipif(self):
        """Skipif marker - conditionally skip a test"""
        return MarkDecorator('skipif')

    @property
    def xfail(self):
        """Xfail marker - expect a test to fail"""
        return MarkDecorator('xfail')

    @property
    def parametrize(self):
        """Parametrize marker - run test with multiple parameter sets"""
        return MarkDecorator('parametrize')

    @property
    def usefixtures(self):
        """Usefixtures marker - use fixtures without arguments"""
        return MarkDecorator('usefixtures')

    @property
    def filterwarnings(self):
        """Filterwarnings marker - filter warnings during test"""
        return MarkDecorator('filterwarnings')


# Global mark generator
mark = MarkGenerator()


def skip(reason: str = "") -> Callable:
    """
    Skip a test with optional reason.

    Usage:
        @pytest.mark.skip(reason="not implemented")
        def test_something():
            pass
    """
    def decorator(func):
        mark_obj = Mark('skip', (), {'reason': reason})
        return mark_obj(func)
    return decorator


def skipif(condition: bool, *, reason: str = "") -> Callable:
    """
    Skip a test if condition is true.

    Usage:
        @pytest.mark.skipif(sys.version_info < (3, 8), reason="requires 3.8+")
        def test_something():
            pass
    """
    def decorator(func):
        mark_obj = Mark('skipif', (condition,), {'reason': reason})
        return mark_obj(func)
    return decorator


def xfail(reason: str = "", *, raises: Optional[type] = None,
          strict: bool = False, condition: bool = True) -> Callable:
    """
    Mark a test as expected to fail.

    Usage:
        @pytest.mark.xfail(reason="known bug")
        def test_something():
            pass
    """
    def decorator(func):
        mark_obj = Mark('xfail', (), {
            'reason': reason,
            'raises': raises,
            'strict': strict,
            'condition': condition
        })
        return mark_obj(func)
    return decorator


def parametrize(argnames: Union[str, List[str]], argvalues: List,
                ids: Optional[List[str]] = None) -> Callable:
    """
    Parametrize a test function.

    Usage:
        @pytest.mark.parametrize("x,y,expected", [
            (1, 2, 3),
            (2, 3, 5),
            (10, 20, 30),
        ])
        def test_add(x, y, expected):
            assert x + y == expected
    """
    def decorator(func):
        mark_obj = Mark('parametrize', (argnames, argvalues), {'ids': ids})
        return mark_obj(func)
    return decorator


def get_markers(func: Callable) -> List[Mark]:
    """Get all markers from a function"""
    return getattr(func, '_pytest_markers', [])


def has_marker(func: Callable, name: str) -> bool:
    """Check if function has a specific marker"""
    markers = get_markers(func)
    return any(m.name == name for m in markers)


def get_marker(func: Callable, name: str) -> Optional[Mark]:
    """Get a specific marker from a function"""
    markers = get_markers(func)
    for m in markers:
        if m.name == name:
            return m
    return None
