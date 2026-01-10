"""
mymatplotlib colors and styling

Color definitions and style utilities.
"""

from typing import Union, Tuple, List, Optional

# Named colors (subset of CSS colors)
NAMED_COLORS = {
    'b': '#0000FF',
    'g': '#008000',
    'r': '#FF0000',
    'c': '#00FFFF',
    'm': '#FF00FF',
    'y': '#FFFF00',
    'k': '#000000',
    'w': '#FFFFFF',
    'blue': '#0000FF',
    'green': '#008000',
    'red': '#FF0000',
    'cyan': '#00FFFF',
    'magenta': '#FF00FF',
    'yellow': '#FFFF00',
    'black': '#000000',
    'white': '#FFFFFF',
    'orange': '#FFA500',
    'purple': '#800080',
    'brown': '#A52A2A',
    'pink': '#FFC0CB',
    'gray': '#808080',
    'grey': '#808080',
    'olive': '#808000',
    'navy': '#000080',
    'teal': '#008080',
    'maroon': '#800000',
    'lime': '#00FF00',
    'aqua': '#00FFFF',
    'silver': '#C0C0C0',
    'fuchsia': '#FF00FF',
}

# Default color cycle (tab10 colors)
DEFAULT_COLORS = [
    '#1f77b4',  # blue
    '#ff7f0e',  # orange
    '#2ca02c',  # green
    '#d62728',  # red
    '#9467bd',  # purple
    '#8c564b',  # brown
    '#e377c2',  # pink
    '#7f7f7f',  # gray
    '#bcbd22',  # olive
    '#17becf',  # cyan
]

# Line styles
LINE_STYLES = {
    '-': 'solid',
    '--': 'dashed',
    '-.': 'dashdot',
    ':': 'dotted',
    'solid': 'solid',
    'dashed': 'dashed',
    'dashdot': 'dashdot',
    'dotted': 'dotted',
    '': 'none',
    ' ': 'none',
    'none': 'none',
}

# Markers
MARKERS = {
    '.': 'point',
    ',': 'pixel',
    'o': 'circle',
    'v': 'triangle_down',
    '^': 'triangle_up',
    '<': 'triangle_left',
    '>': 'triangle_right',
    's': 'square',
    'p': 'pentagon',
    '*': 'star',
    'h': 'hexagon1',
    'H': 'hexagon2',
    '+': 'plus',
    'x': 'x',
    'D': 'diamond',
    'd': 'thin_diamond',
    '|': 'vline',
    '_': 'hline',
    '': 'none',
    ' ': 'none',
    'none': 'none',
}


def to_hex(color: Union[str, Tuple, List]) -> str:
    """Convert color to hex format"""
    if isinstance(color, str):
        # Already hex
        if color.startswith('#'):
            return color
        # Named color
        if color.lower() in NAMED_COLORS:
            return NAMED_COLORS[color.lower()]
        # Single letter
        if color in NAMED_COLORS:
            return NAMED_COLORS[color]
        return color

    # RGB or RGBA tuple (0-1 range)
    if isinstance(color, (tuple, list)):
        if len(color) >= 3:
            r, g, b = color[:3]
            # Convert 0-1 to 0-255 if needed
            if all(0 <= c <= 1 for c in (r, g, b)):
                r, g, b = int(r * 255), int(g * 255), int(b * 255)
            return f'#{int(r):02x}{int(g):02x}{int(b):02x}'

    return '#000000'


def to_rgba(color: Union[str, Tuple, List], alpha: float = 1.0) -> Tuple[float, float, float, float]:
    """Convert color to RGBA tuple (0-1 range)"""
    hex_color = to_hex(color)

    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)

        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        return (r, g, b, alpha)

    return (0, 0, 0, alpha)


class Colormap:
    """Simple colormap implementation"""

    def __init__(self, name: str, colors: List[str]):
        self.name = name
        self.colors = colors

    def __call__(self, value: float) -> str:
        """Map value (0-1) to color"""
        value = max(0, min(1, value))
        index = int(value * (len(self.colors) - 1))
        return self.colors[index]


# Built-in colormaps
COLORMAPS = {
    'viridis': Colormap('viridis', [
        '#440154', '#482878', '#3e4989', '#31688e', '#26828e',
        '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'
    ]),
    'plasma': Colormap('plasma', [
        '#0d0887', '#46039f', '#7201a8', '#9c179e', '#bd3786',
        '#d8576b', '#ed7953', '#fb9f3a', '#fdca26', '#f0f921'
    ]),
    'inferno': Colormap('inferno', [
        '#000004', '#1b0c41', '#4a0c6b', '#781c6d', '#a52c60',
        '#cf4446', '#ed6925', '#fb9b06', '#f7d13d', '#fcffa4'
    ]),
    'magma': Colormap('magma', [
        '#000004', '#180f3d', '#440f76', '#721f81', '#9e2f7f',
        '#cd4071', '#f1605d', '#fd9668', '#feca8d', '#fcfdbf'
    ]),
    'hot': Colormap('hot', [
        '#000000', '#330000', '#660000', '#990000', '#cc0000',
        '#ff0000', '#ff3300', '#ff6600', '#ff9900', '#ffcc00',
        '#ffff00', '#ffff55', '#ffffaa', '#ffffff'
    ]),
    'cool': Colormap('cool', [
        '#00ffff', '#33ccff', '#6699ff', '#9966ff', '#cc33ff', '#ff00ff'
    ]),
    'gray': Colormap('gray', [
        '#000000', '#333333', '#666666', '#999999', '#cccccc', '#ffffff'
    ]),
    'jet': Colormap('jet', [
        '#000080', '#0000ff', '#0080ff', '#00ffff', '#80ff80',
        '#ffff00', '#ff8000', '#ff0000', '#800000'
    ]),
}


def get_cmap(name: str = 'viridis') -> Colormap:
    """Get a colormap by name"""
    return COLORMAPS.get(name, COLORMAPS['viridis'])


class Cycler:
    """Color cycler for automatic color assignment"""

    def __init__(self, colors: Optional[List[str]] = None):
        self.colors = colors or DEFAULT_COLORS
        self.index = 0

    def __next__(self) -> str:
        color = self.colors[self.index % len(self.colors)]
        self.index += 1
        return color

    def reset(self):
        self.index = 0


def parse_fmt(fmt: str) -> dict:
    """
    Parse a format string like 'ro-' into components.

    Returns dict with 'color', 'marker', 'linestyle'
    """
    result = {'color': None, 'marker': None, 'linestyle': None}

    i = 0
    while i < len(fmt):
        c = fmt[i]

        # Check for color (single letter)
        if c in 'bgrcmykw':
            result['color'] = c
            i += 1
            continue

        # Check for linestyle (can be 1 or 2 chars)
        if i + 1 < len(fmt) and fmt[i:i+2] in LINE_STYLES:
            result['linestyle'] = fmt[i:i+2]
            i += 2
            continue
        if c in LINE_STYLES:
            result['linestyle'] = c
            i += 1
            continue

        # Check for marker
        if c in MARKERS:
            result['marker'] = c
            i += 1
            continue

        i += 1

    return result
