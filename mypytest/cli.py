"""
mypytest CLI

Command-line interface for running tests.
"""

import sys
import argparse
from typing import List, Optional

from .runner import TestSession, TestRunner
from .reporting import TestReporter


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog='mypytest',
        description='mypytest - A simple test framework'
    )

    parser.add_argument(
        'paths',
        nargs='*',
        default=['.'],
        help='Paths to test files or directories'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet output (minimal)'
    )

    parser.add_argument(
        '-x', '--exitfirst',
        action='store_true',
        help='Exit on first failure'
    )

    parser.add_argument(
        '-k',
        metavar='EXPRESSION',
        dest='keyword',
        help='Only run tests matching keyword expression'
    )

    parser.add_argument(
        '--collect-only',
        action='store_true',
        help='Only collect tests, do not run'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '-s', '--capture=no',
        action='store_true',
        dest='no_capture',
        help='Do not capture stdout/stderr'
    )

    parser.add_argument(
        '--tb',
        choices=['short', 'long', 'line', 'no'],
        default='short',
        help='Traceback print mode'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='mypytest 1.0.0'
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for mypytest CLI.

    Parameters:
    -----------
    args : list of str, optional
        Command line arguments. If None, uses sys.argv.

    Returns:
    --------
    int
        Exit code (0 for success, 1 for failure)
    """
    parsed = parse_args(args)

    # Create session
    session = TestSession(paths=parsed.paths)
    session.verbose = parsed.verbose
    session.failfast = parsed.exitfirst
    session.capture = not parsed.no_capture

    # Parse keyword filter
    if parsed.keyword:
        session.keywords = [parsed.keyword]

    # Create runner and reporter
    runner = TestRunner(session)
    reporter = TestReporter(
        color=not parsed.no_color,
        verbose=parsed.verbose
    )

    # Header
    print("=" * 60)
    print("mypytest session starts")
    print("=" * 60)

    # Collect tests
    runner.collect()

    # Report collection
    reporter.report_collection(session)

    # Collect only mode
    if parsed.collect_only:
        print("\nCollected tests:")
        for item in session.collected:
            print(f"  {item.nodeid}")
        return 0

    # Run tests
    runner.run_all()

    # Report results
    for result in session.results:
        reporter.report_test_result(result)

    reporter.report_failures(session)
    reporter.report_summary(session)

    # Return exit code
    if session.failed or session.errors:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
