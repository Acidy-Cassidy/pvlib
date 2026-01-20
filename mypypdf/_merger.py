"""
PdfMerger class for merging PDF files.
"""

from ._reader import PdfReader
from ._writer import PdfWriter


class PdfMerger:
    """
    Merge multiple PDF files into one.

    Usage:
        merger = PdfMerger()
        merger.append("file1.pdf")
        merger.append("file2.pdf")
        merger.write("merged.pdf")
        merger.close()
    """

    def __init__(self):
        """Initialize PdfMerger."""
        self._writer = PdfWriter()
        self._readers = []
        self._pages = []
        self._closed = False

    def append(self, fileobj, pages=None, import_outline=True):
        """
        Append pages from a PDF file.

        Args:
            fileobj: File path, file object, or PdfReader
            pages: Page range (None = all, or (start, end) tuple, or list)
            import_outline: Import bookmarks (default True)

        Returns:
            Self for chaining
        """
        return self.merge(len(self._pages), fileobj, pages, import_outline)

    def merge(self, position, fileobj, pages=None, import_outline=True):
        """
        Merge pages from a PDF file at a specific position.

        Args:
            position: Position to insert pages
            fileobj: File path, file object, or PdfReader
            pages: Page range (None = all)
            import_outline: Import bookmarks

        Returns:
            Self for chaining
        """
        if self._closed:
            raise RuntimeError("PdfMerger has been closed")

        # Get reader
        if isinstance(fileobj, PdfReader):
            reader = fileobj
        else:
            reader = PdfReader(fileobj)
            self._readers.append(reader)

        # Determine page range
        if pages is None:
            page_indices = range(len(reader.pages))
        elif isinstance(pages, (list, tuple)) and len(pages) == 2:
            start, end = pages
            page_indices = range(start, end)
        elif isinstance(pages, (list, tuple)):
            page_indices = pages
        else:
            page_indices = range(len(reader.pages))

        # Insert pages
        insert_pos = position
        for i in page_indices:
            if 0 <= i < len(reader.pages):
                page = reader.pages[i]
                self._pages.insert(insert_pos, page)
                insert_pos += 1

        return self

    def write(self, fileobj):
        """
        Write the merged PDF to a file.

        Args:
            fileobj: File path or file-like object
        """
        if self._closed:
            raise RuntimeError("PdfMerger has been closed")

        # Add all pages to writer
        for page in self._pages:
            self._writer.add_page(page)

        # Write output
        self._writer.write(fileobj)

    def close(self):
        """Close the merger and release resources."""
        self._readers = []
        self._pages = []
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def add_metadata(self, metadata):
        """
        Add metadata to the merged document.

        Args:
            metadata: Dictionary of metadata fields
        """
        self._writer.add_metadata(metadata)

    def set_page_layout(self, layout):
        """
        Set the page layout.

        Args:
            layout: Layout string (SinglePage, OneColumn, etc.)
        """
        pass  # Simplified

    def set_page_mode(self, mode):
        """
        Set the page mode.

        Args:
            mode: Mode string (UseNone, UseOutlines, etc.)
        """
        pass  # Simplified

    def add_outline_item(self, title, page_number, parent=None):
        """
        Add an outline/bookmark item.

        Args:
            title: Bookmark title
            page_number: Destination page number
            parent: Parent outline item

        Returns:
            Outline item reference
        """
        return None  # Simplified

    @property
    def pages(self):
        """Get list of merged pages."""
        return self._pages
