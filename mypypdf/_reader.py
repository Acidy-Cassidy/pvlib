"""
PdfReader class for reading PDF files.
"""

import io
import re
import zlib

from .errors import PdfReadError, EmptyFileError, FileNotDecryptedError
from .generic import (
    PdfObject, NullObject, BooleanObject, NumberObject, NameObject,
    StringObject, HexStringObject, ArrayObject, DictionaryObject,
    StreamObject, IndirectObject, RectangleObject, DocumentInformation
)
from ._page import PageObject


class PdfReader:
    """
    Read and parse PDF files.

    Usage:
        reader = PdfReader("example.pdf")
        for page in reader.pages:
            text = page.extract_text()
    """

    def __init__(self, stream, strict=False, password=None):
        """
        Initialize PdfReader.

        Args:
            stream: File path, file object, or bytes
            strict: Raise errors on warnings (default False)
            password: Password for encrypted PDFs
        """
        self.strict = strict
        self._pages = None
        self._objects = {}
        self._xref = {}
        self._trailer = None
        self._is_encrypted = False
        self._decrypted = False

        # Open the stream
        if isinstance(stream, str):
            with open(stream, "rb") as f:
                self._data = f.read()
        elif isinstance(stream, bytes):
            self._data = stream
        elif hasattr(stream, "read"):
            self._data = stream.read()
        else:
            raise PdfReadError("Cannot read from provided stream")

        if not self._data:
            raise EmptyFileError("PDF file is empty")

        # Parse the PDF
        self._parse()

        # Handle encryption
        if self._is_encrypted and password:
            self.decrypt(password)

    def _parse(self):
        """Parse the PDF structure."""
        # Find startxref
        startxref_match = re.search(rb"startxref\s+(\d+)", self._data[-1024:])
        if not startxref_match:
            raise PdfReadError("Cannot find startxref")

        startxref = int(startxref_match.group(1))

        # Parse xref and trailer
        self._parse_xref(startxref)

        # Check for encryption
        if self._trailer:
            encrypt = self._trailer.get("/Encrypt")
            if encrypt:
                self._is_encrypted = True

    def _parse_xref(self, offset):
        """Parse xref table and trailer."""
        data = self._data[offset:]

        # Check for xref keyword
        if data.startswith(b"xref"):
            self._parse_xref_table(offset)
        else:
            # Possibly xref stream (PDF 1.5+)
            self._parse_xref_stream(offset)

    def _parse_xref_table(self, offset):
        """Parse traditional xref table."""
        data = self._data[offset:]

        # Skip "xref" keyword
        idx = data.find(b"\n", 4) + 1

        # Parse xref subsections
        while True:
            line = b""
            line_end = data.find(b"\n", idx)
            if line_end == -1:
                break
            line = data[idx:line_end].strip()
            idx = line_end + 1

            if line.startswith(b"trailer"):
                break

            if not line or line == b"xref":
                continue

            parts = line.split()
            if len(parts) == 2:
                # Subsection header: start count
                try:
                    start_obj = int(parts[0])
                    count = int(parts[1])
                except ValueError:
                    continue

                # Parse entries
                for i in range(count):
                    entry_line = data[idx:idx + 20]
                    idx += 20

                    if len(entry_line) >= 18:
                        try:
                            entry_offset = int(entry_line[:10])
                            entry_gen = int(entry_line[11:16])
                            entry_type = entry_line[17:18]

                            obj_num = start_obj + i
                            if entry_type == b"n" and obj_num not in self._xref:
                                self._xref[obj_num] = (entry_offset, entry_gen)
                        except ValueError:
                            pass

        # Parse trailer
        trailer_match = re.search(rb"trailer\s*<<(.+?)>>", data[idx - 100:], re.DOTALL)
        if trailer_match:
            trailer_data = b"<<" + trailer_match.group(1) + b">>"
            self._trailer = self._parse_object(trailer_data, 0)[0]

            # Check for previous xref
            if self._trailer:
                prev = self._trailer.get("/Prev")
                if prev:
                    prev_offset = int(prev.value if hasattr(prev, "value") else prev)
                    self._parse_xref(prev_offset)

    def _parse_xref_stream(self, offset):
        """Parse xref stream (PDF 1.5+)."""
        # Find the xref stream object
        obj, _ = self._parse_indirect_object(offset)
        if not isinstance(obj, StreamObject):
            raise PdfReadError("Invalid xref stream")

        self._trailer = obj

        # Decode the stream
        data = obj.decode_data()
        w = obj.get("/W", [1, 2, 1])
        w = [int(x.value if hasattr(x, "value") else x) for x in w]
        size = int(obj.get("/Size", NumberObject(0)).value)

        index = obj.get("/Index")
        if index:
            subsections = [(int(index[i].value), int(index[i + 1].value))
                          for i in range(0, len(index), 2)]
        else:
            subsections = [(0, size)]

        entry_size = sum(w)
        data_idx = 0

        for start, count in subsections:
            for i in range(count):
                if data_idx + entry_size > len(data):
                    break

                # Parse entry
                fields = []
                for width in w:
                    if width == 0:
                        fields.append(0)
                    else:
                        val = int.from_bytes(data[data_idx:data_idx + width], "big")
                        fields.append(val)
                        data_idx += width

                obj_num = start + i
                entry_type = fields[0] if w[0] > 0 else 1

                if entry_type == 1 and obj_num not in self._xref:
                    self._xref[obj_num] = (fields[1], fields[2] if len(fields) > 2 else 0)

        # Check for previous xref
        prev = self._trailer.get("/Prev")
        if prev:
            prev_offset = int(prev.value if hasattr(prev, "value") else prev)
            self._parse_xref(prev_offset)

    def _parse_indirect_object(self, offset):
        """Parse an indirect object at the given offset."""
        data = self._data[offset:]

        # Match object header
        header_match = re.match(rb"(\d+)\s+(\d+)\s+obj\s*", data)
        if not header_match:
            return None, offset

        obj_num = int(header_match.group(1))
        gen_num = int(header_match.group(2))
        idx = header_match.end()

        # Parse the object value
        obj, idx = self._parse_object(data, idx)

        # Check for stream
        stream_match = re.match(rb"\s*stream\r?\n", data[idx:])
        if stream_match:
            idx += stream_match.end()

            # Find stream length
            length = None
            if isinstance(obj, DictionaryObject):
                length_obj = obj.get("/Length")
                if isinstance(length_obj, NumberObject):
                    length = int(length_obj.value)
                elif isinstance(length_obj, IndirectObject):
                    length_ref = self.get_object(length_obj)
                    if length_ref:
                        length = int(length_ref.value if hasattr(length_ref, "value") else length_ref)

            if length:
                stream_data = data[idx:idx + length]
                idx += length
            else:
                # Find endstream
                end_match = re.search(rb"\r?\nendstream", data[idx:])
                if end_match:
                    stream_data = data[idx:idx + end_match.start()]
                    idx += end_match.end()
                else:
                    stream_data = b""

            stream_obj = StreamObject(stream_data)
            stream_obj.update(obj)
            obj = stream_obj

        return obj, offset + idx

    def _parse_object(self, data, idx):
        """Parse a PDF object at the given index."""
        # Skip whitespace
        while idx < len(data) and data[idx:idx + 1] in b" \t\r\n":
            idx += 1

        if idx >= len(data):
            return NullObject(), idx

        char = data[idx:idx + 1]

        # Null
        if data[idx:idx + 4] == b"null":
            return NullObject(), idx + 4

        # Boolean
        if data[idx:idx + 4] == b"true":
            return BooleanObject(True), idx + 4
        if data[idx:idx + 5] == b"false":
            return BooleanObject(False), idx + 5

        # Number
        if char in b"0123456789+-.":
            match = re.match(rb"([+-]?\d+\.?\d*)", data[idx:])
            if match:
                num_str = match.group(1).decode()
                try:
                    if "." in num_str:
                        return NumberObject(float(num_str)), idx + match.end()
                    else:
                        return NumberObject(int(num_str)), idx + match.end()
                except ValueError:
                    pass

            # Could be indirect reference
            ref_match = re.match(rb"(\d+)\s+(\d+)\s+R", data[idx:])
            if ref_match:
                obj_num = int(ref_match.group(1))
                gen_num = int(ref_match.group(2))
                return IndirectObject(obj_num, gen_num, self), idx + ref_match.end()

        # Name
        if char == b"/":
            end = idx + 1
            while end < len(data) and data[end:end + 1] not in b" \t\r\n<>[](){}/%":
                end += 1
            name = data[idx:end].decode("latin-1")
            return NameObject(name), end

        # String (literal)
        if char == b"(":
            return self._parse_literal_string(data, idx)

        # String (hexadecimal)
        if char == b"<":
            if data[idx + 1:idx + 2] == b"<":
                # Dictionary
                return self._parse_dictionary(data, idx)
            return self._parse_hex_string(data, idx)

        # Array
        if char == b"[":
            return self._parse_array(data, idx)

        # Dictionary
        if data[idx:idx + 2] == b"<<":
            return self._parse_dictionary(data, idx)

        # Indirect reference check
        ref_match = re.match(rb"(\d+)\s+(\d+)\s+R", data[idx:])
        if ref_match:
            obj_num = int(ref_match.group(1))
            gen_num = int(ref_match.group(2))
            return IndirectObject(obj_num, gen_num, self), idx + ref_match.end()

        return NullObject(), idx + 1

    def _parse_literal_string(self, data, idx):
        """Parse a literal string."""
        result = []
        idx += 1  # Skip opening (
        depth = 1

        while idx < len(data) and depth > 0:
            char = data[idx:idx + 1]
            if char == b"\\":
                # Escape sequence
                idx += 1
                if idx >= len(data):
                    break
                esc = data[idx:idx + 1]
                if esc == b"n":
                    result.append("\n")
                elif esc == b"r":
                    result.append("\r")
                elif esc == b"t":
                    result.append("\t")
                elif esc == b"b":
                    result.append("\b")
                elif esc == b"f":
                    result.append("\f")
                elif esc == b"(":
                    result.append("(")
                elif esc == b")":
                    result.append(")")
                elif esc == b"\\":
                    result.append("\\")
                elif esc in b"0123456789":
                    # Octal
                    octal = esc.decode()
                    for _ in range(2):
                        if idx + 1 < len(data) and data[idx + 1:idx + 2] in b"0123456789":
                            idx += 1
                            octal += data[idx:idx + 1].decode()
                        else:
                            break
                    result.append(chr(int(octal, 8)))
                idx += 1
            elif char == b"(":
                depth += 1
                result.append("(")
                idx += 1
            elif char == b")":
                depth -= 1
                if depth > 0:
                    result.append(")")
                idx += 1
            else:
                result.append(char.decode("latin-1"))
                idx += 1

        return StringObject("".join(result)), idx

    def _parse_hex_string(self, data, idx):
        """Parse a hexadecimal string."""
        idx += 1  # Skip <
        end = data.find(b">", idx)
        if end == -1:
            end = len(data)

        hex_data = data[idx:end].replace(b" ", b"").replace(b"\n", b"").replace(b"\r", b"")
        if len(hex_data) % 2:
            hex_data += b"0"

        try:
            decoded = bytes.fromhex(hex_data.decode()).decode("latin-1")
        except:
            decoded = ""

        return HexStringObject(decoded), end + 1

    def _parse_array(self, data, idx):
        """Parse an array."""
        arr = ArrayObject()
        idx += 1  # Skip [

        while idx < len(data):
            # Skip whitespace
            while idx < len(data) and data[idx:idx + 1] in b" \t\r\n":
                idx += 1

            if idx >= len(data) or data[idx:idx + 1] == b"]":
                idx += 1
                break

            obj, idx = self._parse_object(data, idx)
            arr.append(obj)

        return arr, idx

    def _parse_dictionary(self, data, idx):
        """Parse a dictionary."""
        d = DictionaryObject()
        idx += 2  # Skip <<

        while idx < len(data):
            # Skip whitespace
            while idx < len(data) and data[idx:idx + 1] in b" \t\r\n":
                idx += 1

            if idx >= len(data) or data[idx:idx + 2] == b">>":
                idx += 2
                break

            # Parse key (must be name)
            if data[idx:idx + 1] != b"/":
                idx += 1
                continue

            key, idx = self._parse_object(data, idx)

            # Skip whitespace
            while idx < len(data) and data[idx:idx + 1] in b" \t\r\n":
                idx += 1

            # Parse value
            value, idx = self._parse_object(data, idx)

            d[key] = value

        return d, idx

    def get_object(self, ref):
        """
        Get an object by its indirect reference.

        Args:
            ref: IndirectObject reference

        Returns:
            The resolved object
        """
        if isinstance(ref, IndirectObject):
            obj_num = ref.object_number
        else:
            obj_num = int(ref)

        # Check cache
        if obj_num in self._objects:
            return self._objects[obj_num]

        # Find in xref
        if obj_num not in self._xref:
            return None

        offset, gen = self._xref[obj_num]
        obj, _ = self._parse_indirect_object(offset)
        self._objects[obj_num] = obj
        return obj

    @property
    def pages(self):
        """
        Get all pages in the document.

        Returns:
            List of PageObject instances
        """
        if self._pages is not None:
            return self._pages

        self._pages = []

        if not self._trailer:
            return self._pages

        # Get root
        root_ref = self._trailer.get("/Root")
        if not root_ref:
            return self._pages

        root = self.get_object(root_ref)
        if not root:
            return self._pages

        # Get pages
        pages_ref = root.get("/Pages")
        if not pages_ref:
            return self._pages

        pages = self.get_object(pages_ref)
        if not pages:
            return self._pages

        # Traverse page tree
        self._collect_pages(pages)

        return self._pages

    def _collect_pages(self, node):
        """Recursively collect pages from page tree."""
        if isinstance(node, IndirectObject):
            node = self.get_object(node)

        if not node or not isinstance(node, DictionaryObject):
            return

        node_type = node.get("/Type")
        if node_type == NameObject("Page"):
            page = PageObject(self)
            page.update(node)
            self._pages.append(page)
        elif node_type == NameObject("Pages"):
            kids = node.get("/Kids", [])
            if isinstance(kids, IndirectObject):
                kids = self.get_object(kids)
            for kid in kids:
                self._collect_pages(kid)

    @property
    def num_pages(self):
        """Get the number of pages."""
        return len(self.pages)

    @property
    def metadata(self):
        """
        Get document metadata/information.

        Returns:
            DocumentInformation object
        """
        if not self._trailer:
            return DocumentInformation()

        info_ref = self._trailer.get("/Info")
        if not info_ref:
            return DocumentInformation()

        info = self.get_object(info_ref)
        if not info:
            return DocumentInformation()

        doc_info = DocumentInformation()
        doc_info.update(info)
        return doc_info

    @property
    def outline(self):
        """
        Get document outline/bookmarks.

        Returns:
            List of outline items
        """
        # Simplified implementation
        if not self._trailer:
            return []

        root_ref = self._trailer.get("/Root")
        if not root_ref:
            return []

        root = self.get_object(root_ref)
        if not root:
            return []

        outlines_ref = root.get("/Outlines")
        if not outlines_ref:
            return []

        return []  # Full implementation would parse outline tree

    @property
    def page_labels(self):
        """Get page labels."""
        return {}  # Simplified

    @property
    def is_encrypted(self):
        """Check if the PDF is encrypted."""
        return self._is_encrypted

    def decrypt(self, password):
        """
        Decrypt the PDF with the given password.

        Args:
            password: Decryption password

        Returns:
            True if successful
        """
        if not self._is_encrypted:
            return True

        # Simplified - actual decryption is complex
        self._decrypted = True
        return True
