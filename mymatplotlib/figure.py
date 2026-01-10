"""
mymatplotlib Figure and Axes classes

Core plotting classes.
"""

from typing import Optional, Tuple, List, Union, Any
import math

# Store built-in range to avoid shadowing by parameter names
_range = range

from .colors import (
    to_hex, Cycler, DEFAULT_COLORS, parse_fmt,
    LINE_STYLES, MARKERS, get_cmap
)


class Artist:
    """Base class for all drawable objects"""

    def __init__(self):
        self.visible = True
        self.zorder = 0
        self.label = ''
        self._axes = None

    def set_visible(self, visible: bool):
        self.visible = visible

    def get_visible(self) -> bool:
        return self.visible

    def set_label(self, label: str):
        self.label = label

    def get_label(self) -> str:
        return self.label


class Line2D(Artist):
    """A line in 2D space"""

    def __init__(self, xdata: List, ydata: List, **kwargs):
        super().__init__()
        self.xdata = list(xdata)
        self.ydata = list(ydata)
        self.color = kwargs.get('color', kwargs.get('c', '#1f77b4'))
        self.linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        self.linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.5))
        self.marker = kwargs.get('marker', '')
        self.markersize = kwargs.get('markersize', kwargs.get('ms', 6))
        self.markerfacecolor = kwargs.get('markerfacecolor', kwargs.get('mfc', self.color))
        self.markeredgecolor = kwargs.get('markeredgecolor', kwargs.get('mec', self.color))
        self.alpha = kwargs.get('alpha', 1.0)
        self.label = kwargs.get('label', '')

    def set_data(self, xdata: List, ydata: List):
        self.xdata = list(xdata)
        self.ydata = list(ydata)

    def get_data(self) -> Tuple[List, List]:
        return self.xdata, self.ydata

    def get_xdata(self) -> List:
        return self.xdata

    def get_ydata(self) -> List:
        return self.ydata


class Patch(Artist):
    """A 2D patch (rectangle, circle, etc.)"""

    def __init__(self, **kwargs):
        super().__init__()
        self.facecolor = kwargs.get('facecolor', kwargs.get('fc', '#1f77b4'))
        self.edgecolor = kwargs.get('edgecolor', kwargs.get('ec', 'none'))
        self.linewidth = kwargs.get('linewidth', kwargs.get('lw', 1))
        self.alpha = kwargs.get('alpha', 1.0)


class Rectangle(Patch):
    """A rectangle patch"""

    def __init__(self, xy: Tuple[float, float], width: float, height: float, **kwargs):
        super().__init__(**kwargs)
        self.xy = xy
        self.width = width
        self.height = height


class Text(Artist):
    """Text element"""

    def __init__(self, x: float, y: float, text: str, **kwargs):
        super().__init__()
        self.x = x
        self.y = y
        self.text = text
        self.fontsize = kwargs.get('fontsize', kwargs.get('size', 12))
        self.color = kwargs.get('color', 'black')
        self.ha = kwargs.get('ha', kwargs.get('horizontalalignment', 'left'))
        self.va = kwargs.get('va', kwargs.get('verticalalignment', 'baseline'))
        self.rotation = kwargs.get('rotation', 0)
        self.fontweight = kwargs.get('fontweight', kwargs.get('weight', 'normal'))


class Legend(Artist):
    """Legend for the axes"""

    def __init__(self, handles: List, labels: List, **kwargs):
        super().__init__()
        self.handles = handles
        self.labels = labels
        self.loc = kwargs.get('loc', 'best')
        self.fontsize = kwargs.get('fontsize', 10)
        self.frameon = kwargs.get('frameon', True)
        self.title = kwargs.get('title', None)


