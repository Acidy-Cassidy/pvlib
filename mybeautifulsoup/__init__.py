"""
mybeautifulsoup - Your custom BeautifulSoup library

A simple HTML/XML parser built on Python's html.parser, inspired by Beautiful Soup 4.
"""

from .soup import BeautifulSoup, BeautifulStoneSoup, SoupStrainer, ResultSet
from .element import Tag, NavigableString, Comment
from .parser import (
    TreeBuilder,
    HTMLTreeBuilder,
    LXMLTreeBuilder,
    XMLTreeBuilder,
    get_tree_builder,
)

# Version
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

# Commonly used features
__all__ = [
    # Main classes
    'BeautifulSoup',
    'BeautifulStoneSoup',
    'SoupStrainer',
    'ResultSet',

    # Element classes
    'Tag',
    'NavigableString',
    'Comment',

    # Tree builders
    'TreeBuilder',
    'HTMLTreeBuilder',
    'LXMLTreeBuilder',
    'XMLTreeBuilder',
    'get_tree_builder',
]
