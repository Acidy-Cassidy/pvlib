"""
myrequests API - Core HTTP functions
"""

import json as _json
import time
import ssl
import gzip
import zlib
from io import BytesIO
from typing import Optional, Dict, Any, Union
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler, HTTPCookieProcessor
from urllib.parse import urlencode, urlparse, urljoin
from urllib.error import URLError, HTTPError as URLHTTPError
from http.cookiejar import CookieJar

from .models import Response, PreparedRequest, CaseInsensitiveDict
from .exceptions import (
    RequestException, ConnectionError, Timeout, HTTPError,
    MissingSchema, InvalidURL, TooManyRedirects
)


# Default timeout in seconds
DEFAULT_TIMEOUT = 30

# Default headers
DEFAULT_HEADERS = {
    'User-Agent': 'myrequests/1.0',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}


def _build_url(url: str, params: Optional[Dict] = None) -> str:
    """Build URL with query parameters"""
    if not params:
        return url

    query_string = urlencode(params)
    separator = '&' if '?' in url else '?'
    return f"{url}{separator}{query_string}"


def _prepare_body(
    data: Optional[Union[Dict, str, bytes]] = None,
    json: Optional[Any] = None,
    files: Optional[Dict] = None
) -> tuple:
    """Prepare request body and content-type header"""
    content_type = None
    body = None

    if json is not None:
        body = _json.dumps(json).encode('utf-8')
        content_type = 'application/json'
    elif data is not None:
        if isinstance(data, dict):
            body = urlencode(data).encode('utf-8')
            content_type = 'application/x-www-form-urlencoded'
        elif isinstance(data, str):
            body = data.encode('utf-8')
        elif isinstance(data, bytes):
            body = data
    elif files is not None:
        # Simple multipart form handling
        boundary = '----MyRequestsBoundary'
        body_parts = []

        for field_name, file_info in files.items():
            if isinstance(file_info, tuple):
                filename, file_content = file_info[0], file_info[1]
                if len(file_info) > 2:
                    file_content_type = file_info[2]
                else:
                    file_content_type = 'application/octet-stream'
            else:
                filename = field_name
                file_content = file_info
                file_content_type = 'application/octet-stream'

            if hasattr(file_content, 'read'):
                file_content = file_content.read()
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')

            body_parts.append(f'--{boundary}\r\n'.encode())
            body_parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
            )
            body_parts.append(f'Content-Type: {file_content_type}\r\n\r\n'.encode())
            body_parts.append(file_content)
            body_parts.append(b'\r\n')

        body_parts.append(f'--{boundary}--\r\n'.encode())
        body = b''.join(body_parts)
        content_type = f'multipart/form-data; boundary={boundary}'

    return body, content_type


def _decompress_content(content: bytes, encoding: str) -> bytes:
    """Decompress gzip or deflate content"""
    if encoding == 'gzip':
        try:
            return gzip.decompress(content)
        except Exception:
            return content
    elif encoding == 'deflate':
        try:
            return zlib.decompress(content)
        except Exception:
            try:
                return zlib.decompress(content, -zlib.MAX_WBITS)
            except Exception:
                return content
    return content


