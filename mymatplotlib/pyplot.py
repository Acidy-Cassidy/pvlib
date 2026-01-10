"""
mymatplotlib.pyplot

State-based interface for matplotlib, similar to MATLAB.
"""

from typing import Optional, Tuple, List, Union, Any

from .figure import Figure, Axes, subplots as _subplots
from .colors import get_cmap, COLORMAPS
from .backend import show_figure, save_figure

# Global state
_current_figure: Optional[Figure] = None
_figures: List[Figure] = []


def figure(num=None, figsize: Tuple[float, float] = None, dpi: int = 100,
           facecolor: str = 'white', **kwargs) -> Figure:
    """Create a new figure or activate existing one"""
    global _current_figure

    fig = Figure(figsize=figsize, dpi=dpi, facecolor=facecolor, **kwargs)
    _figures.append(fig)
    _current_figure = fig

    return fig


def gcf() -> Figure:
    """Get current figure, creating one if necessary"""
    global _current_figure

    if _current_figure is None:
        _current_figure = figure()

    return _current_figure


def gca() -> Axes:
    """Get current axes, creating one if necessary"""
    fig = gcf()
    return fig.gca()


def subplot(*args, **kwargs) -> Axes:
    """Add a subplot to the current figure"""
    fig = gcf()
    return fig.add_subplot(*args, **kwargs)


def subplots(nrows: int = 1, ncols: int = 1, figsize: Tuple[float, float] = None,
             **kwargs) -> Tuple[Figure, Union[Axes, List[Axes]]]:
    """Create a figure and subplots"""
    global _current_figure

    fig, axes = _subplots(nrows, ncols, figsize=figsize, **kwargs)
    _figures.append(fig)
    _current_figure = fig

    return fig, axes


def plot(*args, **kwargs) -> List:
    """Plot lines on current axes"""
    ax = gca()
    return ax.plot(*args, **kwargs)


def scatter(x, y, s=None, c=None, marker='o', **kwargs):
    """Create scatter plot on current axes"""
    ax = gca()
    return ax.scatter(x, y, s=s, c=c, marker=marker, **kwargs)


def bar(x, height, width=0.8, bottom=None, **kwargs):
    """Create bar chart on current axes"""
    ax = gca()
    return ax.bar(x, height, width=width, bottom=bottom, **kwargs)


def barh(y, width, height=0.8, left=None, **kwargs):
    """Create horizontal bar chart on current axes"""
    ax = gca()
    return ax.barh(y, width, height=height, left=left, **kwargs)


def hist(x, bins=10, range=None, density=False, **kwargs):
    """Create histogram on current axes"""
    ax = gca()
    return ax.hist(x, bins=bins, range=range, density=density, **kwargs)


def pie(x, labels=None, autopct=None, **kwargs):
    """Create pie chart on current axes"""
    ax = gca()
    return ax.pie(x, labels=labels, autopct=autopct, **kwargs)


def imshow(X, cmap='viridis', aspect='equal', **kwargs):
    """Display image on current axes"""
    ax = gca()
    return ax.imshow(X, cmap=cmap, aspect=aspect, **kwargs)


def fill(x, y, **kwargs):
    """Fill area under curve"""
    ax = gca()
    return ax.fill(x, y, **kwargs)


def fill_between(x, y1, y2=0, **kwargs):
    """Fill between two curves"""
    ax = gca()
    return ax.fill_between(x, y1, y2, **kwargs)


def axhline(y=0, **kwargs):
    """Add horizontal line"""
    ax = gca()
    return ax.axhline(y, **kwargs)


def axvline(x=0, **kwargs):
    """Add vertical line"""
    ax = gca()
    return ax.axvline(x, **kwargs)


def text(x: float, y: float, s: str, **kwargs):
    """Add text to axes"""
    ax = gca()
    return ax.text(x, y, s, **kwargs)


def annotate(text: str, xy: Tuple, xytext: Tuple = None, **kwargs):
    """Add annotation"""
    ax = gca()
    return ax.annotate(text, xy, xytext, **kwargs)


def xlabel(label: str, **kwargs):
    """Set x-axis label"""
    ax = gca()
    ax.set_xlabel(label, **kwargs)


def ylabel(label: str, **kwargs):
    """Set y-axis label"""
    ax = gca()
    ax.set_ylabel(label, **kwargs)


