"""
HTML/content sanitization utilities for feedparser.
"""

import re
import html
from html.parser import HTMLParser

# Safe HTML tags that are allowed
SAFE_TAGS = frozenset([
    "a", "abbr", "acronym", "address", "b", "big", "blockquote", "br",
    "center", "cite", "code", "col", "colgroup", "dd", "del", "dfn",
    "dir", "div", "dl", "dt", "em", "font", "h1", "h2", "h3", "h4",
    "h5", "h6", "hr", "i", "img", "ins", "kbd", "li", "ol", "p", "pre",
    "q", "s", "samp", "small", "span", "strike", "strong", "sub", "sup",
    "table", "tbody", "td", "tfoot", "th", "thead", "tr", "tt", "u", "ul", "var"
])

# Safe attributes for allowed tags
SAFE_ATTRS = frozenset([
    "abbr", "accept", "accept-charset", "accesskey", "align", "alt",
    "axis", "border", "cellpadding", "cellspacing", "char", "charoff",
    "charset", "cite", "class", "clear", "cols", "colspan", "color",
    "compact", "coords", "datetime", "dir", "disabled", "enctype",
    "for", "frame", "headers", "height", "href", "hreflang", "hspace",
    "id", "ismap", "label", "lang", "longdesc", "maxlength", "media",
    "method", "multiple", "name", "nohref", "noshade", "nowrap",
    "prompt", "readonly", "rel", "rev", "rows", "rowspan", "rules",
    "scope", "selected", "shape", "size", "span", "src", "start",
    "summary", "tabindex", "target", "title", "type", "usemap",
    "valign", "value", "vspace", "width", "xml:lang"
])

# Pattern for stripping tags
STRIP_TAGS_RE = re.compile(r"<[^>]+>")


class HTMLSanitizer(HTMLParser):
    """
    HTML parser that strips unsafe content.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.result = []
        self.in_unsafe = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in SAFE_TAGS:
            safe_attrs = []
            for name, value in attrs:
                if name.lower() in SAFE_ATTRS:
                    if value is None:
                        safe_attrs.append(name)
                    else:
                        # Escape attribute value
                        value = html.escape(value, quote=True)
                        safe_attrs.append(f'{name}="{value}"')
            attr_str = " ".join(safe_attrs)
            if attr_str:
                self.result.append(f"<{tag} {attr_str}>")
            else:
                self.result.append(f"<{tag}>")
        else:
            self.in_unsafe += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in SAFE_TAGS:
            self.result.append(f"</{tag}>")
        elif self.in_unsafe > 0:
            self.in_unsafe -= 1

    def handle_data(self, data):
        if self.in_unsafe == 0:
            self.result.append(html.escape(data))

    def handle_entityref(self, name):
        if self.in_unsafe == 0:
            self.result.append(f"&{name};")

    def handle_charref(self, name):
        if self.in_unsafe == 0:
            self.result.append(f"&#{name};")

    def get_result(self):
        return "".join(self.result)


def sanitize_html(html_content):
    """
    Sanitize HTML content, removing unsafe tags and attributes.

    Args:
        html_content: HTML string to sanitize

    Returns:
        Sanitized HTML string
    """
    if not html_content:
        return ""

    try:
        sanitizer = HTMLSanitizer()
        sanitizer.feed(html_content)
        return sanitizer.get_result()
    except Exception:
        # If parsing fails, strip all tags
        return strip_tags(html_content)


def strip_tags(html_content):
    """
    Strip all HTML tags from content.

    Args:
        html_content: HTML string

    Returns:
        Plain text with all tags removed
    """
    if not html_content:
        return ""

    # Unescape HTML entities first
    text = html.unescape(html_content)
    # Remove all tags
    text = STRIP_TAGS_RE.sub("", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def detect_content_type(content):
    """
    Detect if content is HTML or plain text.

    Args:
        content: Content string to check

    Returns:
        "text/html" or "text/plain"
    """
    if not content:
        return "text/plain"

    # Check for common HTML indicators
    html_indicators = ["<p", "<br", "<div", "<span", "<a ", "<img", "&amp;", "&lt;", "&gt;"]
    content_lower = content.lower()

    for indicator in html_indicators:
        if indicator in content_lower:
            return "text/html"

    return "text/plain"
