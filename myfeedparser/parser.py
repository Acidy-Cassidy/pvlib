"""
Main feed parsing logic.
"""

import io
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .models import (
    FeedParserDict,
    make_detail,
    make_link,
    make_person,
    make_tag,
    make_enclosure,
    make_content,
)
from .dates import _parse_date
from .namespaces import detect_feed_version, strip_namespace, NAMESPACES
from .sanitizer import sanitize_html, strip_tags, detect_content_type


class FeedParser:
    """
    Feed parser class that handles RSS and Atom feeds.
    """

    def __init__(self):
        self.result = FeedParserDict()
        self.result.feed = FeedParserDict()
        self.result.entries = []
        self.result.bozo = 0
        self.result.bozo_exception = None
        self.result.headers = FeedParserDict()
        self.result.href = ""
        self.result.status = 0
        self.result.encoding = "utf-8"
        self.result.version = ""
        self.result.namespaces = {}

    def parse(self, source, etag=None, modified=None, agent=None,
              handlers=None, request_headers=None):
        """
        Parse a feed from various sources.

        Args:
            source: URL, file path, file object, or string
            etag: HTTP ETag for conditional GET
            modified: HTTP Last-Modified for conditional GET
            agent: User-Agent string
            handlers: Custom URL handlers (ignored)
            request_headers: Additional HTTP headers

        Returns:
            FeedParserDict result
        """
        data = None

        # Determine source type and get data
        if hasattr(source, "read"):
            # File-like object
            data = source.read()
            if isinstance(data, str):
                data = data.encode("utf-8")
        elif source.startswith(("http://", "https://")):
            # URL
            data = self._fetch_url(source, etag, modified, agent, request_headers)
        elif source.startswith("<?xml") or source.startswith("<rss") or source.startswith("<feed"):
            # XML string
            if isinstance(source, str):
                data = source.encode("utf-8")
            else:
                data = source
        else:
            # Try as file path
            try:
                with open(source, "rb") as f:
                    data = f.read()
            except (IOError, OSError):
                # Treat as XML string
                if isinstance(source, str):
                    data = source.encode("utf-8")
                else:
                    data = source

        if data is None:
            return self.result

        # Parse XML
        self._parse_xml(data)
        return self.result

    def _fetch_url(self, url, etag=None, modified=None, agent=None, request_headers=None):
        """
        Fetch feed content from URL.
        """
        self.result.href = url
        headers = {}

        if agent:
            headers["User-Agent"] = agent
        else:
            headers["User-Agent"] = "myfeedparser/0.1.0"

        if etag:
            headers["If-None-Match"] = etag
        if modified:
            headers["If-Modified-Since"] = modified
        if request_headers:
            headers.update(request_headers)

        request = Request(url, headers=headers)

        try:
            response = urlopen(request, timeout=30)
            self.result.status = response.status

            # Store headers
            for key, value in response.headers.items():
                self.result.headers[key.lower()] = value

            # Check for redirects
            self.result.href = response.url

            # Get encoding
            content_type = response.headers.get("Content-Type", "")
            if "charset=" in content_type:
                self.result.encoding = content_type.split("charset=")[1].split(";")[0].strip()

            return response.read()

        except HTTPError as e:
            self.result.status = e.code
            self.result.bozo = 1
            self.result.bozo_exception = e
            return None
        except URLError as e:
            self.result.bozo = 1
            self.result.bozo_exception = e
            return None

    def _parse_xml(self, data):
        """
        Parse XML data into feed structure.
        """
        try:
            # Handle encoding declaration
            if isinstance(data, bytes):
                # Try to detect encoding from XML declaration
                if data.startswith(b"<?xml"):
                    decl_end = data.find(b"?>")
                    if decl_end > 0:
                        decl = data[:decl_end].decode("ascii", errors="ignore")
                        if 'encoding="' in decl:
                            enc = decl.split('encoding="')[1].split('"')[0]
                            self.result.encoding = enc
                        elif "encoding='" in decl:
                            enc = decl.split("encoding='")[1].split("'")[0]
                            self.result.encoding = enc

            root = ET.fromstring(data)

            # Detect version
            self.result.version = detect_feed_version(root.tag, root.attrib)

            # Extract namespaces
            self._extract_namespaces(root)

            # Parse based on feed type
            if self.result.version.startswith("atom"):
                self._parse_atom(root)
            else:
                self._parse_rss(root)

        except ET.ParseError as e:
            self.result.bozo = 1
            self.result.bozo_exception = e

    def _extract_namespaces(self, root):
        """
        Extract namespace mappings from document.
        """
        # ElementTree doesn't expose namespace declarations directly
        # We'll use the registered namespaces
        for prefix, uri in NAMESPACES.items():
            self.result.namespaces[prefix] = uri

    def _parse_rss(self, root):
        """
        Parse RSS 0.9x, 1.0, or 2.0 feed.
        """
        # Find channel element
        channel = root.find("channel")
        if channel is None:
            # RSS 1.0 uses namespaced channel
            channel = root.find("{http://purl.org/rss/1.0/}channel")
        if channel is None:
            channel = root

        # Parse feed metadata
        self._parse_rss_channel(channel)

        # Parse items
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://purl.org/rss/1.0/}item")

        for item in items:
            entry = self._parse_rss_item(item)
            self.result.entries.append(entry)

    def _parse_rss_channel(self, channel):
        """
        Parse RSS channel metadata into feed dict.
        """
        feed = self.result.feed

        # Title
        title = self._get_text(channel, "title")
        if title:
            feed.title = title
            feed.title_detail = make_detail(title)

        # Link
        link = self._get_text(channel, "link")
        if link:
            feed.link = link
            feed.links = [make_link(link)]

        # Description/subtitle
        desc = self._get_text(channel, "description")
        if desc:
            feed.subtitle = desc
            feed.subtitle_detail = make_detail(desc, detect_content_type(desc))

        # Language
        lang = self._get_text(channel, "language")
        if lang:
            feed.language = lang

        # Published/updated dates
        pub_date = self._get_text(channel, "pubDate") or self._get_text(channel, "lastBuildDate")
        if pub_date:
            feed.updated = pub_date
            feed.updated_parsed = _parse_date(pub_date)

        # Image
        image = channel.find("image")
        if image is not None:
            feed.image = FeedParserDict()
            feed.image.url = self._get_text(image, "url")
            feed.image.title = self._get_text(image, "title")
            feed.image.link = self._get_text(image, "link")

        # Generator
        generator = self._get_text(channel, "generator")
        if generator:
            feed.generator = generator
            feed.generator_detail = FeedParserDict({"name": generator})

        # Copyright/rights
        copyright_ = self._get_text(channel, "copyright")
        if copyright_:
            feed.rights = copyright_
            feed.rights_detail = make_detail(copyright_)

        # Managing editor as author
        editor = self._get_text(channel, "managingEditor")
        if editor:
            feed.author = editor
            feed.author_detail = make_person(name=editor)

        # Categories/tags
        categories = channel.findall("category")
        if categories:
            feed.tags = []
            for cat in categories:
                term = cat.text or ""
                domain = cat.get("domain")
                feed.tags.append(make_tag(term, scheme=domain))

    def _parse_rss_item(self, item):
        """
        Parse RSS item into entry dict.
        """
        entry = FeedParserDict()

        # Title
        title = self._get_text(item, "title")
        if title:
            entry.title = title
            entry.title_detail = make_detail(title)

        # Link
        link = self._get_text(item, "link")
        if link:
            entry.link = link
            entry.links = [make_link(link)]

        # Description/summary
        desc = self._get_text(item, "description")
        if desc:
            entry.summary = desc
            entry.summary_detail = make_detail(desc, detect_content_type(desc))

        # Content (content:encoded)
        content = self._get_text(item, "{http://purl.org/rss/1.0/modules/content/}encoded")
        if content:
            entry.content = [make_content(content)]

        # GUID/id
        guid = self._get_text(item, "guid")
        if guid:
            entry.id = guid
        elif link:
            entry.id = link

        # Published date
        pub_date = self._get_text(item, "pubDate")
        if pub_date:
            entry.published = pub_date
            entry.published_parsed = _parse_date(pub_date)
            entry.updated = pub_date
            entry.updated_parsed = _parse_date(pub_date)

        # Author
        author = self._get_text(item, "author")
        if not author:
            author = self._get_text(item, "{http://purl.org/dc/elements/1.1/}creator")
        if author:
            entry.author = author
            entry.author_detail = make_person(name=author)

        # Categories/tags
        categories = item.findall("category")
        if categories:
            entry.tags = []
            for cat in categories:
                term = cat.text or ""
                domain = cat.get("domain")
                entry.tags.append(make_tag(term, scheme=domain))

        # Enclosures
        enclosure = item.find("enclosure")
        if enclosure is not None:
            enc = make_enclosure(
                enclosure.get("url", ""),
                enclosure.get("type"),
                enclosure.get("length")
            )
            entry.enclosures = [enc]

        # Comments
        comments = self._get_text(item, "comments")
        if comments:
            entry.comments = comments

        return entry

    def _parse_atom(self, root):
        """
        Parse Atom 0.3 or 1.0 feed.
        """
        # Parse feed metadata
        self._parse_atom_feed(root)

        # Parse entries
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        if not entries:
            entries = root.findall("{http://purl.org/atom/ns#}entry")
        if not entries:
            entries = root.findall("entry")

        for entry_elem in entries:
            entry = self._parse_atom_entry(entry_elem)
            self.result.entries.append(entry)

    def _parse_atom_feed(self, root):
        """
        Parse Atom feed metadata.
        """
        feed = self.result.feed
        ns = "{http://www.w3.org/2005/Atom}"

        # Try both namespaced and non-namespaced
        def find_text(tag):
            elem = root.find(f"{ns}{tag}")
            if elem is None:
                elem = root.find(tag)
            if elem is not None and elem.text:
                return elem.text.strip()
            return None

        def find_elem(tag):
            elem = root.find(f"{ns}{tag}")
            if elem is None:
                elem = root.find(tag)
            return elem

        # Title
        title = find_text("title")
        if title:
            feed.title = title
            title_elem = find_elem("title")
            type_ = title_elem.get("type", "text") if title_elem is not None else "text"
            feed.title_detail = make_detail(title, f"text/{type_}" if "/" not in type_ else type_)

        # Links
        links = root.findall(f"{ns}link") or root.findall("link")
        feed.links = []
        for link in links:
            rel = link.get("rel", "alternate")
            href = link.get("href", "")
            type_ = link.get("type")
            title = link.get("title")
            feed.links.append(make_link(href, rel, type_, title))
            if rel == "alternate" and href:
                feed.link = href

        # Subtitle
        subtitle = find_text("subtitle") or find_text("tagline")
        if subtitle:
            feed.subtitle = subtitle
            feed.subtitle_detail = make_detail(subtitle)

        # ID
        id_ = find_text("id")
        if id_:
            feed.id = id_

        # Updated
        updated = find_text("updated") or find_text("modified")
        if updated:
            feed.updated = updated
            feed.updated_parsed = _parse_date(updated)

        # Author
        author_elem = find_elem("author")
        if author_elem is not None:
            name = self._get_text(author_elem, f"{ns}name") or self._get_text(author_elem, "name")
            email = self._get_text(author_elem, f"{ns}email") or self._get_text(author_elem, "email")
            uri = self._get_text(author_elem, f"{ns}uri") or self._get_text(author_elem, "uri")
            feed.author = name or email or ""
            feed.author_detail = make_person(name, email, uri)

        # Generator
        generator_elem = find_elem("generator")
        if generator_elem is not None and generator_elem.text:
            feed.generator = generator_elem.text.strip()
            feed.generator_detail = FeedParserDict({
                "name": generator_elem.text.strip(),
                "href": generator_elem.get("uri"),
                "version": generator_elem.get("version"),
            })

        # Rights
        rights = find_text("rights")
        if rights:
            feed.rights = rights
            feed.rights_detail = make_detail(rights)

        # Categories
        categories = root.findall(f"{ns}category") or root.findall("category")
        if categories:
            feed.tags = []
            for cat in categories:
                term = cat.get("term", "")
                scheme = cat.get("scheme")
                label = cat.get("label")
                feed.tags.append(make_tag(term, scheme, label))

    def _parse_atom_entry(self, entry_elem):
        """
        Parse Atom entry into entry dict.
        """
        entry = FeedParserDict()
        ns = "{http://www.w3.org/2005/Atom}"

        def find_text(tag):
            elem = entry_elem.find(f"{ns}{tag}")
            if elem is None:
                elem = entry_elem.find(tag)
            if elem is not None and elem.text:
                return elem.text.strip()
            return None

        def find_elem(tag):
            elem = entry_elem.find(f"{ns}{tag}")
            if elem is None:
                elem = entry_elem.find(tag)
            return elem

        # Title
        title = find_text("title")
        if title:
            entry.title = title
            title_elem = find_elem("title")
            type_ = title_elem.get("type", "text") if title_elem is not None else "text"
            entry.title_detail = make_detail(title, f"text/{type_}" if "/" not in type_ else type_)

        # Links
        links = entry_elem.findall(f"{ns}link") or entry_elem.findall("link")
        entry.links = []
        entry.enclosures = []
        for link in links:
            rel = link.get("rel", "alternate")
            href = link.get("href", "")
            type_ = link.get("type")
            title = link.get("title")
            length = link.get("length")

            if rel == "enclosure":
                entry.enclosures.append(make_enclosure(href, type_, length))
            else:
                entry.links.append(make_link(href, rel, type_, title))
                if rel == "alternate" and href:
                    entry.link = href

        # Summary
        summary = find_text("summary")
        if summary:
            entry.summary = summary
            summary_elem = find_elem("summary")
            type_ = summary_elem.get("type", "text") if summary_elem is not None else "text"
            entry.summary_detail = make_detail(summary, f"text/{type_}" if "/" not in type_ else type_)

        # Content
        content_elem = find_elem("content")
        if content_elem is not None:
            content_text = content_elem.text or ""
            type_ = content_elem.get("type", "text")
            entry.content = [make_content(content_text, f"text/{type_}" if "/" not in type_ else type_)]

        # ID
        id_ = find_text("id")
        if id_:
            entry.id = id_

        # Published
        published = find_text("published") or find_text("issued")
        if published:
            entry.published = published
            entry.published_parsed = _parse_date(published)

        # Updated
        updated = find_text("updated") or find_text("modified")
        if updated:
            entry.updated = updated
            entry.updated_parsed = _parse_date(updated)
        elif published:
            entry.updated = published
            entry.updated_parsed = _parse_date(published)

        # Author
        author_elem = find_elem("author")
        if author_elem is not None:
            name = self._get_text(author_elem, f"{ns}name") or self._get_text(author_elem, "name")
            email = self._get_text(author_elem, f"{ns}email") or self._get_text(author_elem, "email")
            uri = self._get_text(author_elem, f"{ns}uri") or self._get_text(author_elem, "uri")
            entry.author = name or email or ""
            entry.author_detail = make_person(name, email, uri)

        # Contributors
        contributors = entry_elem.findall(f"{ns}contributor") or entry_elem.findall("contributor")
        if contributors:
            entry.contributors = []
            for contrib in contributors:
                name = self._get_text(contrib, f"{ns}name") or self._get_text(contrib, "name")
                email = self._get_text(contrib, f"{ns}email") or self._get_text(contrib, "email")
                uri = self._get_text(contrib, f"{ns}uri") or self._get_text(contrib, "uri")
                entry.contributors.append(make_person(name, email, uri))

        # Categories
        categories = entry_elem.findall(f"{ns}category") or entry_elem.findall("category")
        if categories:
            entry.tags = []
            for cat in categories:
                term = cat.get("term", "")
                scheme = cat.get("scheme")
                label = cat.get("label")
                entry.tags.append(make_tag(term, scheme, label))

        return entry

    def _get_text(self, elem, tag):
        """
        Get text content of a child element.
        """
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None


def parse(url_file_stream_or_string, etag=None, modified=None,
          agent=None, handlers=None, request_headers=None):
    """
    Parse a feed from various sources.

    Args:
        url_file_stream_or_string: URL, file path, file object, or XML string
        etag: HTTP ETag for conditional GET
        modified: HTTP Last-Modified for conditional GET
        agent: User-Agent string
        handlers: Custom URL handlers (ignored in this implementation)
        request_headers: Additional HTTP headers dict

    Returns:
        FeedParserDict with parsed feed data
    """
    parser = FeedParser()
    return parser.parse(
        url_file_stream_or_string,
        etag=etag,
        modified=modified,
        agent=agent,
        handlers=handlers,
        request_headers=request_headers
    )
