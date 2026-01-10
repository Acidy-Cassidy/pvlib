"""
mycolorama - Your custom colorama library

Cross-platform colored terminal text using ANSI escape sequences.
"""

from .ansi import Fore, Back, Style, Cursor
from .ansi import code_to_chars, set_title, clear_screen, clear_line
from .initialise import init, deinit, reinit, just_fix_windows_console

# Version
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

__all__ = [
    'Fore',
    'Back',
    'Style',
    'Cursor',
    'init',
    'deinit',
    'reinit',
    'just_fix_windows_console',
    'code_to_chars',
    'set_title',
    'clear_screen',
    'clear_line',
]
