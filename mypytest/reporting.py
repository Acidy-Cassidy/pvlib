"""
mypytest reporting

Test result output and formatting.
"""

import sys
import time
from typing import List, Optional, TextIO

from .runner import TestSession, TestResult, TestOutcome


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'


class TestReporter:
    """Reports test results to output"""

    def __init__(self, output: Optional[TextIO] = None, color: bool = True,
                 verbose: bool = False):
        self.output = output or sys.stdout
        self.color = color and hasattr(self.output, 'isatty') and self.output.isatty()
        self.verbose = verbose

    def _colorize(self, text: str, color: str) -> str:
        """Add color to text if color is enabled"""
        if self.color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _outcome_char(self, outcome: TestOutcome) -> str:
        """Get character representation of outcome"""
        chars = {
            TestOutcome.PASSED: self._colorize('.', Colors.GREEN),
            TestOutcome.FAILED: self._colorize('F', Colors.RED),
            TestOutcome.ERROR: self._colorize('E', Colors.RED),
            TestOutcome.SKIPPED: self._colorize('s', Colors.YELLOW),
            TestOutcome.XFAILED: self._colorize('x', Colors.YELLOW),
            TestOutcome.XPASSED: self._colorize('X', Colors.YELLOW),
        }
        return chars.get(outcome, '?')

    def _outcome_word(self, outcome: TestOutcome) -> str:
        """Get word representation of outcome with color"""
        words = {
            TestOutcome.PASSED: self._colorize('PASSED', Colors.GREEN),
            TestOutcome.FAILED: self._colorize('FAILED', Colors.RED),
            TestOutcome.ERROR: self._colorize('ERROR', Colors.RED),
            TestOutcome.SKIPPED: self._colorize('SKIPPED', Colors.YELLOW),
            TestOutcome.XFAILED: self._colorize('XFAIL', Colors.YELLOW),
            TestOutcome.XPASSED: self._colorize('XPASS', Colors.YELLOW),
        }
        return words.get(outcome, 'UNKNOWN')

    def report_collection(self, session: TestSession):
        """Report test collection"""
        count = len(session.collected)
        self.output.write(f"collected {count} item{'s' if count != 1 else ''}\n\n")

    def report_test_start(self, test_item):
        """Report start of a test (verbose mode)"""
        if self.verbose:
            self.output.write(f"{test_item.nodeid} ")
            self.output.flush()

    def report_test_result(self, result: TestResult):
        """Report result of a single test"""
        if self.verbose:
            self.output.write(f"{self._outcome_word(result.outcome)}")
            if result.duration > 0.01:
                self.output.write(f" ({result.duration:.2f}s)")
            self.output.write('\n')
        else:
            self.output.write(self._outcome_char(result.outcome))
            self.output.flush()

    def report_failures(self, session: TestSession):
        """Report detailed failure information"""
        failures = session.failed + session.errors

        if not failures:
            return

        self.output.write('\n\n')
        self.output.write(self._colorize('=' * 60, Colors.RED))
        self.output.write('\n')
        self.output.write(self._colorize('FAILURES', Colors.RED + Colors.BOLD))
        self.output.write('\n')
        self.output.write(self._colorize('=' * 60, Colors.RED))
        self.output.write('\n')

        for result in failures:
            self.output.write('\n')
            self.output.write(self._colorize(f'___ {result.nodeid} ___', Colors.RED))
            self.output.write('\n\n')

            if result.traceback_str:
                self.output.write(result.traceback_str)

            if result.message:
                self.output.write(f"\n{result.message}\n")

    def report_summary(self, session: TestSession):
        """Report final summary"""
        if not self.verbose:
            self.output.write('\n')

        self.output.write('\n')

        # Build summary line
        parts = []

        total = len(session.results)
        passed = len(session.passed)
        failed = len(session.failed)
        errors = len(session.errors)
        skipped = len(session.skipped)
        xfailed = len(session.xfailed)
        xpassed = len(session.xpassed)

        if passed:
            parts.append(self._colorize(f'{passed} passed', Colors.GREEN))
        if failed:
            parts.append(self._colorize(f'{failed} failed', Colors.RED))
        if errors:
            parts.append(self._colorize(f'{errors} errors', Colors.RED))
        if skipped:
            parts.append(self._colorize(f'{skipped} skipped', Colors.YELLOW))
        if xfailed:
            parts.append(self._colorize(f'{xfailed} xfailed', Colors.YELLOW))
        if xpassed:
            parts.append(self._colorize(f'{xpassed} xpassed', Colors.YELLOW))

        # Overall status
        if failed or errors:
            status = self._colorize('FAILED', Colors.RED + Colors.BOLD)
        else:
            status = self._colorize('PASSED', Colors.GREEN + Colors.BOLD)

        duration_str = f" in {session.duration:.2f}s "

        # Print summary line
        line = f"{'=' * 20} {status} {'=' * 20}"
        self.output.write(line + '\n')
        self.output.write(', '.join(parts) + duration_str + '\n')

    def report_session(self, session: TestSession):
        """Report full session results"""
        self.report_collection(session)

        for result in session.results:
            self.report_test_result(result)

        self.report_failures(session)
        self.report_summary(session)


def print_report(session: TestSession, verbose: bool = False,
                 color: bool = True, output: Optional[TextIO] = None):
    """
    Convenience function to print test report.

    Parameters:
    -----------
    session : TestSession
        Test session with results
    verbose : bool
        Verbose output mode
    color : bool
        Use colored output
    output : TextIO
        Output stream (default: stdout)
    """
    reporter = TestReporter(output=output, color=color, verbose=verbose)
    reporter.report_session(session)
