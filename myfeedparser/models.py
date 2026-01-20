"""
Data models for feedparser.
"""


class FeedParserDict(dict):
    """
    A dict-like object that allows attribute access.
    Used for feed, entries, and result objects.
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def get(self, key, default=None):
        """Get item with default."""
        try:
            return self[key]
        except KeyError:
            return default


def make_detail(value, type_="text/plain", language=None, base=None):
    """
    Create a detail dict for title_detail, summary_detail, etc.

    Args:
        value: The text content
        type_: Content type (text/plain, text/html, application/xhtml+xml)
        language: Language code
        base: Base URL

    Returns:
        FeedParserDict with detail fields
    """
    detail = FeedParserDict()
    detail["value"] = value
    detail["type"] = type_
    if language:
        detail["language"] = language
    if base:
        detail["base"] = base
    return detail


def make_link(href, rel="alternate", type_=None, title=None, length=None):
    """
    Create a link dict.

    Args:
        href: Link URL
        rel: Relationship (alternate, self, enclosure, etc.)
        type_: MIME type
        title: Link title
        length: Content length

    Returns:
        FeedParserDict with link fields
    """
    link = FeedParserDict()
    link["href"] = href
    link["rel"] = rel
    if type_:
        link["type"] = type_
    if title:
        link["title"] = title
    if length:
        link["length"] = length
    return link


def make_person(name=None, email=None, href=None):
    """
    Create a person dict for author, contributor.

    Args:
        name: Person's name
        email: Email address
        href: Homepage URL

    Returns:
        FeedParserDict with person fields
    """
    person = FeedParserDict()
    if name:
        person["name"] = name
    if email:
        person["email"] = email
    if href:
        person["href"] = href
    return person


def make_tag(term, scheme=None, label=None):
    """
    Create a tag/category dict.

    Args:
        term: Category term
        scheme: Category scheme/domain
        label: Human-readable label

    Returns:
        FeedParserDict with tag fields
    """
    tag = FeedParserDict()
    tag["term"] = term
    if scheme:
        tag["scheme"] = scheme
    if label:
        tag["label"] = label
    else:
        tag["label"] = term
    return tag


def make_enclosure(href, type_=None, length=None):
    """
    Create an enclosure dict for media attachments.

    Args:
        href: Media URL
        type_: MIME type
        length: File size in bytes

    Returns:
        FeedParserDict with enclosure fields
    """
    enc = FeedParserDict()
    enc["href"] = href
    if type_:
        enc["type"] = type_
    if length:
        enc["length"] = length
    return enc


def make_content(value, type_="text/html", language=None, base=None):
    """
    Create a content dict for entry content.

    Args:
        value: Content HTML/text
        type_: Content type
        language: Language code
        base: Base URL

    Returns:
        FeedParserDict with content fields
    """
    content = FeedParserDict()
    content["value"] = value
    content["type"] = type_
    if language:
        content["language"] = language
    if base:
        content["base"] = base
    return content
