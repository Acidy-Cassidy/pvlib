"""
mymatplotlib backend

Renders figures to various formats (SVG, text summary).
"""

import os
from typing import Optional
from .colors import to_hex, LINE_STYLES


def save_figure(fig, fname: str, dpi: int = 100, format: str = None):
    """Save figure to file"""
    if format is None:
        _, ext = os.path.splitext(fname)
        format = ext[1:].lower() if ext else 'svg'

    if format == 'svg':
        svg_content = render_svg(fig, dpi)
        with open(fname, 'w') as f:
            f.write(svg_content)
    elif format in ('png', 'jpg', 'jpeg', 'pdf'):
        # For non-SVG formats, save as SVG with note
        svg_content = render_svg(fig, dpi)
        svg_fname = fname.rsplit('.', 1)[0] + '.svg'
        with open(svg_fname, 'w') as f:
            f.write(svg_content)
        print(f"Note: Saved as SVG ({svg_fname}). Install full matplotlib for {format} support.")
    else:
        # Default to text summary
        with open(fname, 'w') as f:
            f.write(render_text(fig))


def render_svg(fig, dpi: int = 100) -> str:
    """Render figure to SVG string"""
    width_px = int(fig.figsize[0] * dpi)
    height_px = int(fig.figsize[1] * dpi)

    lines = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" height="{height_px}" viewBox="0 0 {width_px} {height_px}">',
        f'  <rect width="100%" height="100%" fill="{fig.facecolor}"/>',
    ]

    # Render each axes
    for ax in fig.axes:
        lines.extend(_render_axes_svg(ax, fig, dpi))

    # Suptitle
    if fig._suptitle:
        x = width_px / 2
        y = 20
        lines.append(f'  <text x="{x}" y="{y}" text-anchor="middle" font-size="14" font-weight="bold">{_escape_xml(fig._suptitle)}</text>')

    lines.append('</svg>')

    return '\n'.join(lines)


