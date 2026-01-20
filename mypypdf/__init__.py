"""
mypypdf - Educational pypdf implementation
Mirrors pypdf API for learning purposes.

Supports basic PDF reading, writing, and merging.
"""

__version__ = "0.1.0"

from ._reader import PdfReader
from ._writer import PdfWriter
from ._merger import PdfMerger
from ._page import PageObject, create_blank_page
from .errors import (
    PdfReadError,
    PdfReadWarning,
    EmptyFileError,
    FileNotDecryptedError,
    PdfWriteError,
    PageSizeNotDefinedError,
)
from .generic import (
    PdfObject,
    NullObject,
    BooleanObject,
    NumberObject,
    NameObject,
    StringObject,
    ArrayObject,
    DictionaryObject,
    StreamObject,
    IndirectObject,
    RectangleObject,
    DocumentInformation,
)

__all__ = [
    # Main classes
    "PdfReader",
    "PdfWriter",
    "PdfMerger",
    "PageObject",
    # Helpers
    "create_blank_page",
    # Errors
    "PdfReadError",
    "PdfReadWarning",
    "EmptyFileError",
    "FileNotDecryptedError",
    "PdfWriteError",
    "PageSizeNotDefinedError",
    # Generic objects
    "PdfObject",
    "NullObject",
    "BooleanObject",
    "NumberObject",
    "NameObject",
    "StringObject",
    "ArrayObject",
    "DictionaryObject",
    "StreamObject",
    "IndirectObject",
    "RectangleObject",
    "DocumentInformation",
]
