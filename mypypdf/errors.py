"""
Custom exceptions for mypypdf.
"""


class PdfReadError(Exception):
    """Error reading PDF file."""
    pass


class PdfReadWarning(UserWarning):
    """Warning during PDF reading."""
    pass


class EmptyFileError(PdfReadError):
    """PDF file is empty."""
    pass


class FileNotDecryptedError(PdfReadError):
    """PDF file is encrypted and not decrypted."""
    pass


class PdfWriteError(Exception):
    """Error writing PDF file."""
    pass


class PageSizeNotDefinedError(Exception):
    """Page size could not be determined."""
    pass
