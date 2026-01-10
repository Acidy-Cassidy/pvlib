"""
myrequests - Your custom requests library

A simple HTTP library built on urllib, inspired by the requests library.
"""

from .api import (
    request,
    get,
    post,
    put,
    patch,
    delete,
    head,
    options,
)

from .models import Response, PreparedRequest, CaseInsensitiveDict

from .exceptions import (
    RequestException,
    ConnectionError,
    Timeout,
    HTTPError,
    URLRequired,
    TooManyRedirects,
    MissingSchema,
    InvalidURL,
    JSONDecodeError,
)

# Version
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

# Convenience access
codes = {
    'ok': 200,
    'created': 201,
    'accepted': 202,
    'no_content': 204,
    'moved_permanently': 301,
    'found': 302,
    'not_modified': 304,
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'method_not_allowed': 405,
    'conflict': 409,
    'gone': 410,
    'unprocessable_entity': 422,
    'too_many_requests': 429,
    'internal_server_error': 500,
    'bad_gateway': 502,
    'service_unavailable': 503,
    'gateway_timeout': 504,
}

__all__ = [
    'request',
    'get',
    'post',
    'put',
    'patch',
    'delete',
    'head',
    'options',
    'Response',
    'PreparedRequest',
    'CaseInsensitiveDict',
    'RequestException',
    'ConnectionError',
    'Timeout',
    'HTTPError',
    'URLRequired',
    'TooManyRedirects',
    'MissingSchema',
    'InvalidURL',
    'JSONDecodeError',
    'Session',
    'codes',
]

# Import Session after other imports to avoid circular imports
from .session import Session
