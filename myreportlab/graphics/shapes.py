"""
Vector graphics shapes.
"""

from ..lib.colors import black, white, toColor


class Shape:
    """Base class for all shapes."""

    def __init__(self):
        self.strokeColor = black
        self.fillColor = None
        self.strokeWidth = 1

    def copy(self):
        """Create a copy of the shape."""
        import copy
        return copy.deepcopy(self)


class Group(Shape):
    """Container for multiple shapes."""

    def __init__(self, *elements, **kwargs):
        super().__init__()
        self.contents = list(elements)
        self.transform = kwargs.get("transform", (1, 0, 0, 1, 0, 0))

    def add(self, shape):
        """Add a shape to the group."""
        self.contents.append(shape)

    def insert(self, index, shape):
        """Insert a shape at index."""
        self.contents.insert(index, shape)


class Drawing(Group):
    """
    Top-level container for vector graphics.
    """

    def __init__(self, width=400, height=200, *elements, **kwargs):
        super().__init__(*elements, **kwargs)
        self.width = width
        self.height = height
        self.background = kwargs.get("background", None)

    def drawOn(self, canvas, x, y):
        """Draw on a canvas."""
        canvas.saveState()
        canvas.translate(x, y)

        # Draw background
        if self.background:
            canvas.setFillColor(self.background)
            canvas.rect(0, 0, self.width, self.height, stroke=0, fill=1)

        # Draw contents
        for shape in self.contents:
            self._draw_shape(canvas, shape)

        canvas.restoreState()

    def _draw_shape(self, canvas, shape):
        """Draw a single shape."""
        if isinstance(shape, Group):
            canvas.saveState()
            if hasattr(shape, "transform"):
                canvas.transform(*shape.transform)
            for child in shape.contents:
                self._draw_shape(canvas, child)
            canvas.restoreState()
        elif isinstance(shape, Line):
            if shape.strokeColor:
                canvas.setStrokeColor(shape.strokeColor)
                canvas.setLineWidth(shape.strokeWidth)
                canvas.line(shape.x1, shape.y1, shape.x2, shape.y2)
        elif isinstance(shape, Rect):
            self._set_colors(canvas, shape)
            canvas.rect(shape.x, shape.y, shape.width, shape.height,
                       stroke=1 if shape.strokeColor else 0,
                       fill=1 if shape.fillColor else 0)
        elif isinstance(shape, Circle):
            self._set_colors(canvas, shape)
            canvas.circle(shape.cx, shape.cy, shape.r,
                         stroke=1 if shape.strokeColor else 0,
                         fill=1 if shape.fillColor else 0)
        elif isinstance(shape, Ellipse):
            self._set_colors(canvas, shape)
            canvas.ellipse(shape.cx - shape.rx, shape.cy - shape.ry,
                          shape.cx + shape.rx, shape.cy + shape.ry,
                          stroke=1 if shape.strokeColor else 0,
                          fill=1 if shape.fillColor else 0)
        elif isinstance(shape, Polygon):
            self._draw_polygon(canvas, shape)
        elif isinstance(shape, PolyLine):
            self._draw_polyline(canvas, shape)
        elif isinstance(shape, String):
            if shape.fillColor:
                canvas.setFillColor(shape.fillColor)
            canvas.setFont(shape.fontName, shape.fontSize)
            canvas.drawString(shape.x, shape.y, shape.text)
        elif isinstance(shape, Path):
            self._draw_path(canvas, shape)

    def _set_colors(self, canvas, shape):
        """Set stroke and fill colors."""
        if shape.strokeColor:
            canvas.setStrokeColor(shape.strokeColor)
        if shape.fillColor:
            canvas.setFillColor(shape.fillColor)
        canvas.setLineWidth(shape.strokeWidth)

    def _draw_polygon(self, canvas, shape):
        """Draw a polygon."""
        if not shape.points:
            return
        path = canvas.beginPath()
        points = shape.points
        path.moveTo(points[0], points[1])
        for i in range(2, len(points), 2):
            path.lineTo(points[i], points[i + 1])
        path.close()
        self._set_colors(canvas, shape)
        canvas.drawPath(path,
                       stroke=1 if shape.strokeColor else 0,
                       fill=1 if shape.fillColor else 0)

    def _draw_polyline(self, canvas, shape):
        """Draw a polyline."""
        if not shape.points or len(shape.points) < 4:
            return
        if shape.strokeColor:
            canvas.setStrokeColor(shape.strokeColor)
            canvas.setLineWidth(shape.strokeWidth)
        points = shape.points
        for i in range(0, len(points) - 2, 2):
            canvas.line(points[i], points[i + 1], points[i + 2], points[i + 3])

    def _draw_path(self, canvas, shape):
        """Draw a path."""
        path = canvas.beginPath()
        for op in shape.operators:
            cmd = op[0]
            args = op[1:]
            if cmd == "moveTo":
                path.moveTo(*args)
            elif cmd == "lineTo":
                path.lineTo(*args)
            elif cmd == "curveTo":
                path.curveTo(*args)
            elif cmd == "closePath":
                path.close()
        self._set_colors(canvas, shape)
        canvas.drawPath(path,
                       stroke=1 if shape.strokeColor else 0,
                       fill=1 if shape.fillColor else 0)

    def save(self, filename=None, fmt="pdf"):
        """Save the drawing to a file."""
        from ..pdfgen import Canvas
        filename = filename or "drawing.pdf"
        c = Canvas(filename, pagesize=(self.width, self.height))
        self.drawOn(c, 0, 0)
        c.showPage()
        c.save()