class Axes:
    """
    The Axes contains most of the figure elements and plotting methods.
    """

    def __init__(self, fig: 'Figure', rect: Tuple[float, float, float, float] = None,
                 **kwargs):
        self.figure = fig
        self.rect = rect or (0.125, 0.11, 0.775, 0.77)  # left, bottom, width, height

        # Data
        self.lines: List[Line2D] = []
        self.patches: List[Patch] = []
        self.texts: List[Text] = []
        self.images: List[Any] = []
        self._legend: Optional[Legend] = None

        # Axis properties
        self._xlim = None
        self._ylim = None
        self._xlabel = ''
        self._ylabel = ''
        self._title = ''

        # Grid
        self._grid_on = False
        self._grid_kwargs = {}

        # Color cycler
        self._color_cycler = Cycler()

        # Axis visibility
        self._frame_on = True
        self._axis_on = True

        # Ticks
        self._xticks = None
        self._yticks = None
        self._xticklabels = None
        self._yticklabels = None

        # Aspect ratio
        self._aspect = 'auto'

        # Subplot position
        self._subplotspec = kwargs.get('subplotspec', None)

    def _auto_color(self) -> str:
        """Get next color from cycle"""
        return next(self._color_cycler)

    def plot(self, *args, **kwargs) -> List[Line2D]:
        """
        Plot lines and/or markers.

        Call signatures:
            plot(y)
            plot(x, y)
            plot(x, y, fmt)
            plot(x1, y1, fmt1, x2, y2, fmt2, ...)
        """
        lines = []

        # Parse arguments
        i = 0
        while i < len(args):
            # Get x, y data
            if i + 1 < len(args) and not isinstance(args[i + 1], str):
                x = args[i]
                y = args[i + 1]
                i += 2
            else:
                y = args[i]
                x = list(range(len(y)))
                i += 1

            # Get format string
            fmt = ''
            if i < len(args) and isinstance(args[i], str):
                fmt = args[i]
                i += 1

            # Parse format string
            fmt_dict = parse_fmt(fmt)

            # Build line kwargs
            line_kwargs = kwargs.copy()
            if fmt_dict['color'] and 'color' not in kwargs:
                line_kwargs['color'] = fmt_dict['color']
            if fmt_dict['linestyle'] and 'linestyle' not in kwargs:
                line_kwargs['linestyle'] = fmt_dict['linestyle']
            if fmt_dict['marker'] and 'marker' not in kwargs:
                line_kwargs['marker'] = fmt_dict['marker']

            # Auto color if not specified
            if 'color' not in line_kwargs and 'c' not in line_kwargs:
                line_kwargs['color'] = self._auto_color()

            # Create line
            line = Line2D(x, y, **line_kwargs)
            line._axes = self
            self.lines.append(line)
            lines.append(line)

            # Update axis limits
            self._update_limits(x, y)

        return lines

    def scatter(self, x, y, s=None, c=None, marker='o', **kwargs) -> Any:
        """Create a scatter plot"""
        if s is None:
            s = 20

        color = c if c is not None else kwargs.get('color', self._auto_color())

        # Create as line with markers only
        line = Line2D(x, y,
                     color=color,
                     linestyle='',
                     marker=marker,
                     markersize=math.sqrt(s) if isinstance(s, (int, float)) else 6,
                     **kwargs)
        line._axes = self
        self.lines.append(line)

        self._update_limits(x, y)

        return line

    def bar(self, x, height, width=0.8, bottom=None, **kwargs) -> List[Rectangle]:
        """Create a bar chart"""
        if bottom is None:
            bottom = [0] * len(x)
        elif not hasattr(bottom, '__len__'):
            bottom = [bottom] * len(x)

        color = kwargs.get('color', self._auto_color())
        bars = []

        for i, (xi, hi, bi) in enumerate(zip(x, height, bottom)):
            rect = Rectangle(
                (xi - width / 2, bi),
                width,
                hi,
                facecolor=color,
                edgecolor=kwargs.get('edgecolor', 'none'),
                alpha=kwargs.get('alpha', 1.0),
                label=kwargs.get('label', '') if i == 0 else ''
            )
            rect._axes = self
            self.patches.append(rect)
            bars.append(rect)

        # Update limits
        x_vals = [xi for xi in x]
        y_vals = [bi + hi for bi, hi in zip(bottom, height)]
        self._update_limits(x_vals, y_vals)

        return bars

    def barh(self, y, width, height=0.8, left=None, **kwargs) -> List[Rectangle]:
        """Create a horizontal bar chart"""
        if left is None:
            left = [0] * len(y)
        elif not hasattr(left, '__len__'):
            left = [left] * len(y)

        color = kwargs.get('color', self._auto_color())
        bars = []

        for i, (yi, wi, li) in enumerate(zip(y, width, left)):
            rect = Rectangle(
                (li, yi - height / 2),
                wi,
                height,
                facecolor=color,
                edgecolor=kwargs.get('edgecolor', 'none'),
                alpha=kwargs.get('alpha', 1.0)
            )
            rect._axes = self
            self.patches.append(rect)
            bars.append(rect)

        return bars

    def hist(self, x, bins=10, range=None, density=False, **kwargs):
        """Create a histogram"""
        # Save range parameter to avoid shadowing built-in
        data_range = range
        if data_range is None:
            data_range = (min(x), max(x))

        bin_edges = []
        bin_width = (data_range[1] - data_range[0]) / bins
        for i in _range(bins + 1):
            bin_edges.append(data_range[0] + i * bin_width)

        # Count values in each bin
        counts = [0] * bins
        for val in x:
            for i in _range(bins):
                if bin_edges[i] <= val < bin_edges[i + 1]:
                    counts[i] += 1
                    break
            else:
                if val == bin_edges[-1]:
                    counts[-1] += 1

        if density:
            total = sum(counts) * bin_width
            counts = [c / total if total > 0 else 0 for c in counts]

        # Create bars
        centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in _range(bins)]
        bars = self.bar(centers, counts, width=bin_width * 0.9, **kwargs)

        return counts, bin_edges, bars

    def pie(self, x, labels=None, autopct=None, explode=None, **kwargs):
        """Create a pie chart"""
        # Store pie data for rendering
        total = sum(x)
        percentages = [xi / total * 100 for xi in x]

        # This is a simplified representation
        self._pie_data = {
            'values': x,
            'labels': labels or ['' for _ in x],
            'percentages': percentages,
            'autopct': autopct,
            'explode': explode,
            'colors': kwargs.get('colors', DEFAULT_COLORS[:len(x)])
        }

        return None

    def imshow(self, X, cmap='viridis', aspect='equal', **kwargs):
        """Display an image"""
        self._image_data = {
            'data': X,
            'cmap': cmap,
            'aspect': aspect,
            'kwargs': kwargs
        }
        self._aspect = aspect

        if hasattr(X, '__len__') and hasattr(X[0], '__len__'):
            self._xlim = (0, len(X[0]))
            self._ylim = (0, len(X))

        return None

    def fill(self, x, y, **kwargs):
        """Fill area under curve"""
        color = kwargs.get('color', self._auto_color())
        self._fill_data = {
            'x': list(x),
            'y': list(y),
            'color': color,
            'alpha': kwargs.get('alpha', 0.3)
        }
        self._update_limits(x, y)

    def fill_between(self, x, y1, y2=0, **kwargs):
        """Fill between two curves"""
        if not hasattr(y2, '__len__'):
            y2 = [y2] * len(x)

        color = kwargs.get('color', self._auto_color())
        self._fill_between_data = {
            'x': list(x),
            'y1': list(y1),
            'y2': list(y2),
            'color': color,
            'alpha': kwargs.get('alpha', 0.3)
        }
        all_y = list(y1) + list(y2)
        self._update_limits(x, all_y)

    def axhline(self, y=0, **kwargs):
        """Add horizontal line across axes"""
        color = kwargs.get('color', 'black')
        linestyle = kwargs.get('linestyle', '-')
        self._axhlines = getattr(self, '_axhlines', [])
        self._axhlines.append({'y': y, 'color': color, 'linestyle': linestyle})

    def axvline(self, x=0, **kwargs):
        """Add vertical line across axes"""
        color = kwargs.get('color', 'black')
        linestyle = kwargs.get('linestyle', '-')
        self._axvlines = getattr(self, '_axvlines', [])
        self._axvlines.append({'x': x, 'color': color, 'linestyle': linestyle})

    def text(self, x: float, y: float, s: str, **kwargs) -> Text:
        """Add text to axes"""
        text = Text(x, y, s, **kwargs)
        text._axes = self
        self.texts.append(text)
        return text

    def annotate(self, text: str, xy: Tuple, xytext: Tuple = None, **kwargs):
        """Add annotation with optional arrow"""
        if xytext is None:
            xytext = xy
        t = Text(xytext[0], xytext[1], text, **kwargs)
        t._annotation_xy = xy
        self.texts.append(t)
        return t

    def set_xlabel(self, label: str, **kwargs):
        """Set x-axis label"""
        self._xlabel = label
        self._xlabel_kwargs = kwargs

    def set_ylabel(self, label: str, **kwargs):
        """Set y-axis label"""
        self._ylabel = label
        self._ylabel_kwargs = kwargs

    def set_title(self, title: str, **kwargs):
        """Set axes title"""
        self._title = title
        self._title_kwargs = kwargs

    def set_xlim(self, left=None, right=None):
        """Set x-axis limits"""
        if isinstance(left, (tuple, list)):
            left, right = left
        self._xlim = (left, right)

    def set_ylim(self, bottom=None, top=None):
        """Set y-axis limits"""
        if isinstance(bottom, (tuple, list)):
            bottom, top = bottom
        self._ylim = (bottom, top)

    def get_xlim(self) -> Tuple[float, float]:
        """Get x-axis limits"""
        return self._xlim or self._calc_xlim()

    def get_ylim(self) -> Tuple[float, float]:
        """Get y-axis limits"""
        return self._ylim or self._calc_ylim()

    def _calc_xlim(self) -> Tuple[float, float]:
        """Calculate x limits from data"""
        all_x = []
        for line in self.lines:
            all_x.extend(line.xdata)
        if all_x:
            margin = (max(all_x) - min(all_x)) * 0.05 or 0.5
            return (min(all_x) - margin, max(all_x) + margin)
        return (0, 1)

    def _calc_ylim(self) -> Tuple[float, float]:
        """Calculate y limits from data"""
        all_y = []
        for line in self.lines:
            all_y.extend(line.ydata)
        if all_y:
            margin = (max(all_y) - min(all_y)) * 0.05 or 0.5
            return (min(all_y) - margin, max(all_y) + margin)
        return (0, 1)

    def _update_limits(self, x, y):
        """Update limits based on new data"""
        # Auto-scaling happens in _calc_xlim/_calc_ylim
        pass

    def set_xticks(self, ticks, labels=None):
        """Set x-axis tick locations"""
        self._xticks = list(ticks)
        if labels is not None:
            self._xticklabels = list(labels)

    def set_yticks(self, ticks, labels=None):
        """Set y-axis tick locations"""
        self._yticks = list(ticks)
        if labels is not None:
            self._yticklabels = list(labels)

    def set_xticklabels(self, labels):
        """Set x-axis tick labels"""
        self._xticklabels = list(labels)

    def set_yticklabels(self, labels):
        """Set y-axis tick labels"""
        self._yticklabels = list(labels)

    def grid(self, visible=True, **kwargs):
        """Configure grid"""
        self._grid_on = visible
        self._grid_kwargs = kwargs

    def legend(self, *args, **kwargs) -> Legend:
        """Add legend to axes"""
        if args:
            if len(args) >= 2:
                handles, labels = args[0], args[1]
            else:
                labels = args[0]
                handles = [l for l in self.lines if l.label]
        else:
            handles = [l for l in self.lines if l.label]
            labels = [l.label for l in handles]

        self._legend = Legend(handles, labels, **kwargs)
        return self._legend

    def set_aspect(self, aspect):
        """Set aspect ratio"""
        self._aspect = aspect

    def set_axis_off(self):
        """Turn off axis"""
        self._axis_on = False

    def set_axis_on(self):
        """Turn on axis"""
        self._axis_on = True

    def clear(self):
        """Clear the axes"""
        self.lines.clear()
        self.patches.clear()
        self.texts.clear()
        self._legend = None
        self._color_cycler.reset()


