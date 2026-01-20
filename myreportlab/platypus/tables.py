"""
Table flowable for document layout.
"""

from .flowables import Flowable
from ..lib.colors import black, white, toColor


class TableStyle:
    """
    Style commands for table formatting.

    Commands are tuples of (command, start, end, ...values)
    where start/end are (col, row) coordinates.
    -1 means "last".

    Example:
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
    """

    def __init__(self, cmds=None, parent=None):
        """
        Create table style.

        Args:
            cmds: List of style commands
            parent: Parent style to inherit from
        """
        self._cmds = []
        if parent:
            self._cmds.extend(parent._cmds)
        if cmds:
            self._cmds.extend(cmds)

    def add(self, *cmds):
        """Add style commands."""
        self._cmds.extend(cmds)

    def getCommands(self):
        """Get all commands."""
        return self._cmds


class Table(Flowable):
    """
    Table flowable with rows and columns.
    """

    def __init__(self, data, colWidths=None, rowHeights=None, style=None,
                 repeatRows=0, repeatCols=0, splitByRow=1, emptyTableAction=None,
                 ident=None, hAlign="CENTER", vAlign="MIDDLE",
                 normalizedData=0, cellStyles=None, rowSplitRange=None,
                 spaceBefore=None, spaceAfter=None, cornerRadii=None):
        """
        Create a table.

        Args:
            data: 2D list of cell values
            colWidths: List of column widths (None = auto)
            rowHeights: List of row heights (None = auto)
            style: TableStyle object
            repeatRows: Rows to repeat on each page
            repeatCols: Columns to repeat
            splitByRow: Allow splitting between rows
            hAlign: Horizontal alignment
            vAlign: Vertical alignment
        """
        super().__init__()
        self._data = data
        self._colWidths = colWidths
        self._rowHeights = rowHeights
        self._style = style
        self._repeatRows = repeatRows
        self._repeatCols = repeatCols
        self._splitByRow = splitByRow
        self._hAlign = hAlign
        self._vAlign = vAlign
        self.spaceBefore = spaceBefore or 0
        self.spaceAfter = spaceAfter or 0

        # Calculate dimensions
        self._nrows = len(data) if data else 0
        self._ncols = max(len(row) for row in data) if data else 0

        # Style cache
        self._cellStyles = {}

    def _calc_widths(self, availWidth):
        """Calculate column widths."""
        if self._colWidths:
            # Use provided widths
            widths = list(self._colWidths)
            # Handle None values
            total_fixed = sum(w for w in widths if w is not None)
            none_count = widths.count(None)
            if none_count > 0:
                remaining = availWidth - total_fixed
                auto_width = remaining / none_count
                widths = [w if w is not None else auto_width for w in widths]
        else:
            # Auto-calculate based on content
            widths = [availWidth / self._ncols] * self._ncols

        return widths

    def _calc_heights(self, availHeight):
        """Calculate row heights."""
        if self._rowHeights:
            heights = list(self._rowHeights)
            # Handle None values
            heights = [h if h is not None else 20 for h in heights]
        else:
            # Default height
            heights = [20] * self._nrows

        return heights

    def wrap(self, availWidth, availHeight):
        """Calculate table dimensions."""
        self._widths = self._calc_widths(availWidth)
        self._heights = self._calc_heights(availHeight)

        self.width = sum(self._widths)
        self.height = sum(self._heights)

        return (self.width, self.height)

    def _resolve_coord(self, coord, nrows, ncols):
        """Resolve negative coordinates."""
        col, row = coord
        if col < 0:
            col = ncols + col + 1
        if row < 0:
            row = nrows + row + 1
        return (col, row)

    def _get_cell_style(self, row, col):
        """Get accumulated style for a cell."""
        if (row, col) in self._cellStyles:
            return self._cellStyles[(row, col)]

        style = {
            "background": None,
            "textcolor": black,
            "fontname": "Helvetica",
            "fontsize": 10,
            "align": "LEFT",
            "valign": "MIDDLE",
            "leftpadding": 3,
            "rightpadding": 3,
            "toppadding": 1,
            "bottompadding": 1,
            "grid": None,
            "box": None,
            "lineabove": None,
            "linebelow": None,
            "linebefore": None,
            "lineafter": None,
        }

        if self._style:
            for cmd in self._style.getCommands():
                name = cmd[0].upper()
                start = self._resolve_coord(cmd[1], self._nrows, self._ncols)
                end = self._resolve_coord(cmd[2], self._nrows, self._ncols)
                values = cmd[3:]

                # Check if cell is in range
                if (start[0] <= col <= end[0] and start[1] <= row <= end[1]):
                    if name == "BACKGROUND":
                        style["background"] = toColor(values[0])
                    elif name == "TEXTCOLOR":
                        style["textcolor"] = toColor(values[0])
                    elif name == "FONTNAME" or name == "FONT":
                        style["fontname"] = values[0]
                    elif name == "FONTSIZE":
                        style["fontsize"] = values[0]
                    elif name == "ALIGN":
                        style["align"] = values[0]
                    elif name == "VALIGN":
                        style["valign"] = values[0]
                    elif name == "LEFTPADDING":
                        style["leftpadding"] = values[0]
                    elif name == "RIGHTPADDING":
                        style["rightpadding"] = values[0]
                    elif name == "TOPPADDING":
                        style["toppadding"] = values[0]
                    elif name == "BOTTOMPADDING":
                        style["bottompadding"] = values[0]
                    elif name == "GRID":
                        style["grid"] = (values[0], toColor(values[1]) if len(values) > 1 else black)
                    elif name == "BOX":
                        style["box"] = (values[0], toColor(values[1]) if len(values) > 1 else black)
                    elif name == "INNERGRID":
                        style["innergrid"] = (values[0], toColor(values[1]) if len(values) > 1 else black)
                    elif name == "LINEABOVE":
                        style["lineabove"] = (values[0], toColor(values[1]) if len(values) > 1 else black)
                    elif name == "LINEBELOW":
                        style["linebelow"] = (values[0], toColor(values[1]) if len(values) > 1 else black)
                    elif name == "LINEBEFORE":
                        style["linebefore"] = (values[0], toColor(values[1]) if len(values) > 1 else black)
                    elif name == "LINEAFTER":
                        style["lineafter"] = (values[0], toColor(values[1]) if len(values) > 1 else black)

        self._cellStyles[(row, col)] = style
        return style

    def draw(self):
        """Draw the table."""
        if not self.canv or not self._data:
            return

        # Draw cells
        y = self.height
        for row_idx, row_data in enumerate(self._data):
            row_height = self._heights[row_idx]
            y -= row_height
            x = 0

            for col_idx, cell_value in enumerate(row_data):
                if col_idx >= len(self._widths):
                    break

                col_width = self._widths[col_idx]
                style = self._get_cell_style(row_idx, col_idx)

                # Draw background
                if style["background"]:
                    self.canv.setFillColor(style["background"])
                    self.canv.rect(x, y, col_width, row_height, stroke=0, fill=1)

                # Draw cell content
                self.canv.setFillColor(style["textcolor"])
                self.canv.setFont(style["fontname"], style["fontsize"])

                text = str(cell_value) if cell_value is not None else ""
                text_x = x + style["leftpadding"]
                text_y = y + row_height / 2 - style["fontsize"] / 3

                # Horizontal alignment
                text_width = len(text) * style["fontsize"] * 0.5
                available_width = col_width - style["leftpadding"] - style["rightpadding"]

                if style["align"] == "CENTER":
                    text_x = x + (col_width - text_width) / 2
                elif style["align"] == "RIGHT":
                    text_x = x + col_width - style["rightpadding"] - text_width

                self.canv.drawString(text_x, text_y, text)

                # Draw cell borders
                self._draw_cell_borders(x, y, col_width, row_height, row_idx, col_idx)

                x += col_width

    def _draw_cell_borders(self, x, y, width, height, row, col):
        """Draw cell borders based on style."""
        style = self._get_cell_style(row, col)

        # Grid lines
        if style.get("grid"):
            line_width, color = style["grid"]
            self.canv.setStrokeColor(color)
            self.canv.setLineWidth(line_width)
            self.canv.rect(x, y, width, height, stroke=1, fill=0)

        # Individual lines
        for line_type, side in [("lineabove", "top"), ("linebelow", "bottom"),
                                ("linebefore", "left"), ("lineafter", "right")]:
            if style.get(line_type):
                line_width, color = style[line_type]
                self.canv.setStrokeColor(color)
                self.canv.setLineWidth(line_width)
                if side == "top":
                    self.canv.line(x, y + height, x + width, y + height)
                elif side == "bottom":
                    self.canv.line(x, y, x + width, y)
                elif side == "left":
                    self.canv.line(x, y, x, y + height)
                elif side == "right":
                    self.canv.line(x + width, y, x + width, y + height)

    def setStyle(self, style):
        """Set or add table style."""
        if self._style is None:
            self._style = style
        else:
            self._style.add(*style.getCommands())
        self._cellStyles = {}  # Clear cache

    def split(self, availWidth, availHeight):
        """Split table across pages."""
        self.wrap(availWidth, availHeight)

        if self.height <= availHeight:
            return [self]

        if not self._splitByRow:
            return []

        # Find split point
        cumHeight = 0
        splitRow = 0
        for i, h in enumerate(self._heights):
            if cumHeight + h > availHeight:
                splitRow = i
                break
            cumHeight += h

        if splitRow <= self._repeatRows:
            return []  # Can't split

        # Create two tables
        firstData = self._data[:splitRow]
        restData = self._data[splitRow:]

        if self._repeatRows:
            restData = self._data[:self._repeatRows] + restData

        first = Table(firstData, self._colWidths, self._rowHeights[:splitRow],
                     style=self._style)
        rest = Table(restData, self._colWidths,
                    style=self._style, repeatRows=self._repeatRows)

        return [first, rest]
