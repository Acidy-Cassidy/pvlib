"""
myrequests exceptions
"""


class RequestException(Exception):
    """Base exception for myrequests"""
    pass


class ConnectionError(RequestException):
    """A connection error occurred"""
    pass


class Timeout(RequestException):
    """The request timed out"""
    pass


class HTTPError(RequestException):
    """An HTTP error occurred"""

    def __init__(self, message=None, response=None):
        super().__init__(message)
        self.response = response


class URLRequired(RequestException):
    """A valid URL is required"""
    pass


class TooManyRedirects(RequestException):
    """Too many redirects"""
    pass


class MissingSchema(RequestException):
    """The URL schema (e.g., http or https) is missing"""
    pass


class InvalidURL(RequestException):
    """The URL is invalid"""
    pass


class JSONDecodeError(RequestException):
    """JSON decoding failed"""
    pass