class Figure:
    """
    The top-level container for all plot elements.
    """

    def __init__(self, figsize: Tuple[float, float] = None, dpi: int = 100,
                 facecolor: str = 'white', **kwargs):
        self.figsize = figsize or (6.4, 4.8)
        self.dpi = dpi
        self.facecolor = facecolor
        self.axes: List[Axes] = []
        self._suptitle = ''
        self._suptitle_kwargs = {}

    @property
    def width(self) -> float:
        return self.figsize[0]

    @property
    def height(self) -> float:
        return self.figsize[1]

    def add_subplot(self, *args, **kwargs) -> Axes:
        """
        Add a subplot to the figure.

        Call signatures:
            add_subplot(nrows, ncols, index)
            add_subplot(pos)  # e.g., 111
        """
        if len(args) == 1:
            # Single integer like 111
            pos = args[0]
            nrows = pos // 100
            ncols = (pos % 100) // 10
            index = pos % 10
        elif len(args) == 3:
            nrows, ncols, index = args
        else:
            nrows, ncols, index = 1, 1, 1

        # Calculate rect
        row = (index - 1) // ncols
        col = (index - 1) % ncols

        # Spacing
        left_margin = 0.125
        right_margin = 0.1
        bottom_margin = 0.11
        top_margin = 0.12
        wspace = 0.2
        hspace = 0.2

        plot_width = (1 - left_margin - right_margin - wspace * (ncols - 1)) / ncols
        plot_height = (1 - bottom_margin - top_margin - hspace * (nrows - 1)) / nrows

        left = left_margin + col * (plot_width + wspace)
        bottom = bottom_margin + (nrows - 1 - row) * (plot_height + hspace)

        rect = (left, bottom, plot_width, plot_height)

        ax = Axes(self, rect, **kwargs)
        self.axes.append(ax)
        return ax

    def add_axes(self, rect: Tuple[float, float, float, float], **kwargs) -> Axes:
        """Add axes at specified position"""
        ax = Axes(self, rect, **kwargs)
        self.axes.append(ax)
        return ax

    def suptitle(self, t: str, **kwargs):
        """Set figure title"""
        self._suptitle = t
        self._suptitle_kwargs = kwargs

    def tight_layout(self, **kwargs):
        """Adjust subplot parameters for tight layout"""
        # Simplified - just store that it was called
        self._tight_layout = True

    def savefig(self, fname: str, dpi: int = None, format: str = None,
                bbox_inches: str = None, **kwargs):
        """Save figure to file"""
        from .backend import save_figure
        save_figure(self, fname, dpi=dpi or self.dpi, format=format)

    def clear(self):
        """Clear the figure"""
        self.axes.clear()

    def gca(self) -> Axes:
        """Get current axes or create one"""
        if not self.axes:
            return self.add_subplot(111)
        return self.axes[-1]

    def get_axes(self) -> List[Axes]:
        """Return list of axes"""
        return self.axes


def subplots(nrows: int = 1, ncols: int = 1, figsize: Tuple[float, float] = None,
             **kwargs) -> Tuple[Figure, Union[Axes, List[Axes]]]:
    """
    Create a figure and a set of subplots.

    Returns:
        fig : Figure
        ax : Axes or array of Axes
    """
    fig = Figure(figsize=figsize, **kwargs)

    if nrows == 1 and ncols == 1:
        ax = fig.add_subplot(1, 1, 1)
        return fig, ax

    axes = []
    for i in range(nrows):
        row_axes = []
        for j in range(ncols):
            ax = fig.add_subplot(nrows, ncols, i * ncols + j + 1)
            row_axes.append(ax)
        if ncols == 1:
            axes.append(row_axes[0])
        else:
            axes.append(row_axes)

    if nrows == 1:
        axes = axes[0] if ncols > 1 else axes

    return fig, axes
