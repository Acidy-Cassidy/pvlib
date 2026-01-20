"""
Flowable elements for document layout.
"""

from ..lib.colors import black, white, toColor
from ..lib.styles import ParagraphStyle, getSampleStyleSheet


class Flowable:
    """Base class for all flowable elements."""

    width = 0
    height = 0
    _fixedWidth = 0
    _fixedHeight = 0

    def __init__(self):
        self.width = 0
        self.height = 0
        self._frame = None
        self.canv = None

    def wrap(self, availWidth, availHeight):
        """
        Calculate dimensions needed to render.

        Args:
            availWidth: Available width
            availHeight: Available height

        Returns:
            (width, height) tuple
        """
        return (self.width, self.height)

    def draw(self):
        """Draw the flowable on the canvas."""
        pass

    def drawOn(self, canvas, x, y, _sW=0):
        """
        Draw on canvas at position.

        Args:
            canvas: Canvas to draw on
            x, y: Position
            _sW: Extra width for alignment
        """
        self.canv = canvas
        canvas.saveState()
        canvas.translate(x, y)
        self.draw()
        canvas.restoreState()

    def split(self, availWidth, availHeight):
        """
        Split flowable if it doesn't fit.

        Returns:
            List of flowables or empty list if can't split
        """
        return []

    def getSpaceBefore(self):
        """Get space before this flowable."""
        return getattr(self, "spaceBefore", 0)

    def getSpaceAfter(self):
        """Get space after this flowable."""
        return getattr(self, "spaceAfter", 0)


class Spacer(Flowable):
    """Fixed amount of vertical space."""

    def __init__(self, width, height):
        """
        Create a spacer.

        Args:
            width: Width (usually 0 or 1)
            height: Height to reserve
        """
        super().__init__()
        self.width = width
        self.height = height
        self._fixedWidth = 1
        self._fixedHeight = 1

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        pass  # Nothing to draw


class Paragraph(Flowable):
    """
    Formatted text paragraph.
    """

    def __init__(self, text, style=None, bulletText=None, caseSensitive=1):
        """
        Create a paragraph.

        Args:
            text: Text content (may include simple HTML tags)
            style: ParagraphStyle object
            bulletText: Bullet character/text
            caseSensitive: Case sensitivity for tags
        """
        super().__init__()
        self.text = text
        self.style = style or getSampleStyleSheet()["Normal"]
        self.bulletText = bulletText

        # Parse text
        self._plainText = self._strip_tags(text)

    def _strip_tags(self, text):
        """Strip HTML-like tags from text."""
        import re
        return re.sub(r"<[^>]+>", "", text)

    def wrap(self, availWidth, availHeight):
        """Calculate wrapped dimensions."""
        style = self.style
        fontSize = style.fontSize
        leading = style.leading
        leftIndent = style.leftIndent
        rightIndent = style.rightIndent
        firstLineIndent = style.firstLineIndent

        # Available text width
        textWidth = availWidth - leftIndent - rightIndent

        # Estimate character width
        charWidth = fontSize * 0.5

        # Count lines needed
        text = self._plainText
        if textWidth > 0 and charWidth > 0:
            charsPerLine = max(1, int(textWidth / charWidth))
            lines = []
            current_line = ""
            for word in text.split():
                if len(current_line) + len(word) + 1 <= charsPerLine:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            self._lines = lines
            numLines = max(1, len(lines))
        else:
            self._lines = [text]
            numLines = 1

        self.width = availWidth
        self.height = numLines * leading + style.spaceBefore + style.spaceAfter

        return (self.width, self.height)

    def draw(self):
        """Draw the paragraph."""
        if not self.canv:
            return

        style = self.style
        x = style.leftIndent
        y = self.height - style.spaceBefore - style.leading

        self.canv.setFont(style.fontName, style.fontSize)

        if style.textColor:
            self.canv.setFillColor(style.textColor)

        for i, line in enumerate(self._lines):
            # Handle alignment
            lineWidth = len(line) * style.fontSize * 0.5
            textWidth = self.width - style.leftIndent - style.rightIndent

            if style.alignment == 1:  # Center
                x = (self.width - lineWidth) / 2
            elif style.alignment == 2:  # Right
                x = self.width - style.rightIndent - lineWidth
            else:  # Left (default)
                x = style.leftIndent
                if i == 0:
                    x += style.firstLineIndent

            self.canv.drawString(x, y, line)
            y -= style.leading

    def split(self, availWidth, availHeight):
        """Split paragraph if too tall."""
        self.wrap(availWidth, availHeight)

        if self.height <= availHeight:
            return [self]

        # Calculate how many lines fit
        style = self.style
        usableHeight = availHeight - style.spaceBefore
        linesPerPage = max(1, int(usableHeight / style.leading))

        if linesPerPage >= len(self._lines):
            return [self]

        # Split into two paragraphs
        firstLines = self._lines[:linesPerPage]
        restLines = self._lines[linesPerPage:]

        first = Paragraph(" ".join(firstLines), style)
        rest = Paragraph(" ".join(restLines), style)

        return [first, rest]


