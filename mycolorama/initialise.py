"""
mycolorama initialization

Handles initialization for cross-platform colored terminal output.
On Windows, wraps stdout/stderr to convert ANSI codes to Win32 calls.
On other platforms, this is largely a no-op.
"""

import sys
import os
import atexit

# Track initialization state
_initialized = False
_original_stdout = None
_original_stderr = None
_wrap_enabled = True


def _is_windows():
    """Check if running on Windows"""
    return sys.platform.startswith('win') or os.name == 'nt'


def _supports_ansi():
    """Check if the terminal supports ANSI escape codes natively"""
    # Check for common indicators of ANSI support
    if os.environ.get('TERM'):
        return True
    if os.environ.get('COLORTERM'):
        return True
    if os.environ.get('ANSICON'):
        return True
    if os.environ.get('WT_SESSION'):  # Windows Terminal
        return True
    # Check for newer Windows with native ANSI support
    if _is_windows():
        try:
            # Windows 10+ supports ANSI natively with VT processing
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable VT processing
            STD_OUTPUT_HANDLE = -11
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(handle, mode)
            return True
        except Exception:
            pass
    return not _is_windows()


class AnsiToWin32:
    """
    Wrapper for file streams that converts ANSI escape codes to Win32 API calls.
    On non-Windows platforms, this just passes through.
    """

    def __init__(self, wrapped, convert=None, strip=None, autoreset=False):
        self.wrapped = wrapped
        self.autoreset = autoreset
        self._convert = convert
        self._strip = strip

        # Determine conversion behavior
        if convert is None:
            # Auto-detect: convert on Windows if no native ANSI support
            self.convert = _is_windows() and not _supports_ansi()
        else:
            self.convert = convert

        if strip is None:
            # Strip ANSI codes if we're not in a real terminal
            self.strip = not hasattr(wrapped, 'isatty') or not wrapped.isatty()
        else:
            self.strip = strip

    def write(self, text):
        """Write text, handling ANSI codes as needed"""
        if self.strip and not self.convert:
            # Strip ANSI codes
            text = self._strip_ansi(text)
        elif self.convert:
            # Convert ANSI to Win32 (simplified - just strip for now)
            text = self._strip_ansi(text)

        self.wrapped.write(text)

        if self.autoreset:
            self.wrapped.write('\033[0m')

    def _strip_ansi(self, text):
        """Remove ANSI escape sequences from text"""
        import re
        ansi_pattern = re.compile(r'\033\[[0-9;]*[A-Za-z]')
        return ansi_pattern.sub('', text)

    def flush(self):
        """Flush the wrapped stream"""
        if hasattr(self.wrapped, 'flush'):
            self.wrapped.flush()

    def __getattr__(self, name):
        """Delegate attribute access to wrapped stream"""
        return getattr(self.wrapped, name)


class StreamWrapper:
    """Simple stream wrapper that provides colorama-compatible interface"""

    def __init__(self, wrapped, autoreset=False):
        self.wrapped = wrapped
        self.autoreset = autoreset
        self._stream = wrapped

    def write(self, text):
        self.wrapped.write(text)
        if self.autoreset and text and not text.endswith('\033[0m'):
            self.wrapped.write('\033[0m')

    def flush(self):
        if hasattr(self.wrapped, 'flush'):
            self.wrapped.flush()

    def __getattr__(self, name):
        return getattr(self.wrapped, name)


def init(autoreset=False, convert=None, strip=None, wrap=True):
    """
    Initialize colorama.

    Parameters:
    -----------
    autoreset : bool
        If True, automatically reset style after each print
    convert : bool
        If True, convert ANSI codes to Win32 calls (Windows only)
        If None, auto-detect
    strip : bool
        If True, strip ANSI codes from output
        If None, strip if output is not a tty
    wrap : bool
        If True, wrap stdout/stderr with ANSI handling

    On Windows, this enables ANSI code processing or wraps streams.
    On other platforms, this is mostly a no-op.
    """
    global _initialized, _original_stdout, _original_stderr, _wrap_enabled

    if _initialized:
        return

    _wrap_enabled = wrap

    if wrap:
        _original_stdout = sys.stdout
        _original_stderr = sys.stderr

        if _is_windows() and not _supports_ansi():
            # Wrap streams on Windows without native ANSI support
            sys.stdout = AnsiToWin32(sys.stdout, convert=convert, strip=strip, autoreset=autoreset)
            sys.stderr = AnsiToWin32(sys.stderr, convert=convert, strip=strip, autoreset=autoreset)
        elif autoreset:
            # Just wrap for autoreset functionality
            sys.stdout = StreamWrapper(sys.stdout, autoreset=autoreset)
            sys.stderr = StreamWrapper(sys.stderr, autoreset=autoreset)

    _initialized = True

    # Register cleanup on exit
    atexit.register(deinit)


def deinit():
    """
    Restore stdout and stderr to their original values.
    """
    global _initialized, _original_stdout, _original_stderr

    if not _initialized:
        return

    if _original_stdout is not None:
        sys.stdout = _original_stdout
        _original_stdout = None

    if _original_stderr is not None:
        sys.stderr = _original_stderr
        _original_stderr = None

    _initialized = False


def reinit():
    """
    Re-initialize colorama after deinit().
    """
    global _initialized
    if _initialized:
        deinit()
    _initialized = False
    init()


def just_fix_windows_console():
    """
    Enable ANSI code support in Windows console without wrapping streams.
    This is the recommended approach for modern Windows (10+).
    """
    if _is_windows():
        _supports_ansi()  # This enables VT processing as a side effect
