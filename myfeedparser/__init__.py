"""
myfeedparser - Educational feedparser implementation
Mirrors feedparser API for learning purposes.

Supports RSS 0.9x, 1.0, 2.0 and Atom 0.3, 1.0 feeds.
"""

__version__ = "0.1.0"

from .parser import parse, FeedParser
from .models import FeedParserDict
from .dates import _parse_date

__all__ = [
    "parse",
    "FeedParser",
    "FeedParserDict",
    "_parse_date",
]
