"""
mypytest test runner

Executes tests and collects results.
"""

import sys
import time
import traceback
import inspect
from typing import List, Optional, Dict, Any, Callable
from enum import Enum

from .discovery import TestItem, TestCollector
from .fixtures import get_fixture_manager, FixtureManager
from .markers import get_marker, has_marker


class TestOutcome(Enum):
    """Possible test outcomes"""
    PASSED = 'passed'
    FAILED = 'failed'
    ERROR = 'error'
    SKIPPED = 'skipped'
    XFAILED = 'xfailed'  # Expected failure
    XPASSED = 'xpassed'  # Unexpected pass


class TestResult:
    """Result of a single test execution"""

    def __init__(self, test_item: TestItem, outcome: TestOutcome,
                 duration: float = 0.0, message: str = "",
                 exc_info: Optional[tuple] = None):
        self.test_item = test_item
        self.outcome = outcome
        self.duration = duration
        self.message = message
        self.exc_info = exc_info

        # Extract traceback if available
        self.traceback_str = ""
        if exc_info:
            self.traceback_str = ''.join(traceback.format_exception(*exc_info))

    @property
    def nodeid(self) -> str:
        return self.test_item.nodeid

    def __repr__(self):
        return f"<TestResult {self.nodeid} {self.outcome.value}>"


class TestSession:
    """A test session containing configuration and results"""

    def __init__(self, paths: Optional[List[str]] = None):
        self.paths = paths or ['.']
        self.collected: List[TestItem] = []
        self.results: List[TestResult] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.fixture_manager = get_fixture_manager()

        # Configuration
        self.verbose = False
        self.failfast = False
        self.capture = True
        self.keywords: List[str] = []

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def passed(self) -> List[TestResult]:
        return [r for r in self.results if r.outcome == TestOutcome.PASSED]

    @property
    def failed(self) -> List[TestResult]:
        return [r for r in self.results if r.outcome == TestOutcome.FAILED]

    @property
    def errors(self) -> List[TestResult]:
        return [r for r in self.results if r.outcome == TestOutcome.ERROR]

    @property
    def skipped(self) -> List[TestResult]:
        return [r for r in self.results if r.outcome == TestOutcome.SKIPPED]

    @property
    def xfailed(self) -> List[TestResult]:
        return [r for r in self.results if r.outcome == TestOutcome.XFAILED]

    @property
    def xpassed(self) -> List[TestResult]:
        return [r for r in self.results if r.outcome == TestOutcome.XPASSED]


