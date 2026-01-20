"""
Color definitions for reportlab.
"""


class Color:
    """
    RGB color class.
    """

    def __init__(self, red=0, green=0, blue=0, alpha=1):
        """
        Initialize color with RGB values.

        Args:
            red: Red component (0-1)
            green: Green component (0-1)
            blue: Blue component (0-1)
            alpha: Alpha/opacity (0-1)
        """
        self.red = max(0, min(1, red))
        self.green = max(0, min(1, green))
        self.blue = max(0, min(1, blue))
        self.alpha = max(0, min(1, alpha))

    def __repr__(self):
        return f"Color({self.red}, {self.green}, {self.blue}, alpha={self.alpha})"

    def hexval(self):
        """Return hex color string."""
        r = int(self.red * 255)
        g = int(self.green * 255)
        b = int(self.blue * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def clone(self, **kwargs):
        """Clone color with optional modifications."""
        return Color(
            kwargs.get("red", self.red),
            kwargs.get("green", self.green),
            kwargs.get("blue", self.blue),
            kwargs.get("alpha", self.alpha),
        )

    @property
    def rgb(self):
        """Return (r, g, b) tuple."""
        return (self.red, self.green, self.blue)

    @property
    def rgba(self):
        """Return (r, g, b, a) tuple."""
        return (self.red, self.green, self.blue, self.alpha)


class CMYKColor(Color):
    """
    CMYK color class.
    """

    def __init__(self, cyan=0, magenta=0, yellow=0, black=0, alpha=1):
        """
        Initialize CMYK color.

        Args:
            cyan: Cyan component (0-1)
            magenta: Magenta component (0-1)
            yellow: Yellow component (0-1)
            black: Black component (0-1)
            alpha: Alpha/opacity (0-1)
        """
        self.cyan = max(0, min(1, cyan))
        self.magenta = max(0, min(1, magenta))
        self.yellow = max(0, min(1, yellow))
        self.black = max(0, min(1, black))

        # Convert to RGB for compatibility
        r = (1 - cyan) * (1 - black)
        g = (1 - magenta) * (1 - black)
        b = (1 - yellow) * (1 - black)
        super().__init__(r, g, b, alpha)

    def __repr__(self):
        return f"CMYKColor({self.cyan}, {self.magenta}, {self.yellow}, {self.black})"


def HexColor(val, hasAlpha=False):
    """
    Create a color from a hex string.

    Args:
        val: Hex color string (#RGB, #RRGGBB, or #RRGGBBAA)
        hasAlpha: If True, parse alpha from string

    Returns:
        Color object
    """
    if isinstance(val, Color):
        return val

    if isinstance(val, int):
        # Interpret as 0xRRGGBB
        r = ((val >> 16) & 0xFF) / 255.0
        g = ((val >> 8) & 0xFF) / 255.0
        b = (val & 0xFF) / 255.0
        return Color(r, g, b)

    val = val.strip()
    if val.startswith("#"):
        val = val[1:]
    elif val.startswith("0x"):
        val = val[2:]

    if len(val) == 3:
        # #RGB format
        r = int(val[0] * 2, 16) / 255.0
        g = int(val[1] * 2, 16) / 255.0
        b = int(val[2] * 2, 16) / 255.0
        return Color(r, g, b)
    elif len(val) == 6:
        # #RRGGBB format
        r = int(val[0:2], 16) / 255.0
        g = int(val[2:4], 16) / 255.0
        b = int(val[4:6], 16) / 255.0
        return Color(r, g, b)
    elif len(val) == 8 and hasAlpha:
        # #RRGGBBAA format
        r = int(val[0:2], 16) / 255.0
        g = int(val[2:4], 16) / 255.0
        b = int(val[4:6], 16) / 255.0
        a = int(val[6:8], 16) / 255.0
        return Color(r, g, b, a)

    return Color(0, 0, 0)


def toColor(val, default=None):
    """
    Convert a value to a Color object.

    Args:
        val: Color, hex string, tuple, or name
        default: Default color if conversion fails

    Returns:
        Color object
    """
    if val is None:
        return default
    if isinstance(val, Color):
        return val
    if isinstance(val, str):
        if val.startswith("#") or val.startswith("0x"):
            return HexColor(val)
        # Try named color
        val_lower = val.lower()
        if val_lower in _named_colors:
            return _named_colors[val_lower]
    if isinstance(val, (tuple, list)):
        if len(val) == 3:
            return Color(*val)
        elif len(val) == 4:
            return Color(*val)
    return default


# Named colors
black = Color(0, 0, 0)
white = Color(1, 1, 1)
red = Color(1, 0, 0)
green = Color(0, 0.5, 0)
blue = Color(0, 0, 1)
yellow = Color(1, 1, 0)
cyan = Color(0, 1, 1)
magenta = Color(1, 0, 1)
orange = Color(1, 0.647, 0)
pink = Color(1, 0.753, 0.796)
purple = Color(0.5, 0, 0.5)
brown = Color(0.647, 0.165, 0.165)
gray = grey = Color(0.5, 0.5, 0.5)
lightgrey = lightgray = Color(0.827, 0.827, 0.827)
darkgrey = darkgray = Color(0.663, 0.663, 0.663)
silver = Color(0.753, 0.753, 0.753)
gold = Color(1, 0.843, 0)
navy = Color(0, 0, 0.5)
maroon = Color(0.5, 0, 0)
olive = Color(0.5, 0.5, 0)
teal = Color(0, 0.5, 0.5)
aqua = Color(0, 1, 1)
lime = Color(0, 1, 0)
fuchsia = Color(1, 0, 1)
transparent = Color(0, 0, 0, 0)

# Reportlab-specific colors
fidblue = Color(0.259, 0.522, 0.957)
fidred = Color(0.886, 0.208, 0.259)
fidlightblue = Color(0.678, 0.847, 0.902)

# Named color lookup
_named_colors = {
    "black": black,
    "white": white,
    "red": red,
    "green": green,
    "blue": blue,
    "yellow": yellow,
    "cyan": cyan,
    "magenta": magenta,
    "orange": orange,
    "pink": pink,
    "purple": purple,
    "brown": brown,
    "gray": gray,
    "grey": grey,
    "lightgray": lightgray,
    "lightgrey": lightgrey,
    "darkgray": darkgray,
    "darkgrey": darkgrey,
    "silver": silver,
    "gold": gold,
    "navy": navy,
    "maroon": maroon,
    "olive": olive,
    "teal": teal,
    "aqua": aqua,
    "lime": lime,
    "fuchsia": fuchsia,
    "transparent": transparent,
}

# All named colors
getAllNamedColors = lambda: dict(_named_colors)
