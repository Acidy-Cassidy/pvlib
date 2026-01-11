"""
mybeautifulsoup.parser - HTML/XML parsing logic

Uses Python's built-in html.parser for HTML parsing.
"""

from html.parser import HTMLParser
from html.entities import html5
from typing import Optional, List, Tuple, Any
import re

from .element import Tag, NavigableString, Comment


class TreeBuilder:
    """Base class for tree builders."""

    NAME = 'base'
    FEATURES = []

    def __init__(self):
        self.soup = None
        self.root = None

    def reset(self):
        """Reset the builder state."""
        self.root = None

    def initialize_soup(self, soup):
        """Initialize with a BeautifulSoup instance."""
        self.soup = soup

    def feed(self, markup: str):
        """Parse markup and build the tree."""
        raise NotImplementedError


class HTMLTreeBuilder(TreeBuilder, HTMLParser):
    """Tree builder using Python's html.parser."""

    NAME = 'html.parser'
    FEATURES = ['html.parser', 'html']

    def __init__(self):
        TreeBuilder.__init__(self)
        HTMLParser.__init__(self, convert_charrefs=False)
        self._tag_stack: List[Tag] = []
        self._current_tag: Optional[Tag] = None

    def reset(self):
        """Reset the parser state."""
        TreeBuilder.reset(self)
        HTMLParser.reset(self)
        self._tag_stack = []
        self._current_tag = None

    def feed(self, markup: str) -> Tag:
        """Parse HTML markup and return the root tag."""
        self.reset()

        # Create root document tag
        self.root = Tag(name='[document]')
        self._current_tag = self.root
        self._tag_stack = [self.root]

        # Parse the markup
        try:
            HTMLParser.feed(self, markup)
        except Exception:
            pass  # Be lenient with malformed HTML

        # Close any unclosed tags
        while len(self._tag_stack) > 1:
            self._tag_stack.pop()

        return self.root

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle an opening tag."""
        # Convert attrs to dict, handling multiple class values
        attrs_dict = {}
        for key, value in attrs:
            if key == 'class' and value:
                # Split class into list
                attrs_dict[key] = value.split()
            else:
                attrs_dict[key] = value if value is not None else True

        new_tag = Tag(name=tag, attrs=attrs_dict, parent=self._current_tag)

        # Add to parent's contents
        self._append_to_current(new_tag)

        # Handle self-closing tags
        if tag.lower() in Tag.SELF_CLOSING_TAGS:
            return

        # Push to stack for non-self-closing tags
        self._tag_stack.append(new_tag)
        self._current_tag = new_tag

    def handle_endtag(self, tag: str):
        """Handle a closing tag."""
        tag = tag.lower()

        # Find matching opening tag in stack
        for i in range(len(self._tag_stack) - 1, 0, -1):
            if self._tag_stack[i].name == tag:
                # Pop tags up to and including the matching one
                self._tag_stack = self._tag_stack[:i]
                self._current_tag = self._tag_stack[-1] if self._tag_stack else self.root
                return

        # No matching tag found - ignore

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle a self-closing tag like <br/>."""
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str):
        """Handle text data."""
        if data:
            text = NavigableString(data)
            self._append_to_current(text)

    def handle_comment(self, data: str):
        """Handle HTML comments."""
        comment = Comment(data)
        self._append_to_current(comment)

    def handle_entityref(self, name: str):
        """Handle named entities like &nbsp;."""
        char = html5.get(name + ';', f'&{name};')
        text = NavigableString(char)
        self._append_to_current(text)

    def handle_charref(self, name: str):
        """Handle numeric character references like &#65;."""
        try:
            if name.startswith(('x', 'X')):
                char = chr(int(name[1:], 16))
            else:
                char = chr(int(name))
        except (ValueError, OverflowError):
            char = f'&#{name};'

        text = NavigableString(char)
        self._append_to_current(text)

    def handle_decl(self, decl: str):
        """Handle doctype declarations."""
        # Store doctype but don't add to tree as a visible element
        pass

    def handle_pi(self, data: str):
        """Handle processing instructions like <?xml ...?>."""
        pass

    def _append_to_current(self, element):
        """Append an element to the current tag."""
        if self._current_tag is not None:
            self._current_tag.append(element)


class LXMLTreeBuilder(TreeBuilder):
    """
    Tree builder using lxml (placeholder).
    Falls back to html.parser if lxml is not available.
    """

    NAME = 'lxml'
    FEATURES = ['lxml', 'html']

    def __init__(self):
        super().__init__()
        self._html_builder = HTMLTreeBuilder()

    def reset(self):
        super().reset()
        self._html_builder.reset()

    def feed(self, markup: str) -> Tag:
        """Parse using lxml or fallback to html.parser."""
        # For now, just use html.parser as fallback
        return self._html_builder.feed(markup)


class XMLTreeBuilder(TreeBuilder):
    """Tree builder for XML content."""

    NAME = 'xml'
    FEATURES = ['xml']

    def __init__(self):
        super().__init__()
        self._html_builder = HTMLTreeBuilder()

    def reset(self):
        super().reset()
        self._html_builder.reset()

    def feed(self, markup: str) -> Tag:
        """Parse XML markup."""
        # Use html.parser with some XML adjustments
        return self._html_builder.feed(markup)


# Registry of available parsers
PARSERS = {
    'html.parser': HTMLTreeBuilder,
    'html': HTMLTreeBuilder,
    'lxml': LXMLTreeBuilder,
    'lxml-xml': XMLTreeBuilder,
    'xml': XMLTreeBuilder,
}


def get_tree_builder(features=None):
    """Get the best available tree builder for the given features."""
    if features is None:
        features = ['html.parser']

    if isinstance(features, str):
        features = [features]

    for feature in features:
        if feature in PARSERS:
            return PARSERS[feature]()

    # Default to html.parser
    return HTMLTreeBuilder()
