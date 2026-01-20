"""
PDF object types.
Represents the basic objects in PDF files.
"""

import re
import zlib


class PdfObject:
    """Base class for all PDF objects."""

    def write_to_stream(self, stream):
        """Write object to output stream."""
        raise NotImplementedError


class NullObject(PdfObject):
    """PDF null object."""

    def write_to_stream(self, stream):
        stream.write(b"null")

    def __repr__(self):
        return "NullObject"


class BooleanObject(PdfObject):
    """PDF boolean object."""

    def __init__(self, value):
        self.value = bool(value)

    def write_to_stream(self, stream):
        stream.write(b"true" if self.value else b"false")

    def __repr__(self):
        return f"BooleanObject({self.value})"

    def __bool__(self):
        return self.value


class NumberObject(PdfObject):
    """PDF numeric object (integer or real)."""

    def __init__(self, value):
        if isinstance(value, float):
            self.value = value
        else:
            self.value = int(value)

    def write_to_stream(self, stream):
        if isinstance(self.value, float):
            stream.write(f"{self.value:.6f}".rstrip("0").rstrip(".").encode())
        else:
            stream.write(str(self.value).encode())

    def __repr__(self):
        return f"NumberObject({self.value})"

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)


class NameObject(PdfObject):
    """PDF name object (like /Type, /Page, etc.)."""

    def __init__(self, name):
        if name.startswith("/"):
            self.name = name
        else:
            self.name = "/" + name

    def write_to_stream(self, stream):
        stream.write(self.name.encode())

    def __repr__(self):
        return f"NameObject({self.name})"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, NameObject):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other or self.name[1:] == other
        return False

    def __hash__(self):
        return hash(self.name)


class StringObject(PdfObject):
    """PDF string object (literal or hexadecimal)."""

    def __init__(self, value):
        self.value = value

    def write_to_stream(self, stream):
        # Escape special characters
        escaped = self.value.replace("\\", "\\\\")
        escaped = escaped.replace("(", "\\(")
        escaped = escaped.replace(")", "\\)")
        stream.write(f"({escaped})".encode())

    def __repr__(self):
        return f"StringObject({self.value!r})"

    def __str__(self):
        return self.value


class HexStringObject(StringObject):
    """PDF hexadecimal string object."""

    def write_to_stream(self, stream):
        hex_str = self.value.encode().hex()
        stream.write(f"<{hex_str}>".encode())


class ArrayObject(PdfObject, list):
    """PDF array object."""

    def write_to_stream(self, stream):
        stream.write(b"[")
        for i, item in enumerate(self):
            if i > 0:
                stream.write(b" ")
            if isinstance(item, PdfObject):
                item.write_to_stream(stream)
            else:
                stream.write(str(item).encode())
        stream.write(b"]")

    def __repr__(self):
        return f"ArrayObject({list.__repr__(self)})"


class DictionaryObject(PdfObject, dict):
    """PDF dictionary object."""

    def write_to_stream(self, stream):
        stream.write(b"<<")
        for key, value in self.items():
            stream.write(b"\n")
            if isinstance(key, NameObject):
                key.write_to_stream(stream)
            else:
                NameObject(key).write_to_stream(stream)
            stream.write(b" ")
            if isinstance(value, PdfObject):
                value.write_to_stream(stream)
            else:
                stream.write(str(value).encode())
        stream.write(b"\n>>")

    def __repr__(self):
        return f"DictionaryObject({dict.__repr__(self)})"

    def get_object(self, key):
        """Get value, resolving indirect references."""
        value = self.get(key)
        if isinstance(value, IndirectObject):
            return value.get_object()
        return value


class StreamObject(DictionaryObject):
    """PDF stream object (dictionary + data)."""

    def __init__(self, data=b"", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = data
        self._decoded_data = None

    @property
    def data(self):
        """Get decoded stream data."""
        if self._decoded_data is not None:
            return self._decoded_data
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self._decoded_data = None

    def decode_data(self):
        """Decode stream data based on filters."""
        if self._decoded_data is not None:
            return self._decoded_data

        filters = self.get("/Filter")
        data = self._data

        if filters:
            if isinstance(filters, NameObject):
                filters = [filters]
            elif isinstance(filters, ArrayObject):
                filters = list(filters)

            for f in filters:
                filter_name = str(f)
                if filter_name in ("/FlateDecode", "/Fl"):
                    try:
                        data = zlib.decompress(data)
                    except zlib.error:
                        pass  # Keep original data if decompression fails

        self._decoded_data = data
        return data

    def write_to_stream(self, stream):
        # Update length
        self[NameObject("Length")] = NumberObject(len(self._data))
        # Write dictionary
        super().write_to_stream(stream)
        stream.write(b"\nstream\n")
        stream.write(self._data)
        stream.write(b"\nendstream")


class IndirectObject(PdfObject):
    """PDF indirect object reference."""

    def __init__(self, object_number, generation, pdf=None):
        self.object_number = object_number
        self.generation = generation
        self.pdf = pdf

    def write_to_stream(self, stream):
        stream.write(f"{self.object_number} {self.generation} R".encode())

    def get_object(self):
        """Resolve the indirect reference."""
        if self.pdf:
            return self.pdf.get_object(self)
        return None

    def __repr__(self):
        return f"IndirectObject({self.object_number}, {self.generation})"

    def __eq__(self, other):
        if isinstance(other, IndirectObject):
            return (self.object_number == other.object_number and
                    self.generation == other.generation)
        return False

    def __hash__(self):
        return hash((self.object_number, self.generation))


class RectangleObject(ArrayObject):
    """PDF rectangle object."""

    def __init__(self, arr=None):
        super().__init__()
        if arr:
            for v in arr[:4]:
                if isinstance(v, (int, float)):
                    self.append(NumberObject(v))
                else:
                    self.append(v)
        else:
            for _ in range(4):
                self.append(NumberObject(0))

    @property
    def left(self):
        return float(self[0].value if isinstance(self[0], NumberObject) else self[0])

    @property
    def bottom(self):
        return float(self[1].value if isinstance(self[1], NumberObject) else self[1])

    @property
    def right(self):
        return float(self[2].value if isinstance(self[2], NumberObject) else self[2])

    @property
    def top(self):
        return float(self[3].value if isinstance(self[3], NumberObject) else self[3])

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.top - self.bottom


class DocumentInformation(DictionaryObject):
    """PDF document information dictionary."""

    @property
    def title(self):
        return str(self.get("/Title", ""))

    @property
    def author(self):
        return str(self.get("/Author", ""))

    @property
    def subject(self):
        return str(self.get("/Subject", ""))

    @property
    def creator(self):
        return str(self.get("/Creator", ""))

    @property
    def producer(self):
        return str(self.get("/Producer", ""))

    @property
    def creation_date(self):
        return str(self.get("/CreationDate", ""))

    @property
    def modification_date(self):
        return str(self.get("/ModDate", ""))