def _escape_xml(s: str) -> str:
    """Escape XML special characters"""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _render_axes_svg(ax, fig, dpi: int) -> list:
    """Render a single axes to SVG elements"""
    lines = []

    width_px = int(fig.figsize[0] * dpi)
    height_px = int(fig.figsize[1] * dpi)

    # Calculate axes position in pixels
    left, bottom, w, h = ax.rect
    ax_left = int(left * width_px)
    ax_bottom = int((1 - bottom - h) * height_px)  # SVG y is inverted
    ax_width = int(w * width_px)
    ax_height = int(h * height_px)

    # Get data limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    def data_to_svg(x, y):
        """Convert data coordinates to SVG coordinates"""
        sx = ax_left + (x - xlim[0]) / (xlim[1] - xlim[0]) * ax_width
        sy = ax_bottom + ax_height - (y - ylim[0]) / (ylim[1] - ylim[0]) * ax_height
        return sx, sy

    # Create clip path
    clip_id = f"clip_{id(ax)}"
    lines.append(f'  <defs>')
    lines.append(f'    <clipPath id="{clip_id}">')
    lines.append(f'      <rect x="{ax_left}" y="{ax_bottom}" width="{ax_width}" height="{ax_height}"/>')
    lines.append(f'    </clipPath>')
    lines.append(f'  </defs>')

    # Axes background
    lines.append(f'  <rect x="{ax_left}" y="{ax_bottom}" width="{ax_width}" height="{ax_height}" fill="white" stroke="black" stroke-width="1"/>')

    # Grid
    if ax._grid_on:
        grid_color = ax._grid_kwargs.get('color', '#cccccc')
        lines.append(f'  <g stroke="{grid_color}" stroke-width="0.5" stroke-dasharray="2,2">')

        # X grid lines
        xticks = ax._xticks or _auto_ticks(xlim[0], xlim[1])
        for tick in xticks:
            sx, _ = data_to_svg(tick, 0)
            if ax_left <= sx <= ax_left + ax_width:
                lines.append(f'    <line x1="{sx}" y1="{ax_bottom}" x2="{sx}" y2="{ax_bottom + ax_height}"/>')

        # Y grid lines
        yticks = ax._yticks or _auto_ticks(ylim[0], ylim[1])
        for tick in yticks:
            _, sy = data_to_svg(0, tick)
            if ax_bottom <= sy <= ax_bottom + ax_height:
                lines.append(f'    <line x1="{ax_left}" y1="{sy}" x2="{ax_left + ax_width}" y2="{sy}"/>')

        lines.append('  </g>')

    # Render patches (bars, etc.)
    lines.append(f'  <g clip-path="url(#{clip_id})">')
    for patch in ax.patches:
        if hasattr(patch, 'xy'):  # Rectangle
            x, y = patch.xy
            sx, sy = data_to_svg(x, y + patch.height)
            sw = patch.width / (xlim[1] - xlim[0]) * ax_width
            sh = patch.height / (ylim[1] - ylim[0]) * ax_height

            fill = to_hex(patch.facecolor)
            stroke = to_hex(patch.edgecolor) if patch.edgecolor != 'none' else 'none'
            alpha = patch.alpha

            lines.append(f'    <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="{fill}" stroke="{stroke}" opacity="{alpha}"/>')
    lines.append('  </g>')

    # Render lines
    lines.append(f'  <g clip-path="url(#{clip_id})">')
    for line in ax.lines:
        if not line.visible or not line.xdata:
            continue

        color = to_hex(line.color)
        stroke_width = line.linewidth
        linestyle = line.linestyle

        # Dash pattern
        dash = ''
        if linestyle in ('--', 'dashed'):
            dash = 'stroke-dasharray="5,5"'
        elif linestyle in (':', 'dotted'):
            dash = 'stroke-dasharray="2,2"'
        elif linestyle in ('-.', 'dashdot'):
            dash = 'stroke-dasharray="5,2,2,2"'

        # Draw line
        if linestyle and linestyle not in ('', ' ', 'none'):
            points = []
            for x, y in zip(line.xdata, line.ydata):
                sx, sy = data_to_svg(x, y)
                points.append(f'{sx},{sy}')

            if points:
                lines.append(f'    <polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="{stroke_width}" {dash}/>')

        # Draw markers
        if line.marker and line.marker not in ('', ' ', 'none'):
            marker_size = line.markersize
            mfc = to_hex(line.markerfacecolor)
            mec = to_hex(line.markeredgecolor)

            for x, y in zip(line.xdata, line.ydata):
                sx, sy = data_to_svg(x, y)

                if line.marker == 'o':
                    lines.append(f'    <circle cx="{sx}" cy="{sy}" r="{marker_size/2}" fill="{mfc}" stroke="{mec}"/>')
                elif line.marker == 's':
                    half = marker_size / 2
                    lines.append(f'    <rect x="{sx-half}" y="{sy-half}" width="{marker_size}" height="{marker_size}" fill="{mfc}" stroke="{mec}"/>')
                elif line.marker == '^':
                    half = marker_size / 2
                    points = f'{sx},{sy-half} {sx-half},{sy+half} {sx+half},{sy+half}'
                    lines.append(f'    <polygon points="{points}" fill="{mfc}" stroke="{mec}"/>')
                elif line.marker in ('+', 'x'):
                    half = marker_size / 2
                    if line.marker == '+':
                        lines.append(f'    <line x1="{sx}" y1="{sy-half}" x2="{sx}" y2="{sy+half}" stroke="{mec}" stroke-width="1.5"/>')
                        lines.append(f'    <line x1="{sx-half}" y1="{sy}" x2="{sx+half}" y2="{sy}" stroke="{mec}" stroke-width="1.5"/>')
                    else:
                        lines.append(f'    <line x1="{sx-half}" y1="{sy-half}" x2="{sx+half}" y2="{sy+half}" stroke="{mec}" stroke-width="1.5"/>')
                        lines.append(f'    <line x1="{sx-half}" y1="{sy+half}" x2="{sx+half}" y2="{sy-half}" stroke="{mec}" stroke-width="1.5"/>')
                else:
                    # Default to small circle
                    lines.append(f'    <circle cx="{sx}" cy="{sy}" r="{marker_size/3}" fill="{mfc}" stroke="{mec}"/>')

    lines.append('  </g>')

    # Axis labels and title
    if ax._xlabel:
        x = ax_left + ax_width / 2
        y = ax_bottom + ax_height + 35
        lines.append(f'  <text x="{x}" y="{y}" text-anchor="middle" font-size="12">{_escape_xml(ax._xlabel)}</text>')

    if ax._ylabel:
        x = ax_left - 40
        y = ax_bottom + ax_height / 2
        lines.append(f'  <text x="{x}" y="{y}" text-anchor="middle" font-size="12" transform="rotate(-90 {x} {y})">{_escape_xml(ax._ylabel)}</text>')

    if ax._title:
        x = ax_left + ax_width / 2
        y = ax_bottom - 10
        lines.append(f'  <text x="{x}" y="{y}" text-anchor="middle" font-size="12" font-weight="bold">{_escape_xml(ax._title)}</text>')

    # Tick labels
    xticks = ax._xticks or _auto_ticks(xlim[0], xlim[1])
    for i, tick in enumerate(xticks):
        sx, _ = data_to_svg(tick, 0)
        if ax_left <= sx <= ax_left + ax_width:
            label = ax._xticklabels[i] if ax._xticklabels and i < len(ax._xticklabels) else f'{tick:.4g}'
            lines.append(f'  <text x="{sx}" y="{ax_bottom + ax_height + 15}" text-anchor="middle" font-size="10">{label}</text>')

    yticks = ax._yticks or _auto_ticks(ylim[0], ylim[1])
    for i, tick in enumerate(yticks):
        _, sy = data_to_svg(0, tick)
        if ax_bottom <= sy <= ax_bottom + ax_height:
            label = ax._yticklabels[i] if ax._yticklabels and i < len(ax._yticklabels) else f'{tick:.4g}'
            lines.append(f'  <text x="{ax_left - 5}" y="{sy + 3}" text-anchor="end" font-size="10">{label}</text>')

    # Legend
    if ax._legend:
        legend_x = ax_left + ax_width - 100
        legend_y = ax_bottom + 10
        lines.append(f'  <rect x="{legend_x}" y="{legend_y}" width="90" height="{len(ax._legend.labels) * 20 + 10}" fill="white" stroke="black" stroke-width="0.5"/>')

        for i, (handle, label) in enumerate(zip(ax._legend.handles, ax._legend.labels)):
            y = legend_y + 15 + i * 20
            color = to_hex(handle.color) if hasattr(handle, 'color') else '#1f77b4'
            lines.append(f'  <line x1="{legend_x + 5}" y1="{y}" x2="{legend_x + 25}" y2="{y}" stroke="{color}" stroke-width="2"/>')
            lines.append(f'  <text x="{legend_x + 30}" y="{y + 4}" font-size="10">{_escape_xml(label)}</text>')

    return lines


