"""
mymatplotlib - Your custom matplotlib library

A simple plotting library for creating visualizations.
"""

from .figure import Figure, Axes, subplots, Line2D, Patch, Rectangle, Text, Legend
from .colors import (
    to_hex, to_rgba, Colormap, Cycler, get_cmap,
    NAMED_COLORS, DEFAULT_COLORS, LINE_STYLES, MARKERS, COLORMAPS,
    parse_fmt
)
from .backend import save_figure, render_svg, render_text, show_figure
from . import pyplot

# Version
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

__all__ = [
    # Figure and Axes
    'Figure', 'Axes', 'subplots',

    # Artists
    'Line2D', 'Patch', 'Rectangle', 'Text', 'Legend',

    # Colors
    'to_hex', 'to_rgba', 'Colormap', 'Cycler', 'get_cmap',
    'NAMED_COLORS', 'DEFAULT_COLORS', 'LINE_STYLES', 'MARKERS', 'COLORMAPS',

    # Backend
    'save_figure', 'render_svg', 'render_text', 'show_figure',

    # Pyplot module
    'pyplot',
]
