"""
RSS/Atom namespace definitions.
"""

# Common namespaces used in feeds
NAMESPACES = {
    # Atom
    "atom": "http://www.w3.org/2005/Atom",
    "atom03": "http://purl.org/atom/ns#",

    # RSS 1.0 / RDF
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss10": "http://purl.org/rss/1.0/",
    "rss09": "http://my.netscape.com/rdf/simple/0.9/",

    # Dublin Core
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",

    # Content
    "content": "http://purl.org/rss/1.0/modules/content/",

    # Syndication
    "sy": "http://purl.org/rss/1.0/modules/syndication/",

    # Media
    "media": "http://search.yahoo.com/mrss/",

    # iTunes
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",

    # XML
    "xml": "http://www.w3.org/XML/1998/namespace",
}

# Feed version detection patterns
VERSION_PATTERNS = {
    "rss20": [
        ("rss", {"version": "2.0"}),
        ("rss", {"version": "2"}),
    ],
    "rss10": [
        ("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF", {}),
    ],
    "rss091": [
        ("rss", {"version": "0.91"}),
    ],
    "rss092": [
        ("rss", {"version": "0.92"}),
    ],
    "atom10": [
        ("{http://www.w3.org/2005/Atom}feed", {}),
    ],
    "atom03": [
        ("{http://purl.org/atom/ns#}feed", {}),
    ],
}


def detect_feed_version(root_tag, root_attribs):
    """
    Detect feed version from root element.

    Args:
        root_tag: Root element tag name
        root_attribs: Root element attributes

    Returns:
        Feed version string (rss20, atom10, etc.) or empty string
    """
    # Check for Atom first (namespaced)
    if "atom" in root_tag.lower() or "{http://www.w3.org/2005/Atom}" in root_tag:
        return "atom10"
    if "{http://purl.org/atom/ns#}" in root_tag:
        return "atom03"

    # Check for RDF/RSS 1.0
    if "rdf" in root_tag.lower() or "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}" in root_tag:
        return "rss10"

    # Check for RSS 2.0/0.9x
    if root_tag.lower() == "rss":
        version = root_attribs.get("version", "2.0")
        if version.startswith("2"):
            return "rss20"
        elif version.startswith("0.91"):
            return "rss091"
        elif version.startswith("0.92"):
            return "rss092"
        elif version.startswith("0.9"):
            return "rss090"
        return "rss20"  # Default to RSS 2.0

    return ""


def get_namespace_prefix(uri):
    """
    Get the prefix for a namespace URI.

    Args:
        uri: Namespace URI

    Returns:
        Prefix string or None
    """
    for prefix, ns_uri in NAMESPACES.items():
        if ns_uri == uri:
            return prefix
    return None


def strip_namespace(tag):
    """
    Strip namespace from element tag.

    Args:
        tag: Tag with optional namespace (e.g., "{http://...}tagname")

    Returns:
        Tag name without namespace
    """
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def get_namespace(tag):
    """
    Extract namespace from element tag.

    Args:
        tag: Tag with optional namespace

    Returns:
        Namespace URI or empty string
    """
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return ""
