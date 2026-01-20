"""
Canvas class for direct PDF drawing.
"""

import io
import zlib
from datetime import datetime

from ..lib.pagesizes import A4, LETTER
from ..lib.colors import Color, black, white, toColor


class Canvas:
    """
    Canvas for drawing PDF content directly.

    Usage:
        c = Canvas("output.pdf", pagesize=A4)
        c.drawString(100, 700, "Hello World")
        c.showPage()
        c.save()
    """

    def __init__(self, filename, pagesize=LETTER, bottomup=1, pageCompression=0,
                 encoding="utf-8", verbosity=0, encrypt=None):
        """
        Initialize canvas.

        Args:
            filename: Output file path or file-like object
            pagesize: (width, height) tuple in points
            bottomup: If 1, origin at bottom-left (PDF default)
            pageCompression: Compress page streams
            encoding: Text encoding
            verbosity: Debug output level
            encrypt: Encryption settings
        """
        self._filename = filename
        self._pagesize = pagesize
        self._bottomup = bottomup
        self._pageCompression = pageCompression
        self._encoding = encoding

        # State
        self._pages = []
        self._current_page = []
        self._objects = []
        self._fonts_used = set()

        # Graphics state
        self._font_name = "Helvetica"
        self._font_size = 12
        self._fill_color = black
        self._stroke_color = black
        self._line_width = 1

        # State stack
        self._state_stack = []

        # Start first page
        self._start_page()

    def _start_page(self):
        """Start a new page."""
        self._current_page = []

    @property
    def _width(self):
        return self._pagesize[0]

    @property
    def _height(self):
        return self._pagesize[1]

    # Graphics state

    def saveState(self):
        """Save current graphics state."""
        self._state_stack.append({
            "font_name": self._font_name,
            "font_size": self._font_size,
            "fill_color": self._fill_color,
            "stroke_color": self._stroke_color,
            "line_width": self._line_width,
        })
        self._current_page.append("q")

    def restoreState(self):
        """Restore saved graphics state."""
        if self._state_stack:
            state = self._state_stack.pop()
            self._font_name = state["font_name"]
            self._font_size = state["font_size"]
            self._fill_color = state["fill_color"]
            self._stroke_color = state["stroke_color"]
            self._line_width = state["line_width"]
        self._current_page.append("Q")

    # Fonts

    def setFont(self, fontName, fontSize, leading=None):
        """
        Set the current font.

        Args:
            fontName: Font name (Helvetica, Times-Roman, Courier, etc.)
            fontSize: Font size in points
            leading: Line height (unused, for compatibility)
        """
        self._font_name = fontName
        self._font_size = fontSize
        self._fonts_used.add(fontName)
        self._current_page.append(f"/{self._get_font_ref(fontName)} {fontSize} Tf")

    def _get_font_ref(self, fontName):
        """Get font reference name."""
        font_map = {
            "Helvetica": "F1",
            "Helvetica-Bold": "F2",
            "Helvetica-Oblique": "F3",
            "Helvetica-BoldOblique": "F4",
            "Times-Roman": "F5",
            "Times-Bold": "F6",
            "Times-Italic": "F7",
            "Times-BoldItalic": "F8",
            "Courier": "F9",
            "Courier-Bold": "F10",
            "Courier-Oblique": "F11",
            "Courier-BoldOblique": "F12",
            "Symbol": "F13",
            "ZapfDingbats": "F14",
        }
        return font_map.get(fontName, "F1")

    # Colors

    def setFillColor(self, color, alpha=None):
        """Set fill color."""
        color = toColor(color, black)
        self._fill_color = color
        if alpha is not None:
            color = color.clone(alpha=alpha)
        self._current_page.append(f"{color.red:.3f} {color.green:.3f} {color.blue:.3f} rg")

    def setStrokeColor(self, color, alpha=None):
        """Set stroke color."""
        color = toColor(color, black)
        self._stroke_color = color
        if alpha is not None:
            color = color.clone(alpha=alpha)
        self._current_page.append(f"{color.red:.3f} {color.green:.3f} {color.blue:.3f} RG")

    def setFillColorRGB(self, r, g, b, alpha=None):
        """Set fill color from RGB values (0-1)."""
        self.setFillColor(Color(r, g, b, alpha or 1))

    def setStrokeColorRGB(self, r, g, b, alpha=None):
        """Set stroke color from RGB values (0-1)."""
        self.setStrokeColor(Color(r, g, b, alpha or 1))

    def setFillColorCMYK(self, c, m, y, k, alpha=None):
        """Set fill color from CMYK values."""
        from ..lib.colors import CMYKColor
        self.setFillColor(CMYKColor(c, m, y, k, alpha or 1))

    def setStrokeColorCMYK(self, c, m, y, k, alpha=None):
        """Set stroke color from CMYK values."""
        from ..lib.colors import CMYKColor
        self.setStrokeColor(CMYKColor(c, m, y, k, alpha or 1))

    def setFillGray(self, gray, alpha=None):
        """Set fill to grayscale."""
        self.setFillColor(Color(gray, gray, gray, alpha or 1))

    def setStrokeGray(self, gray, alpha=None):
        """Set stroke to grayscale."""
        self.setStrokeColor(Color(gray, gray, gray, alpha or 1))

    # Line properties

    def setLineWidth(self, width):
        """Set line width."""
        self._line_width = width
        self._current_page.append(f"{width} w")

    def setLineCap(self, cap):
        """Set line cap style (0=butt, 1=round, 2=square)."""
        self._current_page.append(f"{cap} J")

    def setLineJoin(self, join):
        """Set line join style (0=miter, 1=round, 2=bevel)."""
        self._current_page.append(f"{join} j")

    def setMiterLimit(self, limit):
        """Set miter limit."""
        self._current_page.append(f"{limit} M")

    def setDash(self, array=[], phase=0):
        """Set dash pattern."""
        if not array:
            self._current_page.append("[] 0 d")
        else:
            arr_str = " ".join(str(x) for x in array)
            self._current_page.append(f"[{arr_str}] {phase} d")

    # Text drawing

    def drawString(self, x, y, text):
        """
        Draw a string at the given position.

        Args:
            x: X coordinate
            y: Y coordinate
            text: Text to draw
        """
        text = self._escape_text(text)
        self._current_page.append("BT")
        self._current_page.append(f"/{self._get_font_ref(self._font_name)} {self._font_size} Tf")
        self._current_page.append(f"{x:.2f} {y:.2f} Td")
        self._current_page.append(f"({text}) Tj")
        self._current_page.append("ET")

    def drawRightString(self, x, y, text):
        """Draw string aligned to the right of x."""
        width = self.stringWidth(text, self._font_name, self._font_size)
        self.drawString(x - width, y, text)

    def drawCentredString(self, x, y, text):
        """Draw string centered at x."""
        width = self.stringWidth(text, self._font_name, self._font_size)
        self.drawString(x - width / 2, y, text)

    drawCenteredString = drawCentredString  # Alias

    def drawText(self, textobject):
        """Draw a text object."""
        if hasattr(textobject, "getCode"):
            self._current_page.append(textobject.getCode())

    def beginText(self, x=0, y=0):
        """Create a text object."""
        return PDFTextObject(self, x, y)

    def stringWidth(self, text, fontName=None, fontSize=None):
        """
        Get the width of a string.

        Args:
            text: String to measure
            fontName: Font name (default: current)
            fontSize: Font size (default: current)

        Returns:
            Width in points
        """
        fontName = fontName or self._font_name
        fontSize = fontSize or self._font_size
        # Approximate width (real implementation uses font metrics)
        avg_char_width = fontSize * 0.5
        return len(text) * avg_char_width

    def _escape_text(self, text):
        """Escape special characters in text."""
        text = str(text)
        text = text.replace("\\", "\\\\")
        text = text.replace("(", "\\(")
        text = text.replace(")", "\\)")
        return text

    # Shape drawing

    def line(self, x1, y1, x2, y2):
        """Draw a line."""
        self._current_page.append(f"{x1:.2f} {y1:.2f} m")
        self._current_page.append(f"{x2:.2f} {y2:.2f} l")
        self._current_page.append("S")

    def lines(self, linelist):
        """Draw multiple lines."""
        for line in linelist:
            if len(line) == 4:
                self.line(*line)

    def rect(self, x, y, width, height, stroke=1, fill=0):
        """
        Draw a rectangle.

        Args:
            x, y: Bottom-left corner
            width, height: Dimensions
            stroke: Draw outline
            fill: Fill interior
        """
        self._current_page.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re")
        self._apply_stroke_fill(stroke, fill)

    def roundRect(self, x, y, width, height, radius, stroke=1, fill=0):
        """Draw a rounded rectangle."""
        # Approximate with bezier curves
        r = min(radius, width / 2, height / 2)
        k = 0.5523  # Bezier approximation constant

        self._current_page.append(f"{x + r:.2f} {y:.2f} m")
        self._current_page.append(f"{x + width - r:.2f} {y:.2f} l")
        self._current_page.append(f"{x + width - r + r * k:.2f} {y:.2f} {x + width:.2f} {y + r - r * k:.2f} {x + width:.2f} {y + r:.2f} c")
        self._current_page.append(f"{x + width:.2f} {y + height - r:.2f} l")
        self._current_page.append(f"{x + width:.2f} {y + height - r + r * k:.2f} {x + width - r + r * k:.2f} {y + height:.2f} {x + width - r:.2f} {y + height:.2f} c")
        self._current_page.append(f"{x + r:.2f} {y + height:.2f} l")
        self._current_page.append(f"{x + r - r * k:.2f} {y + height:.2f} {x:.2f} {y + height - r + r * k:.2f} {x:.2f} {y + height - r:.2f} c")
        self._current_page.append(f"{x:.2f} {y + r:.2f} l")
        self._current_page.append(f"{x:.2f} {y + r - r * k:.2f} {x + r - r * k:.2f} {y:.2f} {x + r:.2f} {y:.2f} c")
        self._current_page.append("h")
        self._apply_stroke_fill(stroke, fill)

    def circle(self, x, y, r, stroke=1, fill=0):
        """Draw a circle."""
        self.ellipse(x - r, y - r, x + r, y + r, stroke, fill)

    def ellipse(self, x1, y1, x2, y2, stroke=1, fill=0):
        """Draw an ellipse."""
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        rx = abs(x2 - x1) / 2
        ry = abs(y2 - y1) / 2
        k = 0.5523

        self._current_page.append(f"{cx + rx:.2f} {cy:.2f} m")
        self._current_page.append(f"{cx + rx:.2f} {cy + ry * k:.2f} {cx + rx * k:.2f} {cy + ry:.2f} {cx:.2f} {cy + ry:.2f} c")
        self._current_page.append(f"{cx - rx * k:.2f} {cy + ry:.2f} {cx - rx:.2f} {cy + ry * k:.2f} {cx - rx:.2f} {cy:.2f} c")
        self._current_page.append(f"{cx - rx:.2f} {cy - ry * k:.2f} {cx - rx * k:.2f} {cy - ry:.2f} {cx:.2f} {cy - ry:.2f} c")
        self._current_page.append(f"{cx + rx * k:.2f} {cy - ry:.2f} {cx + rx:.2f} {cy - ry * k:.2f} {cx + rx:.2f} {cy:.2f} c")
        self._current_page.append("h")
        self._apply_stroke_fill(stroke, fill)

    def wedge(self, x1, y1, x2, y2, startAng, extent, stroke=1, fill=0):
        """Draw a pie wedge."""
        # Simplified - just draw an arc path
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        rx = abs(x2 - x1) / 2
        ry = abs(y2 - y1) / 2

        import math
        start_rad = math.radians(startAng)
        end_rad = math.radians(startAng + extent)

        # Start from center
        self._current_page.append(f"{cx:.2f} {cy:.2f} m")
        # Line to start of arc
        sx = cx + rx * math.cos(start_rad)
        sy = cy + ry * math.sin(start_rad)
        self._current_page.append(f"{sx:.2f} {sy:.2f} l")
        # Arc (simplified as straight line to end)
        ex = cx + rx * math.cos(end_rad)
        ey = cy + ry * math.sin(end_rad)
        self._current_page.append(f"{ex:.2f} {ey:.2f} l")
        # Close
        self._current_page.append("h")
        self._apply_stroke_fill(stroke, fill)

    def _apply_stroke_fill(self, stroke, fill):
        """Apply stroke and fill operators."""
        if stroke and fill:
            self._current_page.append("B")
        elif fill:
            self._current_page.append("f")
        elif stroke:
            self._current_page.append("S")
        else:
            self._current_page.append("n")

    # Paths

    def beginPath(self):
        """Begin a new path."""
        return PDFPathObject()

    def drawPath(self, path, stroke=1, fill=0):
        """Draw a path object."""
        if hasattr(path, "getCode"):
            self._current_page.append(path.getCode())
            self._apply_stroke_fill(stroke, fill)

    def clipPath(self, path, stroke=0, fill=0):
        """Set clipping path."""
        if hasattr(path, "getCode"):
            self._current_page.append(path.getCode())
            self._current_page.append("W n")

    # Transformations

    def translate(self, dx, dy):
        """Translate coordinate system."""
        self._current_page.append(f"1 0 0 1 {dx:.2f} {dy:.2f} cm")

    def scale(self, sx, sy=None):
        """Scale coordinate system."""
        if sy is None:
            sy = sx
        self._current_page.append(f"{sx:.2f} 0 0 {sy:.2f} 0 0 cm")

    def rotate(self, theta):
        """Rotate coordinate system (degrees)."""
        import math
        rad = math.radians(theta)
        cos_t = math.cos(rad)
        sin_t = math.sin(rad)
        self._current_page.append(f"{cos_t:.4f} {sin_t:.4f} {-sin_t:.4f} {cos_t:.4f} 0 0 cm")

    def skew(self, alpha, beta):
        """Skew coordinate system."""
        import math
        tan_a = math.tan(math.radians(alpha))
        tan_b = math.tan(math.radians(beta))
        self._current_page.append(f"1 {tan_a:.4f} {tan_b:.4f} 1 0 0 cm")

    def transform(self, a, b, c, d, e, f):
        """Apply arbitrary transformation matrix."""
        self._current_page.append(f"{a:.4f} {b:.4f} {c:.4f} {d:.4f} {e:.2f} {f:.2f} cm")

    # Images

    def drawImage(self, image, x, y, width=None, height=None, mask=None,
                  preserveAspectRatio=False, anchor='c'):
        """
        Draw an image.

        Args:
            image: Image path or PIL Image
            x, y: Position
            width, height: Size (None = natural size)
            mask: Transparency mask
            preserveAspectRatio: Maintain aspect ratio
            anchor: Anchor point

        Note: This is a simplified stub.
        """
        # For actual implementation, would need to embed image in PDF
        # Just draw a placeholder rectangle
        w = width or 100
        h = height or 100
        self.saveState()
        self.setStrokeColor(black)
        self.setFillGray(0.9)
        self.rect(x, y, w, h, stroke=1, fill=1)
        self.restoreState()

    def drawInlineImage(self, image, x, y, width=None, height=None):
        """Draw an inline image."""
        self.drawImage(image, x, y, width, height)

    # Page management

    def showPage(self):
        """Finish current page and start a new one."""
        # Store current page content
        self._pages.append(self._current_page)
        self._start_page()

    def setPageSize(self, size):
        """Set page size for subsequent pages."""
        self._pagesize = size

    def getPageNumber(self):
        """Get current page number."""
        return len(self._pages) + 1

    # Output

    def save(self):
        """Save the PDF to the output file."""
        # Finalize current page if not empty
        if self._current_page:
            self._pages.append(self._current_page)

        # Generate PDF
        pdf_data = self._generate_pdf()

        # Write to file
        if isinstance(self._filename, str):
            with open(self._filename, "wb") as f:
                f.write(pdf_data)
        else:
            self._filename.write(pdf_data)

    def _generate_pdf(self):
        """Generate PDF bytes."""
        output = io.BytesIO()

        # Header
        output.write(b"%PDF-1.4\n")
        output.write(b"%\xe2\xe3\xcf\xd3\n")

        objects = []
        obj_positions = []

        # Font resources
        fonts = self._generate_fonts()
        font_refs = {}
        for i, (name, font_obj) in enumerate(fonts.items()):
            obj_positions.append(output.tell())
            obj_num = len(obj_positions)
            font_refs[name] = obj_num
            output.write(f"{obj_num} 0 obj\n".encode())
            output.write(font_obj.encode())
            output.write(b"\nendobj\n\n")

        # Pages
        page_refs = []
        for page_content in self._pages:
            # Content stream
            content = "\n".join(page_content)
            content_bytes = content.encode("latin-1", errors="replace")

            obj_positions.append(output.tell())
            content_obj_num = len(obj_positions)
            output.write(f"{content_obj_num} 0 obj\n".encode())
            output.write(f"<< /Length {len(content_bytes)} >>\n".encode())
            output.write(b"stream\n")
            output.write(content_bytes)
            output.write(b"\nendstream\nendobj\n\n")

            # Page object
            obj_positions.append(output.tell())
            page_obj_num = len(obj_positions)
            page_refs.append(page_obj_num)

            # Build font resource dict
            font_res = " ".join(f"/{self._get_font_ref(f)} {font_refs.get(f, 1)} 0 R"
                               for f in self._fonts_used)

            output.write(f"{page_obj_num} 0 obj\n".encode())
            output.write(f"<< /Type /Page /Parent {len(obj_positions) + 2} 0 R ".encode())
            output.write(f"/MediaBox [0 0 {self._pagesize[0]} {self._pagesize[1]}] ".encode())
            output.write(f"/Contents {content_obj_num} 0 R ".encode())
            output.write(f"/Resources << /Font << {font_res} >> >> ".encode())
            output.write(b">>\nendobj\n\n")

        # Pages tree
        obj_positions.append(output.tell())
        pages_obj_num = len(obj_positions)
        kids = " ".join(f"{ref} 0 R" for ref in page_refs)
        output.write(f"{pages_obj_num} 0 obj\n".encode())
        output.write(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>\n".encode())
        output.write(b"endobj\n\n")

        # Catalog
        obj_positions.append(output.tell())
        catalog_obj_num = len(obj_positions)
        output.write(f"{catalog_obj_num} 0 obj\n".encode())
        output.write(f"<< /Type /Catalog /Pages {pages_obj_num} 0 R >>\n".encode())
        output.write(b"endobj\n\n")

        # Cross-reference table
        xref_pos = output.tell()
        output.write(b"xref\n")
        output.write(f"0 {len(obj_positions) + 1}\n".encode())
        output.write(b"0000000000 65535 f \n")
        for pos in obj_positions:
            output.write(f"{pos:010d} 00000 n \n".encode())

        # Trailer
        output.write(b"trailer\n")
        output.write(f"<< /Size {len(obj_positions) + 1} /Root {catalog_obj_num} 0 R >>\n".encode())
        output.write(f"startxref\n{xref_pos}\n".encode())
        output.write(b"%%EOF\n")

        return output.getvalue()

    def _generate_fonts(self):
        """Generate font objects."""
        fonts = {}
        font_map = {
            "Helvetica": ("Helvetica", "Type1"),
            "Helvetica-Bold": ("Helvetica-Bold", "Type1"),
            "Helvetica-Oblique": ("Helvetica-Oblique", "Type1"),
            "Helvetica-BoldOblique": ("Helvetica-BoldOblique", "Type1"),
            "Times-Roman": ("Times-Roman", "Type1"),
            "Times-Bold": ("Times-Bold", "Type1"),
            "Times-Italic": ("Times-Italic", "Type1"),
            "Times-BoldItalic": ("Times-BoldItalic", "Type1"),
            "Courier": ("Courier", "Type1"),
            "Courier-Bold": ("Courier-Bold", "Type1"),
            "Courier-Oblique": ("Courier-Oblique", "Type1"),
            "Courier-BoldOblique": ("Courier-BoldOblique", "Type1"),
            "Symbol": ("Symbol", "Type1"),
            "ZapfDingbats": ("ZapfDingbats", "Type1"),
        }

        for font_name in self._fonts_used:
            base_name, font_type = font_map.get(font_name, ("Helvetica", "Type1"))
            fonts[font_name] = f"<< /Type /Font /Subtype /{font_type} /BaseFont /{base_name} >>"

        # Always include Helvetica
        if "Helvetica" not in fonts:
            fonts["Helvetica"] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

        return fonts


class PDFTextObject:
    """Text object for complex text layout."""

    def __init__(self, canvas, x=0, y=0):
        self._canvas = canvas
        self._code = ["BT", f"{x:.2f} {y:.2f} Td"]
        self._x = x
        self._y = y

    def setTextOrigin(self, x, y):
        """Set text origin."""
        self._code.append(f"{x:.2f} {y:.2f} Td")
        self._x = x
        self._y = y

    def setFont(self, fontName, fontSize, leading=None):
        """Set font."""
        self._canvas._fonts_used.add(fontName)
        ref = self._canvas._get_font_ref(fontName)
        self._code.append(f"/{ref} {fontSize} Tf")

    def setFillColor(self, color):
        """Set fill color."""
        color = toColor(color, black)
        self._code.append(f"{color.red:.3f} {color.green:.3f} {color.blue:.3f} rg")

    def textLine(self, text=""):
        """Output a line of text and move to next line."""
        text = self._canvas._escape_text(text)
        self._code.append(f"({text}) Tj")
        self._code.append("T*")

    def textLines(self, stuff, trim=1):
        """Output multiple lines."""
        if isinstance(stuff, str):
            lines = stuff.split("\n")
        else:
            lines = stuff
        for line in lines:
            self.textLine(line)

    def setLeading(self, leading):
        """Set line spacing."""
        self._code.append(f"{leading} TL")

    def setCharSpace(self, charSpace):
        """Set character spacing."""
        self._code.append(f"{charSpace} Tc")

    def setWordSpace(self, wordSpace):
        """Set word spacing."""
        self._code.append(f"{wordSpace} Tw")

    def setRise(self, rise):
        """Set text rise (superscript/subscript)."""
        self._code.append(f"{rise} Ts")

    def getCode(self):
        """Get PDF code."""
        return "\n".join(self._code + ["ET"])


class PDFPathObject:
    """Path object for complex shapes."""

    def __init__(self):
        self._code = []

    def moveTo(self, x, y):
        """Move to point."""
        self._code.append(f"{x:.2f} {y:.2f} m")

    def lineTo(self, x, y):
        """Line to point."""
        self._code.append(f"{x:.2f} {y:.2f} l")

    def curveTo(self, x1, y1, x2, y2, x3, y3):
        """Bezier curve."""
        self._code.append(f"{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f} {x3:.2f} {y3:.2f} c")

    def arc(self, x1, y1, x2, y2, startAng=0, extent=90):
        """Arc."""
        # Simplified - would need bezier approximation
        pass

    def arcTo(self, x1, y1, x2, y2, startAng=0, extent=90):
        """Arc to."""
        pass

    def rect(self, x, y, width, height):
        """Rectangle."""
        self._code.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re")

    def ellipse(self, x, y, width, height):
        """Ellipse."""
        cx = x + width / 2
        cy = y + height / 2
        rx = width / 2
        ry = height / 2
        k = 0.5523

        self._code.append(f"{cx + rx:.2f} {cy:.2f} m")
        self._code.append(f"{cx + rx:.2f} {cy + ry * k:.2f} {cx + rx * k:.2f} {cy + ry:.2f} {cx:.2f} {cy + ry:.2f} c")
        self._code.append(f"{cx - rx * k:.2f} {cy + ry:.2f} {cx - rx:.2f} {cy + ry * k:.2f} {cx - rx:.2f} {cy:.2f} c")
        self._code.append(f"{cx - rx:.2f} {cy - ry * k:.2f} {cx - rx * k:.2f} {cy - ry:.2f} {cx:.2f} {cy - ry:.2f} c")
        self._code.append(f"{cx + rx * k:.2f} {cy - ry:.2f} {cx + rx:.2f} {cy - ry * k:.2f} {cx + rx:.2f} {cy:.2f} c")

    def circle(self, x, y, r):
        """Circle."""
        self.ellipse(x - r, y - r, 2 * r, 2 * r)

    def close(self):
        """Close path."""
        self._code.append("h")

    def getCode(self):
        """Get PDF code."""
        return "\n".join(self._code)
