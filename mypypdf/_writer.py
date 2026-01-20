"""
PdfWriter class for writing PDF files.
"""

import io
import time
import zlib

from .generic import (
    DictionaryObject, ArrayObject, NameObject, NumberObject, StringObject,
    StreamObject, IndirectObject, RectangleObject
)
from ._page import PageObject, create_blank_page


class PdfWriter:
    """
    Write PDF files.

    Usage:
        writer = PdfWriter()
        writer.add_page(page)
        writer.write("output.pdf")
    """

    def __init__(self):
        """Initialize PdfWriter."""
        self._objects = []
        self._pages = []
        self._root = None
        self._info = None

        # Create root objects
        self._setup_document()

    def _setup_document(self):
        """Set up basic document structure."""
        # Catalog (root)
        self._root = DictionaryObject()
        self._root[NameObject("Type")] = NameObject("Catalog")

        # Pages tree root
        self._pages_root = DictionaryObject()
        self._pages_root[NameObject("Type")] = NameObject("Pages")
        self._pages_root[NameObject("Kids")] = ArrayObject()
        self._pages_root[NameObject("Count")] = NumberObject(0)

        self._root[NameObject("Pages")] = self._add_object(self._pages_root)
        self._add_object(self._root)

        # Info dictionary
        self._info = DictionaryObject()
        self._info[NameObject("Producer")] = StringObject("mypypdf")

    def _add_object(self, obj):
        """
        Add an object to the writer and return its indirect reference.

        Args:
            obj: PDF object to add

        Returns:
            IndirectObject reference
        """
        obj_num = len(self._objects) + 1
        self._objects.append(obj)
        return IndirectObject(obj_num, 0, None)

    def add_page(self, page, index=None):
        """
        Add a page to the document.

        Args:
            page: PageObject to add
            index: Position to insert (None = end)

        Returns:
            Self for chaining
        """
        if not isinstance(page, PageObject):
            # Try to convert dict-like to PageObject
            new_page = PageObject()
            new_page.update(page)
            page = new_page

        # Set parent reference
        page[NameObject("Parent")] = self._get_pages_ref()

        # Add to objects
        page_ref = self._add_object(page)

        # Add to pages list
        kids = self._pages_root[NameObject("Kids")]
        if index is None:
            kids.append(page_ref)
            self._pages.append(page)
        else:
            kids.insert(index, page_ref)
            self._pages.insert(index, page)

        # Update count
        self._pages_root[NameObject("Count")] = NumberObject(len(self._pages))

        return self

    def insert_page(self, page, index=0):
        """
        Insert a page at the specified index.

        Args:
            page: PageObject to insert
            index: Position to insert

        Returns:
            Self for chaining
        """
        return self.add_page(page, index)

    def add_blank_page(self, width=612, height=792):
        """
        Add a blank page with the specified dimensions.

        Args:
            width: Page width in points (default: US Letter)
            height: Page height in points

        Returns:
            The new PageObject
        """
        page = create_blank_page(width, height)
        self.add_page(page)
        return page

    def _get_pages_ref(self):
        """Get indirect reference to pages root."""
        # Find pages root in objects
        for i, obj in enumerate(self._objects):
            if obj is self._pages_root:
                return IndirectObject(i + 1, 0, None)
        return self._add_object(self._pages_root)

    @property
    def pages(self):
        """Get list of pages."""
        return self._pages

    def add_metadata(self, metadata):
        """
        Add metadata to the document.

        Args:
            metadata: Dictionary with metadata fields
                     (title, author, subject, creator, etc.)

        Returns:
            Self for chaining
        """
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if not key.startswith("/"):
                    key = "/" + key.title()
                self._info[NameObject(key)] = StringObject(str(value))
        return self

    def encrypt(self, user_password, owner_password=None, permissions=-1):
        """
        Encrypt the PDF with passwords.

        Args:
            user_password: User password (for opening)
            owner_password: Owner password (for permissions)
            permissions: Permission flags

        Returns:
            Self for chaining

        Note: This is a simplified stub - actual encryption is complex.
        """
        # Actual PDF encryption requires RC4/AES implementation
        return self

    def write(self, stream):
        """
        Write the PDF to a stream.

        Args:
            stream: File path or file-like object
        """
        if isinstance(stream, str):
            with open(stream, "wb") as f:
                self._write_to_stream(f)
        else:
            self._write_to_stream(stream)

    def _write_to_stream(self, stream):
        """Write PDF content to stream."""
        # PDF header
        stream.write(b"%PDF-1.4\n")
        stream.write(b"%\xe2\xe3\xcf\xd3\n")  # Binary marker

        # Track object positions for xref
        positions = []

        # Write objects
        for i, obj in enumerate(self._objects):
            positions.append(stream.tell())
            obj_num = i + 1
            stream.write(f"{obj_num} 0 obj\n".encode())

            if isinstance(obj, StreamObject):
                obj.write_to_stream(stream)
            elif isinstance(obj, DictionaryObject):
                obj.write_to_stream(stream)
            elif hasattr(obj, "write_to_stream"):
                obj.write_to_stream(stream)
            else:
                stream.write(str(obj).encode())

            stream.write(b"\nendobj\n\n")

        # Write xref table
        xref_pos = stream.tell()
        stream.write(b"xref\n")
        stream.write(f"0 {len(self._objects) + 1}\n".encode())
        stream.write(b"0000000000 65535 f \n")

        for pos in positions:
            stream.write(f"{pos:010d} 00000 n \n".encode())

        # Write trailer
        trailer = DictionaryObject()
        trailer[NameObject("Size")] = NumberObject(len(self._objects) + 1)

        # Find root reference
        for i, obj in enumerate(self._objects):
            if obj is self._root:
                trailer[NameObject("Root")] = IndirectObject(i + 1, 0, None)
                break

        # Add info reference
        info_ref = self._add_object(self._info)
        # Rewrite xref with info object
        positions.append(stream.tell())
        stream.write(f"{len(self._objects)} 0 obj\n".encode())
        self._info.write_to_stream(stream)
        stream.write(b"\nendobj\n\n")

        # Update trailer
        trailer[NameObject("Info")] = IndirectObject(len(self._objects), 0, None)

        stream.write(b"trailer\n")
        trailer.write_to_stream(stream)
        stream.write(b"\n")

        # Write startxref
        stream.write(f"startxref\n{xref_pos}\n".encode())
        stream.write(b"%%EOF\n")

    def clone_document_from_reader(self, reader):
        """
        Clone all pages from a reader.

        Args:
            reader: PdfReader instance

        Returns:
            Self for chaining
        """
        for page in reader.pages:
            self.add_page(page)
        return self

    def append_pages_from_reader(self, reader, after_page_append=None):
        """
        Append pages from a reader.

        Args:
            reader: PdfReader instance
            after_page_append: Callback after each page

        Returns:
            Self for chaining
        """
        for page in reader.pages:
            self.add_page(page)
            if after_page_append:
                after_page_append(page)
        return self