class TestRunner:
    """Runs tests and collects results"""

    def __init__(self, session: Optional[TestSession] = None):
        self.session = session or TestSession()
        self.hooks: Dict[str, List[Callable]] = {
            'pytest_collection_start': [],
            'pytest_collection_finish': [],
            'pytest_runtest_setup': [],
            'pytest_runtest_call': [],
            'pytest_runtest_teardown': [],
            'pytest_runtest_logreport': [],
        }

    def add_hook(self, name: str, func: Callable):
        """Register a hook function"""
        if name in self.hooks:
            self.hooks[name].append(func)

    def _call_hooks(self, name: str, **kwargs):
        """Call all registered hooks"""
        for hook in self.hooks.get(name, []):
            try:
                hook(**kwargs)
            except Exception as e:
                print(f"Hook {name} error: {e}")

    def collect(self) -> List[TestItem]:
        """Collect tests from session paths"""
        self._call_hooks('pytest_collection_start', session=self.session)

        collector = TestCollector()
        for path in self.session.paths:
            items = collector.collect_from_path(path)
            self.session.collected.extend(items)

        # Filter by keywords if specified
        if self.session.keywords:
            filtered = []
            for item in self.session.collected:
                for keyword in self.session.keywords:
                    if keyword.lower() in item.nodeid.lower():
                        filtered.append(item)
                        break
            self.session.collected = filtered

        self._call_hooks('pytest_collection_finish', session=self.session)

        return self.session.collected

    def run_test(self, test_item: TestItem) -> TestResult:
        """Run a single test"""
        start_time = time.time()

        # Check for skip marker
        skip_marker = get_marker(test_item.function, 'skip')
        if skip_marker:
            reason = skip_marker.kwargs.get('reason', '')
            return TestResult(test_item, TestOutcome.SKIPPED,
                            duration=0, message=reason)

        # Check for skipif marker
        skipif_marker = get_marker(test_item.function, 'skipif')
        if skipif_marker and skipif_marker.args and skipif_marker.args[0]:
            reason = skipif_marker.kwargs.get('reason', '')
            return TestResult(test_item, TestOutcome.SKIPPED,
                            duration=0, message=reason)

        # Check for xfail marker
        xfail_marker = get_marker(test_item.function, 'xfail')
        expect_failure = xfail_marker is not None
        xfail_strict = xfail_marker.kwargs.get('strict', False) if xfail_marker else False

        self._call_hooks('pytest_runtest_setup', item=test_item)

        try:
            # Setup fixtures
            fixture_values = self.session.fixture_manager.setup_fixtures(test_item)

            self._call_hooks('pytest_runtest_call', item=test_item)

            # Get function parameters
            sig = inspect.signature(test_item.function)
            kwargs = {}

            # Handle parametrize
            if test_item.params:
                param_marker = get_marker(test_item.function, 'parametrize')
                if param_marker:
                    argnames = param_marker.args[0]
                    if isinstance(argnames, str):
                        argnames = [a.strip() for a in argnames.split(',')]

                    for i, name in enumerate(argnames):
                        if i < len(test_item.params):
                            kwargs[name] = test_item.params[i]

            # Add fixture values
            for param_name in sig.parameters:
                if param_name in fixture_values:
                    kwargs[param_name] = fixture_values[param_name]
                elif param_name == 'self' and test_item.cls:
                    # Skip self for class methods - handled separately
                    pass

            # Run the test
            if test_item.cls:
                instance = test_item.cls()
                test_item.function(instance, **kwargs)
            else:
                test_item.function(**kwargs)

            duration = time.time() - start_time

            # Test passed
            if expect_failure:
                # Expected to fail but passed
                if xfail_strict:
                    return TestResult(test_item, TestOutcome.FAILED,
                                    duration=duration,
                                    message="Expected failure but test passed (strict)")
                return TestResult(test_item, TestOutcome.XPASSED,
                                duration=duration,
                                message="Expected failure but test passed")

            return TestResult(test_item, TestOutcome.PASSED, duration=duration)

        except Exception as e:
            duration = time.time() - start_time
            exc_info = sys.exc_info()

            if expect_failure:
                # Expected failure occurred
                xfail_reason = xfail_marker.kwargs.get('reason', '') if xfail_marker else ''
                return TestResult(test_item, TestOutcome.XFAILED,
                                duration=duration, message=xfail_reason,
                                exc_info=exc_info)

            # Determine if it's a test failure or error
            if isinstance(e, AssertionError):
                outcome = TestOutcome.FAILED
            else:
                outcome = TestOutcome.ERROR

            return TestResult(test_item, outcome, duration=duration,
                            message=str(e), exc_info=exc_info)

        finally:
            self._call_hooks('pytest_runtest_teardown', item=test_item)
            self.session.fixture_manager.teardown_fixtures()

    def run_all(self) -> List[TestResult]:
        """Run all collected tests"""
        self.session.start_time = time.time()
        self.session.results = []

        for test_item in self.session.collected:
            result = self.run_test(test_item)
            self.session.results.append(result)

            self._call_hooks('pytest_runtest_logreport', report=result)

            # Failfast mode
            if self.session.failfast and result.outcome in (
                TestOutcome.FAILED, TestOutcome.ERROR
            ):
                break

        self.session.end_time = time.time()
        self.session.fixture_manager.clear_all()

        return self.session.results

    def run(self) -> int:
        """Collect and run tests, return exit code"""
        self.collect()
        self.run_all()

        # Return code: 0 if all passed, 1 if any failed
        if self.session.failed or self.session.errors:
            return 1
        return 0


def run_tests(paths: Optional[List[str]] = None, verbose: bool = False,
              failfast: bool = False, keywords: Optional[List[str]] = None) -> TestSession:
    """
    Convenience function to run tests.

    Parameters:
    -----------
    paths : list of str
        Paths to test files or directories
    verbose : bool
        Verbose output
    failfast : bool
        Stop on first failure
    keywords : list of str
        Filter tests by keyword expressions

    Returns:
    --------
    TestSession with results
    """
    session = TestSession(paths=paths)
    session.verbose = verbose
    session.failfast = failfast
    session.keywords = keywords or []

    runner = TestRunner(session)
    runner.collect()
    runner.run_all()

    return session