def request(
    method: str,
    url: str,
    params: Optional[Dict] = None,
    data: Optional[Union[Dict, str, bytes]] = None,
    json: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    files: Optional[Dict] = None,
    auth: Optional[tuple] = None,
    timeout: Optional[float] = None,
    allow_redirects: bool = True,
    verify: bool = True,
    stream: bool = False,
    max_redirects: int = 30,
) -> Response:
    """
    Send an HTTP request.

    Parameters:
    -----------
    method : str
        HTTP method (GET, POST, PUT, DELETE, etc.)
    url : str
        URL to request
    params : dict, optional
        Query parameters to append to URL
    data : dict, str, or bytes, optional
        Request body data
    json : any, optional
        JSON data to send (sets Content-Type to application/json)
    headers : dict, optional
        HTTP headers
    cookies : dict, optional
        Cookies to send
    files : dict, optional
        Files to upload (multipart/form-data)
    auth : tuple, optional
        Basic auth credentials (username, password)
    timeout : float, optional
        Request timeout in seconds
    allow_redirects : bool
        Follow redirects (default True)
    verify : bool
        Verify SSL certificates (default True)
    stream : bool
        Stream response content (default False)
    max_redirects : int
        Maximum number of redirects to follow

    Returns:
    --------
    Response object
    """
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme:
        raise MissingSchema(f"Missing schema in URL: {url}")
    if parsed.scheme not in ('http', 'https'):
        raise InvalidURL(f"Invalid URL scheme: {parsed.scheme}")

    # Build URL with params
    full_url = _build_url(url, params)

    # Prepare headers
    req_headers = DEFAULT_HEADERS.copy()
    if headers:
        req_headers.update(headers)

    # Add cookies to headers
    if cookies:
        cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
        req_headers['Cookie'] = cookie_str

    # Add basic auth
    if auth:
        import base64
        credentials = base64.b64encode(f'{auth[0]}:{auth[1]}'.encode()).decode()
        req_headers['Authorization'] = f'Basic {credentials}'

    # Prepare body
    body, content_type = _prepare_body(data, json, files)
    if content_type and 'Content-Type' not in req_headers:
        req_headers['Content-Type'] = content_type

    # Create request
    req = Request(full_url, data=body, headers=req_headers, method=method.upper())

    # Prepare response
    response = Response()
    response.url = full_url

    # Create prepared request
    prepared = PreparedRequest()
    prepared.method = method.upper()
    prepared.url = full_url
    prepared.headers = req_headers
    prepared.body = body
    response.request = prepared

    # SSL context
    ssl_context = None
    if not verify:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    # Handle redirects manually if needed
    redirect_count = 0
    history = []

    start_time = time.time()

    while True:
        try:
            # Make request
            if ssl_context:
                resp = urlopen(req, timeout=timeout or DEFAULT_TIMEOUT, context=ssl_context)
            else:
                resp = urlopen(req, timeout=timeout or DEFAULT_TIMEOUT)

            # Build response
            response.status_code = resp.status
            response.reason = resp.reason
            response.url = resp.url
            response.headers = CaseInsensitiveDict(dict(resp.headers))

            # Parse cookies from response
            if 'set-cookie' in response.headers:
                cookie_header = response.headers['set-cookie']
                for cookie_part in cookie_header.split(','):
                    if '=' in cookie_part:
                        name, _, value = cookie_part.strip().partition('=')
                        value = value.split(';')[0]
                        response.cookies[name.strip()] = value.strip()

            # Read content
            content = resp.read()

            # Decompress if needed
            content_encoding = response.headers.get('content-encoding', '').lower()
            if content_encoding:
                content = _decompress_content(content, content_encoding)

            response._content = content
            response.history = history

            break

        except URLHTTPError as e:
            # HTTP error (4xx, 5xx)
            response.status_code = e.code
            response.reason = e.reason
            response.headers = CaseInsensitiveDict(dict(e.headers))
            response._content = e.read()
            response.history = history
            break

        except URLError as e:
            if 'timed out' in str(e.reason).lower():
                raise Timeout(f"Request timed out: {url}")
            raise ConnectionError(f"Connection error: {e.reason}")

        except Exception as e:
            if 'timed out' in str(e).lower():
                raise Timeout(f"Request timed out: {url}")
            raise RequestException(f"Request failed: {e}")

    response.elapsed = time.time() - start_time

    return response


def get(url: str, params: Optional[Dict] = None, **kwargs) -> Response:
    """Send a GET request"""
    return request('GET', url, params=params, **kwargs)


def post(url: str, data: Optional[Union[Dict, str, bytes]] = None,
         json: Optional[Any] = None, **kwargs) -> Response:
    """Send a POST request"""
    return request('POST', url, data=data, json=json, **kwargs)


def put(url: str, data: Optional[Union[Dict, str, bytes]] = None,
        json: Optional[Any] = None, **kwargs) -> Response:
    """Send a PUT request"""
    return request('PUT', url, data=data, json=json, **kwargs)


def patch(url: str, data: Optional[Union[Dict, str, bytes]] = None,
          json: Optional[Any] = None, **kwargs) -> Response:
    """Send a PATCH request"""
    return request('PATCH', url, data=data, json=json, **kwargs)


def delete(url: str, **kwargs) -> Response:
    """Send a DELETE request"""
    return request('DELETE', url, **kwargs)


def head(url: str, **kwargs) -> Response:
    """Send a HEAD request"""
    kwargs['allow_redirects'] = kwargs.get('allow_redirects', False)
    return request('HEAD', url, **kwargs)


def options(url: str, **kwargs) -> Response:
    """Send an OPTIONS request"""
    return request('OPTIONS', url, **kwargs)
