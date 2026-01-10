"""
myrequests Session - Persistent session for HTTP requests
"""

from typing import Optional, Dict, Any, Union
from .api import request as _request
from .models import Response, CaseInsensitiveDict


class Session:
    """
    Session object for making HTTP requests with persistent settings.

    Provides cookie persistence, connection pooling hints, and default
    configurations across requests.

    Usage:
        with Session() as session:
            session.get('https://api.example.com/resource')
    """

    def __init__(self):
        self.headers: Dict[str, str] = {}
        self.cookies: Dict[str, str] = {}
        self.auth: Optional[tuple] = None
        self.verify: bool = True
        self.timeout: Optional[float] = None
        self.max_redirects: int = 30
        self.trust_env: bool = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Close the session (cleanup if needed)"""
        pass

    def _merge_settings(self, kwargs: Dict) -> Dict:
        """Merge session settings with request-specific settings"""
        # Merge headers
        merged_headers = self.headers.copy()
        if 'headers' in kwargs and kwargs['headers']:
            merged_headers.update(kwargs['headers'])
        kwargs['headers'] = merged_headers

        # Merge cookies
        merged_cookies = self.cookies.copy()
        if 'cookies' in kwargs and kwargs['cookies']:
            merged_cookies.update(kwargs['cookies'])
        kwargs['cookies'] = merged_cookies

        # Use session auth if not specified
        if 'auth' not in kwargs or kwargs['auth'] is None:
            kwargs['auth'] = self.auth

        # Use session verify if not specified
        if 'verify' not in kwargs:
            kwargs['verify'] = self.verify

        # Use session timeout if not specified
        if 'timeout' not in kwargs or kwargs['timeout'] is None:
            kwargs['timeout'] = self.timeout

        # Use session max_redirects if not specified
        if 'max_redirects' not in kwargs:
            kwargs['max_redirects'] = self.max_redirects

        return kwargs

    def _update_cookies(self, response: Response):
        """Update session cookies from response"""
        if response.cookies:
            self.cookies.update(response.cookies)

    def request(
        self,
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
        verify: bool = None,
        stream: bool = False,
        max_redirects: int = None,
    ) -> Response:
        """Send a request with session settings"""
        kwargs = {
            'params': params,
            'data': data,
            'json': json,
            'headers': headers,
            'cookies': cookies,
            'files': files,
            'auth': auth,
            'timeout': timeout,
            'allow_redirects': allow_redirects,
            'verify': verify if verify is not None else self.verify,
            'stream': stream,
            'max_redirects': max_redirects if max_redirects is not None else self.max_redirects,
        }

        kwargs = self._merge_settings(kwargs)

        response = _request(method, url, **kwargs)

        # Update session cookies from response
        self._update_cookies(response)

        return response

    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Response:
        """Send a GET request"""
        return self.request('GET', url, params=params, **kwargs)

    def post(self, url: str, data: Optional[Union[Dict, str, bytes]] = None,
             json: Optional[Any] = None, **kwargs) -> Response:
        """Send a POST request"""
        return self.request('POST', url, data=data, json=json, **kwargs)

    def put(self, url: str, data: Optional[Union[Dict, str, bytes]] = None,
            json: Optional[Any] = None, **kwargs) -> Response:
        """Send a PUT request"""
        return self.request('PUT', url, data=data, json=json, **kwargs)

    def patch(self, url: str, data: Optional[Union[Dict, str, bytes]] = None,
              json: Optional[Any] = None, **kwargs) -> Response:
        """Send a PATCH request"""
        return self.request('PATCH', url, data=data, json=json, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        """Send a DELETE request"""
        return self.request('DELETE', url, **kwargs)

    def head(self, url: str, **kwargs) -> Response:
        """Send a HEAD request"""
        kwargs['allow_redirects'] = kwargs.get('allow_redirects', False)
        return self.request('HEAD', url, **kwargs)

    def options(self, url: str, **kwargs) -> Response:
        """Send an OPTIONS request"""
        return self.request('OPTIONS', url, **kwargs)