class Image(Flowable):
    """
    Image flowable.
    """

    def __init__(self, filename, width=None, height=None, kind="direct",
                 mask=None, lazy=1, hAlign="CENTER"):
        """
        Create an image flowable.

        Args:
            filename: Path to image file
            width: Desired width (None = natural)
            height: Desired height (None = natural)
            kind: Sizing mode
            mask: Transparency mask
            lazy: Lazy loading
            hAlign: Horizontal alignment
        """
        super().__init__()
        self.filename = filename
        self._width = width
        self._height = height
        self.hAlign = hAlign
        self.mask = mask

        # Default size
        self.imageWidth = width or 100
        self.imageHeight = height or 100

    def wrap(self, availWidth, availHeight):
        """Calculate dimensions."""
        self.width = self._width or self.imageWidth
        self.height = self._height or self.imageHeight

        # Scale to fit if needed
        if self.width > availWidth:
            scale = availWidth / self.width
            self.width = availWidth
            self.height *= scale

        return (self.width, self.height)

    def draw(self):
        """Draw the image."""
        if not self.canv:
            return

        self.canv.drawImage(
            self.filename,
            0, 0,
            width=self.width,
            height=self.height,
            mask=self.mask
        )


class PageBreak(Flowable):
    """Force a page break."""

    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return (self.width, 0)

    def draw(self):
        pass


class CondPageBreak(Flowable):
    """Conditional page break if not enough space."""

    def __init__(self, height):
        """
        Args:
            height: Minimum required space
        """
        super().__init__()
        self._height = height
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        if availHeight < self._height:
            # Force a page break
            self.height = availHeight + 1
        else:
            self.height = 0
        return (availWidth, self.height)


class KeepTogether(Flowable):
    """Keep flowables together on same page."""

    def __init__(self, flowables):
        super().__init__()
        self._flowables = flowables

    def wrap(self, availWidth, availHeight):
        totalHeight = 0
        maxWidth = 0
        for f in self._flowables:
            w, h = f.wrap(availWidth, availHeight - totalHeight)
            totalHeight += h
            maxWidth = max(maxWidth, w)
        self.width = maxWidth
        self.height = totalHeight
        return (self.width, self.height)

    def draw(self):
        y = self.height
        for f in self._flowables:
            f.canv = self.canv
            y -= f.height
            f.drawOn(self.canv, 0, y)

    def split(self, availWidth, availHeight):
        if self.height <= availHeight:
            return [self]
        # Can't split - return empty to force page break
        return []


class HRFlowable(Flowable):
    """Horizontal rule."""

    def __init__(self, width="100%", thickness=1, color=black,
                 spaceBefore=1, spaceAfter=1, hAlign="CENTER",
                 vAlign="BOTTOM", dash=None):
        super().__init__()
        self._width = width
        self.thickness = thickness
        self.color = color
        self.spaceBefore = spaceBefore
        self.spaceAfter = spaceAfter
        self.hAlign = hAlign

    def wrap(self, availWidth, availHeight):
        if isinstance(self._width, str) and self._width.endswith("%"):
            pct = float(self._width[:-1]) / 100.0
            self.width = availWidth * pct
        else:
            self.width = self._width or availWidth

        self.height = self.thickness + self.spaceBefore + self.spaceAfter
        return (self.width, self.height)

    def draw(self):
        if not self.canv:
            return

        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        y = self.spaceAfter + self.thickness / 2
        self.canv.line(0, y, self.width, y)


class ListFlowable(Flowable):
    """List of items with bullets or numbers."""

    def __init__(self, flowables, start=None, bulletType="bullet",
                 bulletFontName="Helvetica", bulletFontSize=12,
                 bulletOffsetY=0, bulletDedent=18, bulletFormat=None):
        super().__init__()
        self._flowables = flowables
        self.start = start or 1
        self.bulletType = bulletType
        self.bulletFontName = bulletFontName
        self.bulletFontSize = bulletFontSize
        self.bulletDedent = bulletDedent

    def wrap(self, availWidth, availHeight):
        totalHeight = 0
        for i, f in enumerate(self._flowables):
            w, h = f.wrap(availWidth - self.bulletDedent, availHeight - totalHeight)
            totalHeight += h
        self.width = availWidth
        self.height = totalHeight
        return (self.width, self.height)

    def draw(self):
        if not self.canv:
            return

        y = self.height
        for i, f in enumerate(self._flowables):
            y -= f.height

            # Draw bullet
            if self.bulletType == "bullet":
                bullet = "\u2022"
            else:
                bullet = f"{self.start + i}."

            self.canv.setFont(self.bulletFontName, self.bulletFontSize)
            self.canv.drawString(0, y + f.height * 0.3, bullet)

            # Draw content
            f.canv = self.canv
            f.drawOn(self.canv, self.bulletDedent, y)


class ListItem(Flowable):
    """Single list item."""

    def __init__(self, flowables, bulletColor=black, value=None):
        super().__init__()
        if isinstance(flowables, list):
            self._flowables = flowables
        else:
            self._flowables = [flowables]
        self.bulletColor = bulletColor
        self.value = value

    def wrap(self, availWidth, availHeight):
        totalHeight = 0
        for f in self._flowables:
            w, h = f.wrap(availWidth, availHeight - totalHeight)
            totalHeight += h
        self.width = availWidth
        self.height = totalHeight
        return (self.width, self.height)

    def draw(self):
        y = self.height
        for f in self._flowables:
            y -= f.height
            f.canv = self.canv
            f.drawOn(self.canv, 0, y)