class Line(Shape):
    """A straight line."""

    def __init__(self, x1, y1, x2, y2, **kwargs):
        super().__init__()
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.strokeColor = kwargs.get("strokeColor", black)
        self.strokeWidth = kwargs.get("strokeWidth", 1)


class Rect(Shape):
    """A rectangle."""

    def __init__(self, x, y, width, height, rx=0, ry=0, **kwargs):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rx = rx
        self.ry = ry
        self.strokeColor = kwargs.get("strokeColor", black)
        self.fillColor = kwargs.get("fillColor", None)
        self.strokeWidth = kwargs.get("strokeWidth", 1)


class Circle(Shape):
    """A circle."""

    def __init__(self, cx, cy, r, **kwargs):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.r = r
        self.strokeColor = kwargs.get("strokeColor", black)
        self.fillColor = kwargs.get("fillColor", None)
        self.strokeWidth = kwargs.get("strokeWidth", 1)


class Ellipse(Shape):
    """An ellipse."""

    def __init__(self, cx, cy, rx, ry, **kwargs):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.strokeColor = kwargs.get("strokeColor", black)
        self.fillColor = kwargs.get("fillColor", None)
        self.strokeWidth = kwargs.get("strokeWidth", 1)


class Polygon(Shape):
    """A closed polygon."""

    def __init__(self, points=None, **kwargs):
        super().__init__()
        self.points = points or []
        self.strokeColor = kwargs.get("strokeColor", black)
        self.fillColor = kwargs.get("fillColor", None)
        self.strokeWidth = kwargs.get("strokeWidth", 1)


class PolyLine(Shape):
    """An open polyline."""

    def __init__(self, points=None, **kwargs):
        super().__init__()
        self.points = points or []
        self.strokeColor = kwargs.get("strokeColor", black)
        self.strokeWidth = kwargs.get("strokeWidth", 1)


class String(Shape):
    """A text string."""

    def __init__(self, x, y, text, **kwargs):
        super().__init__()
        self.x = x
        self.y = y
        self.text = text
        self.fontName = kwargs.get("fontName", "Helvetica")
        self.fontSize = kwargs.get("fontSize", 10)
        self.fillColor = kwargs.get("fillColor", black)
        self.textAnchor = kwargs.get("textAnchor", "start")


class Path(Shape):
    """A path made of operators."""

    def __init__(self, **kwargs):
        super().__init__()
        self.operators = []
        self.strokeColor = kwargs.get("strokeColor", black)
        self.fillColor = kwargs.get("fillColor", None)
        self.strokeWidth = kwargs.get("strokeWidth", 1)

    def moveTo(self, x, y):
        """Move to point."""
        self.operators.append(("moveTo", x, y))

    def lineTo(self, x, y):
        """Line to point."""
        self.operators.append(("lineTo", x, y))

    def curveTo(self, x1, y1, x2, y2, x3, y3):
        """Bezier curve."""
        self.operators.append(("curveTo", x1, y1, x2, y2, x3, y3))

    def closePath(self):
        """Close the path."""
        self.operators.append(("closePath",))


class Wedge(Shape):
    """A pie wedge."""

    def __init__(self, cx, cy, r, startangledegrees, endangledegrees, **kwargs):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.r = r
        self.startangledegrees = startangledegrees
        self.endangledegrees = endangledegrees
        self.strokeColor = kwargs.get("strokeColor", black)
        self.fillColor = kwargs.get("fillColor", None)
        self.strokeWidth = kwargs.get("strokeWidth", 1)
