"""
myreportlab - Educational reportlab implementation
Mirrors ReportLab API for learning purposes.

Supports basic PDF generation via Canvas and PLATYPUS.
"""

__version__ = "0.1.0"

# Re-export key classes for convenience
from .pdfgen import Canvas
from .platypus import (
    SimpleDocTemplate,
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)
from .lib import (
    # Units
    inch, cm, mm, pica,
    # Colors
    Color, HexColor,
    black, white, red, green, blue, yellow, cyan, magenta,
    # Page sizes
    A4, LETTER, LEGAL, TABLOID,
    landscape, portrait,
    # Styles
    ParagraphStyle, getSampleStyleSheet,
    TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY,
)

__all__ = [
    # Version
    "__version__",
    # Canvas
    "Canvas",
    # PLATYPUS
    "SimpleDocTemplate",
    "BaseDocTemplate",
    "PageTemplate",
    "Frame",
    "Paragraph",
    "Spacer",
    "Image",
    "Table",
    "TableStyle",
    "PageBreak",
    # Units
    "inch",
    "cm",
    "mm",
    "pica",
    # Colors
    "Color",
    "HexColor",
    "black",
    "white",
    "red",
    "green",
    "blue",
    "yellow",
    "cyan",
    "magenta",
    # Page sizes
    "A4",
    "LETTER",
    "LEGAL",
    "TABLOID",
    "landscape",
    "portrait",
    # Styles
    "ParagraphStyle",
    "getSampleStyleSheet",
    "TA_LEFT",
    "TA_CENTER",
    "TA_RIGHT",
    "TA_JUSTIFY",
]
