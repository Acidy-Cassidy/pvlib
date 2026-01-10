"""
mycolorama ANSI escape codes

Defines ANSI escape sequences for colors, styles, and cursor control.
"""

# ANSI escape sequence prefix
CSI = '\033['
OSC = '\033]'
BEL = '\a'


def code_to_chars(code):
    """Convert an ANSI code to escape sequence"""
    return CSI + str(code) + 'm'


def set_title(title):
    """Set terminal window title"""
    return OSC + '2;' + title + BEL


def clear_screen(mode=2):
    """Clear screen: 0=to end, 1=to start, 2=entire"""
    return CSI + str(mode) + 'J'


def clear_line(mode=2):
    """Clear line: 0=to end, 1=to start, 2=entire"""
    return CSI + str(mode) + 'K'


class AnsiCodes:
    """Base class for ANSI code containers"""

    def __init__(self):
        # Convert all class attributes to escape sequences
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                if isinstance(value, int):
                    setattr(self, name, code_to_chars(value))


class AnsiFore(AnsiCodes):
    """ANSI foreground color codes"""
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    RESET = 39

    # Light/bright variants
    LIGHTBLACK_EX = 90
    LIGHTRED_EX = 91
    LIGHTGREEN_EX = 92
    LIGHTYELLOW_EX = 93
    LIGHTBLUE_EX = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX = 96
    LIGHTWHITE_EX = 97


class AnsiBack(AnsiCodes):
    """ANSI background color codes"""
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47
    RESET = 49

    # Light/bright variants
    LIGHTBLACK_EX = 100
    LIGHTRED_EX = 101
    LIGHTGREEN_EX = 102
    LIGHTYELLOW_EX = 103
    LIGHTBLUE_EX = 104
    LIGHTMAGENTA_EX = 105
    LIGHTCYAN_EX = 106
    LIGHTWHITE_EX = 107


class AnsiStyle(AnsiCodes):
    """ANSI style codes"""
    BRIGHT = 1
    DIM = 2
    NORMAL = 22
    RESET_ALL = 0


class AnsiCursor:
    """ANSI cursor control sequences"""

    @staticmethod
    def UP(n=1):
        """Move cursor up n lines"""
        return CSI + str(n) + 'A'

    @staticmethod
    def DOWN(n=1):
        """Move cursor down n lines"""
        return CSI + str(n) + 'B'

    @staticmethod
    def FORWARD(n=1):
        """Move cursor forward n columns"""
        return CSI + str(n) + 'C'

    @staticmethod
    def BACK(n=1):
        """Move cursor back n columns"""
        return CSI + str(n) + 'D'

    @staticmethod
    def POS(x=1, y=1):
        """Set cursor position to (x, y)"""
        return CSI + str(y) + ';' + str(x) + 'H'


# Create singleton instances
Fore = AnsiFore()
Back = AnsiBack()
Style = AnsiStyle()
Cursor = AnsiCursor()
