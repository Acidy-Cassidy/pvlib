"""
myrequests models - Response, Request, etc.
"""

import json as _json
from http.cookies import SimpleCookie
from typing import Dict, Optional, Any
from .exceptions import HTTPError, JSONDecodeError


class CaseInsensitiveDict(dict):
    """Dictionary with case-insensitive key access"""

    def __init__(self, data=None):
        super().__init__()
        if data:
            for key, value in data.items():
                self[key] = value

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __contains__(self, key):
        return super().__contains__(key.lower())

    def get(self, key, default=None):
        return super().get(key.lower(), default)


class Response:
    """HTTP Response object"""

    def __init__(self):
        self.status_code: int = 0
        self.headers: CaseInsensitiveDict = CaseInsensitiveDict()
        self.url: str = ""
        self.encoding: Optional[str] = None
        self._content: bytes = b""
        self.reason: str = ""
        self.cookies: Dict[str, str] = {}
        self.elapsed: float = 0.0
        self.request: Optional['PreparedRequest'] = None
        self.history: list = []

    @property
    def content(self) -> bytes:
        """Raw response content as bytes"""
        return self._content

    @property
    def text(self) -> str:
        """Response content as string"""
        encoding = self.encoding or self._detect_encoding()
        try:
            return self._content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return self._content.decode('utf-8', errors='replace')

    def _detect_encoding(self) -> str:
        """Detect encoding from headers or content"""
        content_type = self.headers.get('content-type', '')
        if 'charset=' in content_type:
            parts = content_type.split('charset=')
            if len(parts) > 1:
                return parts[1].split(';')[0].strip()
        return 'utf-8'

    def json(self, **kwargs) -> Any:
        """Parse response as JSON"""
        try:
            return _json.loads(self.text, **kwargs)
        except _json.JSONDecodeError as e:
            raise JSONDecodeError(f"JSON decode error: {e}")

    def raise_for_status(self) -> None:
        """Raise HTTPError if status code indicates an error"""
        if 400 <= self.status_code < 600:
            raise HTTPError(
                f"{self.status_code} Error: {self.reason} for url: {self.url}",
                response=self
            )

    @property
    def ok(self) -> bool:
        """True if status code is less than 400"""
        return self.status_code < 400

    @property
    def is_redirect(self) -> bool:
        """True if response is a redirect"""
        return self.status_code in (301, 302, 303, 307, 308)

    @property
    def apparent_encoding(self) -> str:
        """Encoding detected from content"""
        return self._detect_encoding()

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"

    def __bool__(self) -> bool:
        return self.ok


class PreparedRequest:
    """Prepared HTTP request ready to be sent"""

    def __init__(self):
        self.method: str = ""
        self.url: str = ""
        self.headers: Dict[str, str] = {}
        self.body: Optional[bytes] = None

    def __repr__(self) -> str:
        return f"<PreparedRequest [{self.method}]>"
