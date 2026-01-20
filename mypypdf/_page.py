"""
PageObject class for PDF pages.
"""

import re
from .generic import (
    DictionaryObject, ArrayObject, NameObject, NumberObject,
    RectangleObject, StreamObject, IndirectObject
)


class PageObject(DictionaryObject):
    """
    Represents a single page in a PDF document.
    """

    def __init__(self, pdf=None, indirect_ref=None):
        super().__init__()
        self.pdf = pdf
        self.indirect_ref = indirect_ref
        self[NameObject("Type")] = NameObject("Page")

    @property
    def mediabox(self):
        """
        Get the page's MediaBox (page dimensions).

        Returns:
            RectangleObject with page bounds
        """
        box = self.get("/MediaBox")
        if box is None and self.pdf:
            # Check parent for inherited MediaBox
            parent = self.get("/Parent")
            if isinstance(parent, IndirectObject):
                parent = parent.get_object()
            if parent:
                box = parent.get("/MediaBox")
        if box is None:
            # Default to US Letter
            return RectangleObject([0, 0, 612, 792])
        if isinstance(box, IndirectObject):
            box = box.get_object()
        return RectangleObject(box)

    @mediabox.setter
    def mediabox(self, value):
        if not isinstance(value, RectangleObject):
            value = RectangleObject(value)
        self[NameObject("MediaBox")] = value

    @property
    def cropbox(self):
        """Get the page's CropBox."""
        box = self.get("/CropBox")
        if box is None:
            return self.mediabox
        if isinstance(box, IndirectObject):
            box = box.get_object()
        return RectangleObject(box)

    @property
    def trimbox(self):
        """Get the page's TrimBox."""
        box = self.get("/TrimBox")
        if box is None:
            return self.cropbox
        if isinstance(box, IndirectObject):
            box = box.get_object()
        return RectangleObject(box)

    @property
    def bleedbox(self):
        """Get the page's BleedBox."""
        box = self.get("/BleedBox")
        if box is None:
            return self.cropbox
        if isinstance(box, IndirectObject):
            box = box.get_object()
        return RectangleObject(box)

    @property
    def artbox(self):
        """Get the page's ArtBox."""
        box = self.get("/ArtBox")
        if box is None:
            return self.cropbox
        if isinstance(box, IndirectObject):
            box = box.get_object()
        return RectangleObject(box)

    def rotate(self, angle):
        """
        Rotate the page by the given angle.

        Args:
            angle: Rotation angle in degrees (90, 180, 270)

        Returns:
            Self for chaining
        """
        current = int(self.get("/Rotate", NumberObject(0)).value if isinstance(
            self.get("/Rotate", NumberObject(0)), NumberObject) else 0)
        new_angle = (current + angle) % 360
        self[NameObject("Rotate")] = NumberObject(new_angle)
        return self

    def scale(self, sx, sy):
        """
        Scale the page by given factors.

        Args:
            sx: Horizontal scale factor
            sy: Vertical scale factor

        Returns:
            Self for chaining
        """
        # Modify the mediabox
        box = self.mediabox
        new_width = box.width * sx
        new_height = box.height * sy
        self.mediabox = RectangleObject([0, 0, new_width, new_height])

        # Add transformation to content stream
        # This is a simplified implementation
        return self

    def scale_by(self, factor):
        """
        Scale the page uniformly.

        Args:
            factor: Scale factor

        Returns:
            Self for chaining
        """
        return self.scale(factor, factor)

    def scale_to(self, width, height):
        """
        Scale the page to exact dimensions.

        Args:
            width: Target width
            height: Target height

        Returns:
            Self for chaining
        """
        box = self.mediabox
        sx = width / box.width if box.width else 1
        sy = height / box.height if box.height else 1
        return self.scale(sx, sy)

    def merge_page(self, other, over=True):
        """
        Merge another page onto this one.

        Args:
            other: Another PageObject
            over: If True, other page content goes over this page

        Returns:
            Self for chaining
        """
        # Get content streams
        my_content = self._get_content_stream()
        other_content = other._get_content_stream()

        if other_content:
            if over:
                # Other content over this content
                new_content = my_content + b"\n" + other_content
            else:
                # Other content under this content
                new_content = other_content + b"\n" + my_content

            # Create new content stream
            content_stream = StreamObject(new_content)
            self[NameObject("Contents")] = content_stream

        # Merge resources
        my_resources = self.get("/Resources", DictionaryObject())
        other_resources = other.get("/Resources", DictionaryObject())

        if isinstance(my_resources, IndirectObject):
            my_resources = my_resources.get_object() or DictionaryObject()
        if isinstance(other_resources, IndirectObject):
            other_resources = other_resources.get_object() or DictionaryObject()

        # Simple merge of resources
        for key, value in other_resources.items():
            if key not in my_resources:
                my_resources[key] = value

        self[NameObject("Resources")] = my_resources
        return self

    def _get_content_stream(self):
        """Get the decoded content stream data."""
        contents = self.get("/Contents")
        if contents is None:
            return b""

        if isinstance(contents, IndirectObject):
            contents = contents.get_object()

        if isinstance(contents, StreamObject):
            return contents.decode_data()
        elif isinstance(contents, ArrayObject):
            # Multiple content streams
            data = []
            for item in contents:
                if isinstance(item, IndirectObject):
                    item = item.get_object()
                if isinstance(item, StreamObject):
                    data.append(item.decode_data())
            return b"\n".join(data)

        return b""

    def extract_text(self, visitor_text=None):
        """
        Extract text content from the page.

        Args:
            visitor_text: Optional callback function for each text segment

        Returns:
            Extracted text as string
        """
        content = self._get_content_stream()
        if not content:
            return ""

        # Decode if bytes
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    content = content.decode("latin-1")
                except:
                    return ""

        # Simple text extraction using regex
        # This is a basic implementation - real PDF text extraction is much more complex
        text_parts = []

        # Pattern for text showing operators
        # Tj - show string
        # TJ - show array
        # ' - move to next line and show
        # " - set spacing and show

        # Match strings in parentheses (literal strings)
        literal_pattern = r"\(([^)]*)\)\s*Tj"
        for match in re.finditer(literal_pattern, content):
            text = match.group(1)
            # Unescape
            text = text.replace("\\(", "(").replace("\\)", ")")
            text = text.replace("\\n", "\n").replace("\\r", "\r")
            text = text.replace("\\t", "\t")
            text = text.replace("\\\\", "\\")
            text_parts.append(text)
            if visitor_text:
                visitor_text(text, None, None, None, None)

        # Match hex strings
        hex_pattern = r"<([0-9A-Fa-f]+)>\s*Tj"
        for match in re.finditer(hex_pattern, content):
            hex_str = match.group(1)
            try:
                text = bytes.fromhex(hex_str).decode("utf-16-be")
                text_parts.append(text)
                if visitor_text:
                    visitor_text(text, None, None, None, None)
            except:
                pass

        # Match TJ arrays (simplified)
        tj_array_pattern = r"\[((?:[^]]+))\]\s*TJ"
        for match in re.finditer(tj_array_pattern, content):
            array_content = match.group(1)
            # Extract strings from array
            for str_match in re.finditer(r"\(([^)]*)\)", array_content):
                text = str_match.group(1)
                text = text.replace("\\(", "(").replace("\\)", ")")
                text_parts.append(text)
                if visitor_text:
                    visitor_text(text, None, None, None, None)

        return "".join(text_parts)

    @property
    def images(self):
        """
        Get embedded images from the page.

        Returns:
            List of image info dictionaries
        """
        images = []
        resources = self.get("/Resources")
        if isinstance(resources, IndirectObject):
            resources = resources.get_object()
        if not resources:
            return images

        xobjects = resources.get("/XObject")
        if isinstance(xobjects, IndirectObject):
            xobjects = xobjects.get_object()
        if not xobjects:
            return images

        for name, obj in xobjects.items():
            if isinstance(obj, IndirectObject):
                obj = obj.get_object()
            if obj and obj.get("/Subtype") == NameObject("Image"):
                images.append({
                    "name": str(name),
                    "width": int(obj.get("/Width", NumberObject(0)).value),
                    "height": int(obj.get("/Height", NumberObject(0)).value),
                    "color_space": str(obj.get("/ColorSpace", "")),
                    "bits_per_component": int(obj.get("/BitsPerComponent", NumberObject(8)).value),
                })

        return images


def create_blank_page(width=612, height=792):
    """
    Create a blank page with the specified dimensions.

    Args:
        width: Page width in points (default: US Letter)
        height: Page height in points (default: US Letter)

    Returns:
        New PageObject
    """
    page = PageObject()
    page.mediabox = RectangleObject([0, 0, width, height])
    page[NameObject("Resources")] = DictionaryObject()
    return page