def title(label: str, **kwargs):
    """Set axes title"""
    ax = gca()
    ax.set_title(label, **kwargs)


def suptitle(t: str, **kwargs):
    """Set figure title"""
    fig = gcf()
    fig.suptitle(t, **kwargs)


def xlim(*args, **kwargs):
    """Set or get x-axis limits"""
    ax = gca()
    if args or kwargs:
        ax.set_xlim(*args, **kwargs)
    return ax.get_xlim()


def ylim(*args, **kwargs):
    """Set or get y-axis limits"""
    ax = gca()
    if args or kwargs:
        ax.set_ylim(*args, **kwargs)
    return ax.get_ylim()


def xticks(ticks=None, labels=None, **kwargs):
    """Set x-axis ticks"""
    ax = gca()
    if ticks is not None:
        ax.set_xticks(ticks, labels)
    return ax._xticks


def yticks(ticks=None, labels=None, **kwargs):
    """Set y-axis ticks"""
    ax = gca()
    if ticks is not None:
        ax.set_yticks(ticks, labels)
    return ax._yticks


def legend(*args, **kwargs):
    """Add legend to axes"""
    ax = gca()
    return ax.legend(*args, **kwargs)


def grid(visible=True, **kwargs):
    """Configure grid"""
    ax = gca()
    ax.grid(visible, **kwargs)


def tight_layout(**kwargs):
    """Adjust subplot parameters"""
    fig = gcf()
    fig.tight_layout(**kwargs)


def savefig(fname: str, dpi: int = None, format: str = None, **kwargs):
    """Save figure to file"""
    fig = gcf()
    fig.savefig(fname, dpi=dpi, format=format, **kwargs)


def show():
    """Display figure (prints summary in this implementation)"""
    fig = gcf()
    show_figure(fig)


def close(fig=None):
    """Close figure"""
    global _current_figure, _figures

    if fig is None:
        fig = _current_figure

    if fig in _figures:
        _figures.remove(fig)

    if _current_figure is fig:
        _current_figure = _figures[-1] if _figures else None


def clf():
    """Clear current figure"""
    fig = gcf()
    fig.clear()


def cla():
    """Clear current axes"""
    ax = gca()
    ax.clear()


def axis(option=None):
    """Set axis properties"""
    ax = gca()

    if option == 'off':
        ax.set_axis_off()
    elif option == 'on':
        ax.set_axis_on()
    elif option == 'equal':
        ax.set_aspect('equal')
    elif option == 'tight':
        pass  # Use data limits
    elif isinstance(option, (list, tuple)) and len(option) == 4:
        ax.set_xlim(option[0], option[1])
        ax.set_ylim(option[2], option[3])

    return ax.get_xlim() + ax.get_ylim()


def colorbar(mappable=None, **kwargs):
    """Add colorbar (placeholder)"""
    print("Colorbar: (not fully implemented in mymatplotlib)")
    return None


# Style functions
def style_use(style: str):
    """Use a predefined style (placeholder)"""
    pass


def rc(group: str, **kwargs):
    """Set rc parameters (placeholder)"""
    pass


def rcParams():
    """Get rc parameters (placeholder)"""
    return {}


# Numpy-like functions for convenience
def linspace(start, stop, num=50):
    """Generate linearly spaced values"""
    if num < 2:
        return [start]
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]


def arange(start, stop=None, step=1):
    """Generate range of values"""
    if stop is None:
        start, stop = 0, start
    result = []
    val = start
    while val < stop:
        result.append(val)
        val += step
    return result


def sin(x):
    """Sine function"""
    import math
    if hasattr(x, '__iter__'):
        return [math.sin(v) for v in x]
    return math.sin(x)


def cos(x):
    """Cosine function"""
    import math
    if hasattr(x, '__iter__'):
        return [math.cos(v) for v in x]
    return math.cos(x)


def sqrt(x):
    """Square root"""
    import math
    if hasattr(x, '__iter__'):
        return [math.sqrt(v) for v in x]
    return math.sqrt(x)


def exp(x):
    """Exponential"""
    import math
    if hasattr(x, '__iter__'):
        return [math.exp(v) for v in x]
    return math.exp(x)


# Constants
pi = 3.141592653589793
