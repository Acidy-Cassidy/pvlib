"""
mybeautifulsoup.soup - Main BeautifulSoup class

Provides the main BeautifulSoup class for parsing and navigating HTML/XML documents.
"""

from typing import Optional, Union, List, Any, Iterator
import re

from .element import Tag, NavigableString, Comment
from .parser import get_tree_builder, HTMLTreeBuilder


class BeautifulSoup(Tag):
    """
    Main class for parsing HTML/XML and navigating the document tree.

    Usage:
        soup = BeautifulSoup('<html><body>Hello</body></html>', 'html.parser')
        print(soup.body.string)  # Hello
    """

    ROOT_TAG_NAME = '[document]'
    DEFAULT_BUILDER_FEATURES = ['html.parser']

    def __init__(
        self,
        markup: Union[str, bytes] = '',
        features: Optional[Union[str, List[str]]] = None,
        builder: Optional[Any] = None,
        parse_only: Optional[Any] = None,
        from_encoding: Optional[str] = None,
        exclude_encodings: Optional[List[str]] = None,
        element_classes: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize BeautifulSoup.

        Parameters:
        -----------
        markup : str or bytes
            The HTML/XML content to parse
        features : str or list
            Parser to use: 'html.parser', 'lxml', 'lxml-xml', 'xml'
        builder : TreeBuilder, optional
            A custom tree builder instance
        parse_only : SoupStrainer, optional
            Only parse elements matching this filter
        from_encoding : str, optional
            Document encoding (for bytes input)
        exclude_encodings : list, optional
            Encodings to exclude when auto-detecting
        element_classes : dict, optional
            Custom classes to use for elements
        """
        super().__init__(name=self.ROOT_TAG_NAME)

        self.original_encoding = from_encoding
        self.declared_html_encoding = None
        self.contains_replacement_characters = False
        self.parse_only = parse_only
        self.element_classes = element_classes or {}

        # Handle bytes input
        if isinstance(markup, bytes):
            markup = self._decode_markup(markup, from_encoding)

        # Get or create tree builder
        if builder is None:
            if features is None:
                features = self.DEFAULT_BUILDER_FEATURES
            builder = get_tree_builder(features)

        self.builder = builder

        # Parse the markup
        if markup:
            self._feed(markup)

    def _decode_markup(self, markup: bytes, encoding: Optional[str] = None) -> str:
        """Decode bytes markup to string."""
        if encoding:
            try:
                return markup.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                pass

        # Try common encodings
        encodings = ['utf-8', 'latin-1', 'windows-1252', 'ascii']

        for enc in encodings:
            try:
                result = markup.decode(enc)
                self.original_encoding = enc
                return result
            except (UnicodeDecodeError, LookupError):
                continue

        # Last resort: decode with replacement
        self.contains_replacement_characters = True
        return markup.decode('utf-8', errors='replace')

    def _feed(self, markup: str):
        """Feed markup to the parser and build the tree."""
        self.builder.reset()

        # Parse the markup
        root = self.builder.feed(markup)

        # Copy the parsed tree to this soup object
        if root is not None:
            self.contents = root.contents
            for child in self.contents:
                child.parent = self
            self._update_sibling_links()

    def reset(self):
        """Reset the soup, removing all parsed content."""
        self.contents.clear()

    def new_tag(
        self,
        name: str,
        namespace: Optional[str] = None,
        nsprefix: Optional[str] = None,
        attrs: Optional[dict] = None,
        **kwargs
    ) -> Tag:
        """Create a new Tag object."""
        attrs = attrs or {}
        attrs.update(kwargs)
        return Tag(name=name, attrs=attrs)

    def new_string(self, s: str, parent: Optional[Tag] = None) -> NavigableString:
        """Create a new NavigableString object."""
        ns = NavigableString(s)
        if parent:
            ns.parent = parent
        return ns

    def encode(
        self,
        encoding: str = 'utf-8',
        indent_level: Optional[int] = None,
        formatter: str = 'minimal',
        errors: str = 'xmlcharrefreplace'
    ) -> bytes:
        """Encode the soup as bytes."""
        return self.decode(formatter=formatter).encode(encoding, errors=errors)

    def decode(self, indent_level: int = 0, formatter: str = 'minimal') -> str:
        """Render the soup as a string."""
        result = []
        for child in self.contents:
            if isinstance(child, Tag):
                result.append(child.decode(indent_level, formatter))
            else:
                result.append(str(child))
        return ''.join(result)

    def __repr__(self) -> str:
        return self.decode()

    def __str__(self) -> str:
        return self.decode()

    # Convenience properties for common elements
    @property
    def title(self) -> Optional[Tag]:
        """Get the <title> tag."""
        return self.find('title')

    @property
    def head(self) -> Optional[Tag]:
        """Get the <head> tag."""
        return self.find('head')

    @property
    def body(self) -> Optional[Tag]:
        """Get the <body> tag."""
        return self.find('body')

    @property
    def html(self) -> Optional[Tag]:
        """Get the <html> tag."""
        return self.find('html')

    @property
    def a(self) -> Optional[Tag]:
        """Get the first <a> tag."""
        return self.find('a')

    @property
    def p(self) -> Optional[Tag]:
        """Get the first <p> tag."""
        return self.find('p')

    @property
    def div(self) -> Optional[Tag]:
        """Get the first <div> tag."""
        return self.find('div')

    @property
    def span(self) -> Optional[Tag]:
        """Get the first <span> tag."""
        return self.find('span')


class SoupStrainer:
    """
    Filter for limiting what parts of the document to parse.
    """

    def __init__(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[dict] = None,
        string: Optional[Union[str, re.Pattern]] = None,
        **kwargs
    ):
        self.name = name
        self.attrs = attrs or {}
        self.attrs.update(kwargs)
        self.string = string

    def search_tag(self, name: str = None, attrs: dict = None) -> bool:
        """Check if a tag matches this strainer."""
        # Check name
        if self.name is not None:
            if isinstance(self.name, str):
                if name != self.name:
                    return False
            elif isinstance(self.name, list):
                if name not in self.name:
                    return False
            elif isinstance(self.name, re.Pattern):
                if not self.name.search(name):
                    return False

        # Check attrs
        if self.attrs:
            attrs = attrs or {}
            for key, value in self.attrs.items():
                if key not in attrs:
                    return False
                if value is not True and attrs[key] != value:
                    return False

        return True


class ResultSet(list):
    """
    A list subclass that stores the source of results.
    """

    def __init__(self, source, result=()):
        super().__init__(result)
        self.source = source


# Aliases for compatibility
BeautifulStoneSoup = BeautifulSoup  # Legacy alias
