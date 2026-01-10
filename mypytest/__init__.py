"""
mypytest - Your custom pytest library

A simple but functional test framework inspired by pytest.
"""

# Core imports
from .discovery import TestItem, TestCollector, collect_tests
from .runner import TestSession, TestRunner, TestOutcome, TestResult, run_tests
from .reporting import TestReporter, print_report
from .fixtures import (
    fixture, FixtureScope, FixtureManager, FixtureRequest,
    get_fixture_manager, tmp_path, tmp_path_factory, capsys, monkeypatch
)
from .markers import (
    mark, Mark, MarkDecorator, MarkGenerator,
    skip, skipif, xfail, parametrize,
    get_markers, has_marker, get_marker
)
from .assertions import (
    raises, warns, approx,
    assert_equal, assert_not_equal,
    assert_true, assert_false,
    assert_is, assert_is_not,
    assert_is_none, assert_is_not_none,
    assert_in, assert_not_in,
    assert_is_instance, assert_not_is_instance,
    assert_almost_equal,
    assert_greater, assert_greater_equal,
    assert_less, assert_less_equal,
    assert_regex, assert_not_regex,
    RaisesContext, WarnsContext, ApproxValue
)
from .cli import main


# Convenience function for running from code
def run(paths=None, verbose=False, failfast=False, keywords=None):
    """
    Run tests programmatically.

    Parameters:
    -----------
    paths : list of str
        Paths to test files or directories
    verbose : bool
        Verbose output
    failfast : bool
        Stop on first failure
    keywords : list of str
        Filter tests by keywords

    Returns:
    --------
    TestSession with results
    """
    session = run_tests(
        paths=paths or ['.'],
        verbose=verbose,
        failfast=failfast,
        keywords=keywords
    )
    print_report(session, verbose=verbose)
    return session


# fail() function for explicit test failure
def fail(reason: str = ""):
    """Explicitly fail a test"""
    raise AssertionError(reason or "Test failed explicitly")


# skip() function for skipping during test execution
def skip_test(reason: str = ""):
    """Skip test during execution"""
    from .runner import TestOutcome

    class SkipException(Exception):
        pass

    raise SkipException(reason)


# importorskip for conditional imports
def importorskip(modname: str, minversion: str = None, reason: str = None):
    """
    Import and return a module, skipping test if import fails.

    Parameters:
    -----------
    modname : str
        Module name to import
    minversion : str, optional
        Minimum version required
    reason : str, optional
        Reason for skipping if import fails
    """
    import importlib

    try:
        mod = importlib.import_module(modname)
    except ImportError:
        skip_reason = reason or f"could not import '{modname}'"
        skip_test(skip_reason)

    if minversion:
        version = getattr(mod, '__version__', None)
        if version is None:
            skip_test(f"{modname} has no __version__ attribute")

        # Simple version comparison
        from packaging.version import Version
        try:
            if Version(version) < Version(minversion):
                skip_test(f"{modname} version {version} < {minversion}")
        except Exception:
            pass

    return mod


# deprecated_call context manager
class deprecated_call:
    """Context manager to check for DeprecationWarning"""

    def __init__(self, match: str = None):
        self.match = match
        self._warns_ctx = None

    def __enter__(self):
        self._warns_ctx = warns(DeprecationWarning)
        self._warns_ctx.match = self.match
        return self._warns_ctx.__enter__()

    def __exit__(self, *args):
        return self._warns_ctx.__exit__(*args)


# param for parametrize
def param(*values, id=None, marks=None):
    """
    Create a parameter set for parametrize.

    Usage:
        @pytest.mark.parametrize("x", [
            pytest.param(1, id="one"),
            pytest.param(2, id="two"),
        ])
    """
    class Param:
        def __init__(self, values, id, marks):
            self.values = values
            self.id = id
            self.marks = marks or []

    return Param(values, id, marks)


# Version info
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

__all__ = [
    # Discovery
    'TestItem', 'TestCollector', 'collect_tests',

    # Runner
    'TestSession', 'TestRunner', 'TestOutcome', 'TestResult', 'run_tests', 'run',

    # Reporting
    'TestReporter', 'print_report',

    # Fixtures
    'fixture', 'FixtureScope', 'FixtureManager', 'FixtureRequest',
    'get_fixture_manager', 'tmp_path', 'tmp_path_factory', 'capsys', 'monkeypatch',

    # Markers
    'mark', 'Mark', 'skip', 'skipif', 'xfail', 'parametrize',
    'get_markers', 'has_marker', 'get_marker',

    # Assertions
    'raises', 'warns', 'approx', 'fail', 'skip_test', 'importorskip',
    'deprecated_call', 'param',
    'assert_equal', 'assert_not_equal',
    'assert_true', 'assert_false',
    'assert_is', 'assert_is_not',
    'assert_is_none', 'assert_is_not_none',
    'assert_in', 'assert_not_in',
    'assert_is_instance', 'assert_not_is_instance',
    'assert_almost_equal',
    'assert_greater', 'assert_greater_equal',
    'assert_less', 'assert_less_equal',
    'assert_regex', 'assert_not_regex',

    # CLI
    'main',
]