def _auto_ticks(vmin: float, vmax: float, n: int = 5) -> list:
    """Generate automatic tick locations"""
    if vmin == vmax:
        return [vmin]

    range_val = vmax - vmin
    # Find nice step size
    raw_step = range_val / n

    # Round to nice number
    magnitude = 10 ** int(f'{raw_step:.0e}'.split('e')[1])
    residual = raw_step / magnitude

    if residual < 1.5:
        nice_step = magnitude
    elif residual < 3:
        nice_step = 2 * magnitude
    elif residual < 7:
        nice_step = 5 * magnitude
    else:
        nice_step = 10 * magnitude

    # Generate ticks
    start = (vmin // nice_step) * nice_step
    ticks = []
    tick = start
    while tick <= vmax + nice_step * 0.01:
        if tick >= vmin - nice_step * 0.01:
            ticks.append(tick)
        tick += nice_step

    return ticks


def render_text(fig) -> str:
    """Render figure as text summary"""
    lines = [
        f"Figure: {fig.figsize[0]}x{fig.figsize[1]} inches, {fig.dpi} dpi",
        f"Number of axes: {len(fig.axes)}",
        ""
    ]

    if fig._suptitle:
        lines.append(f"Title: {fig._suptitle}")
        lines.append("")

    for i, ax in enumerate(fig.axes):
        lines.append(f"Axes {i + 1}:")
        lines.append(f"  Title: {ax._title or '(none)'}")
        lines.append(f"  X label: {ax._xlabel or '(none)'}")
        lines.append(f"  Y label: {ax._ylabel or '(none)'}")
        lines.append(f"  X limits: {ax.get_xlim()}")
        lines.append(f"  Y limits: {ax.get_ylim()}")
        lines.append(f"  Lines: {len(ax.lines)}")
        lines.append(f"  Patches: {len(ax.patches)}")

        for j, line in enumerate(ax.lines):
            lines.append(f"    Line {j + 1}: {len(line.xdata)} points, color={line.color}")

        lines.append("")

    return '\n'.join(lines)


def show_figure(fig):
    """Display figure information (no actual GUI)"""
    print(render_text(fig))
    print("(Use savefig() to save as SVG)")
