"""
Paragraph and document styles for reportlab.
"""

from .colors import black, white


class PropertySet:
    """Base class for property collections."""

    defaults = {}

    def __init__(self, name, parent=None, **kwargs):
        """
        Initialize property set.

        Args:
            name: Style name
            parent: Parent style to inherit from
            **kwargs: Style properties
        """
        self.name = name
        self.parent = parent

        # Set defaults
        for key, value in self.defaults.items():
            setattr(self, key, value)

        # Inherit from parent
        if parent:
            for key in self.defaults:
                if hasattr(parent, key):
                    setattr(self, key, getattr(parent, key))

        # Apply overrides
        for key, value in kwargs.items():
            if key in self.defaults or hasattr(self, key):
                setattr(self, key, value)

    def clone(self, name, parent=None, **kwargs):
        """Create a clone of this style with modifications."""
        # Get current values
        current = {}
        for key in self.defaults:
            current[key] = getattr(self, key)

        # Apply overrides
        current.update(kwargs)

        return self.__class__(name, parent or self.parent, **current)


class ParagraphStyle(PropertySet):
    """
    Style definition for Paragraph flowables.
    """

    defaults = {
        "fontName": "Helvetica",
        "fontSize": 10,
        "leading": 12,
        "leftIndent": 0,
        "rightIndent": 0,
        "firstLineIndent": 0,
        "alignment": 0,  # 0=left, 1=center, 2=right, 4=justify
        "spaceBefore": 0,
        "spaceAfter": 0,
        "bulletFontName": "Helvetica",
        "bulletFontSize": 10,
        "bulletIndent": 0,
        "textColor": black,
        "backColor": None,
        "wordWrap": None,
        "borderWidth": 0,
        "borderPadding": 0,
        "borderColor": None,
        "borderRadius": None,
        "allowWidows": 1,
        "allowOrphans": 0,
        "textTransform": None,
        "endDots": None,
        "splitLongWords": 1,
        "underlineWidth": None,
        "bulletAnchor": "start",
        "justifyLastLine": 0,
        "justifyBreaks": 0,
        "spaceShrinkage": 0.05,
        "strikeWidth": None,
        "underlineOffset": None,
        "underlineGap": None,
        "strikeOffset": None,
        "strikeGap": None,
        "linkUnderline": 0,
        "underlineColor": None,
        "strikeColor": None,
    }

    def __init__(self, name, parent=None, **kwargs):
        super().__init__(name, parent, **kwargs)

        # Ensure leading is at least fontSize
        if self.leading < self.fontSize:
            self.leading = self.fontSize * 1.2


class ListStyle(PropertySet):
    """Style definition for list flowables."""

    defaults = {
        "leftIndent": 18,
        "rightIndent": 0,
        "bulletAlign": "left",
        "bulletType": "1",
        "bulletColor": black,
        "bulletFontName": "Helvetica",
        "bulletFontSize": 12,
        "bulletOffsetY": 0,
        "bulletDedent": "auto",
        "bulletDir": "ltr",
        "bulletFormat": None,
        "start": None,
    }


class StyleSheet1:
    """
    Collection of named styles.
    """

    def __init__(self):
        self.byName = {}
        self.byAlias = {}

    def __getitem__(self, key):
        try:
            return self.byName[key]
        except KeyError:
            return self.byAlias[key]

    def __contains__(self, key):
        return key in self.byName or key in self.byAlias

    def has_key(self, key):
        return key in self

    def add(self, style, alias=None):
        """
        Add a style to the stylesheet.

        Args:
            style: Style object
            alias: Optional alias name
        """
        self.byName[style.name] = style
        if alias:
            self.byAlias[alias] = style

    def list(self):
        """Return list of style names."""
        return list(self.byName.keys())


def getSampleStyleSheet():
    """
    Get a sample stylesheet with common styles.

    Returns:
        StyleSheet1 with default styles
    """
    stylesheet = StyleSheet1()

    # Normal style
    normal = ParagraphStyle(
        "Normal",
        fontName="Helvetica",
        fontSize=10,
        leading=12,
    )
    stylesheet.add(normal)

    # Body text
    body = ParagraphStyle(
        "BodyText",
        parent=normal,
        spaceBefore=6,
    )
    stylesheet.add(body)

    # Italic
    italic = ParagraphStyle(
        "Italic",
        parent=normal,
        fontName="Helvetica-Oblique",
    )
    stylesheet.add(italic)

    # Headings
    h1 = ParagraphStyle(
        "Heading1",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        spaceBefore=12,
        spaceAfter=6,
    )
    stylesheet.add(h1, alias="h1")

    h2 = ParagraphStyle(
        "Heading2",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
    )
    stylesheet.add(h2, alias="h2")

    h3 = ParagraphStyle(
        "Heading3",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        spaceBefore=12,
        spaceAfter=6,
    )
    stylesheet.add(h3, alias="h3")

    h4 = ParagraphStyle(
        "Heading4",
        parent=normal,
        fontName="Helvetica-BoldOblique",
        fontSize=10,
        leading=12,
        spaceBefore=10,
        spaceAfter=4,
    )
    stylesheet.add(h4, alias="h4")

    h5 = ParagraphStyle(
        "Heading5",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        spaceBefore=8,
        spaceAfter=4,
    )
    stylesheet.add(h5, alias="h5")

    h6 = ParagraphStyle(
        "Heading6",
        parent=normal,
        fontName="Helvetica-BoldOblique",
        fontSize=8,
        leading=10,
        spaceBefore=8,
        spaceAfter=4,
    )
    stylesheet.add(h6, alias="h6")

    # Title
    title = ParagraphStyle(
        "Title",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        alignment=1,  # Center
        spaceAfter=12,
    )
    stylesheet.add(title)

    # Bullet
    bullet = ParagraphStyle(
        "Bullet",
        parent=normal,
        firstLineIndent=0,
        leftIndent=18,
        bulletIndent=0,
        spaceBefore=0,
    )
    stylesheet.add(bullet)

    # Definition
    definition = ParagraphStyle(
        "Definition",
        parent=normal,
        leftIndent=36,
        bulletIndent=0,
    )
    stylesheet.add(definition)

    # Code
    code = ParagraphStyle(
        "Code",
        parent=normal,
        fontName="Courier",
        fontSize=9,
        leading=11,
        leftIndent=0,
        firstLineIndent=0,
    )
    stylesheet.add(code)

    return stylesheet


# Text alignment constants
TA_LEFT = 0
TA_CENTER = 1
TA_RIGHT = 2
TA_JUSTIFY = 4
