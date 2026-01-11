"""
mybeautifulsoup.element - Core element classes for BeautifulSoup

Provides Tag, NavigableString, and Comment classes for representing HTML/XML elements.
"""

import re
from typing import Optional, List, Dict, Any, Iterator, Union, Callable


class NavigableString(str):
    """
    A string that knows its location in the parse tree.
    """

    def __new__(cls, value: str = ''):
        instance = super().__new__(cls, value)
        instance.parent = None
        instance.previous_sibling = None
        instance.next_sibling = None
        instance.previous_element = None
        instance.next_element = None
        return instance

    @property
    def name(self) -> None:
        return None

    @property
    def string(self) -> str:
        return str(self)

    def get_text(self, separator: str = '', strip: bool = False) -> str:
        text = str(self)
        if strip:
            text = text.strip()
        return text

    def __repr__(self) -> str:
        return f"'{str(self)}'"


class Comment(NavigableString):
    """
    An HTML/XML comment.
    """

    PREFIX = '<!--'
    SUFFIX = '-->'

    def __repr__(self) -> str:
        return f"Comment('{str(self)}')"

    def output_ready(self) -> str:
        return f'{self.PREFIX}{str(self)}{self.SUFFIX}'


class Tag:
    """
    Represents an HTML/XML tag with attributes and children.
    """

    SELF_CLOSING_TAGS = frozenset([
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'
    ])

    def __init__(
        self,
        name: str = '',
        attrs: Optional[Dict[str, Any]] = None,
        parent: Optional['Tag'] = None,
        parser: Optional[Any] = None
    ):
        self.name = name.lower() if name else ''
        self.attrs = attrs or {}
        self.parent = parent
        self.parser = parser
        self.contents: List[Union['Tag', NavigableString]] = []

        # Navigation links
        self.previous_sibling: Optional[Union['Tag', NavigableString]] = None
        self.next_sibling: Optional[Union['Tag', NavigableString]] = None
        self.previous_element: Optional[Union['Tag', NavigableString]] = None
        self.next_element: Optional[Union['Tag', NavigableString]] = None

    def __repr__(self) -> str:
        return f"<{self.name}>"

    def __str__(self) -> str:
        return self.decode()

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(self.contents)

    def __iter__(self) -> Iterator[Union['Tag', NavigableString]]:
        return iter(self.contents)

    def __getitem__(self, key: str) -> Any:
        """Get attribute value like a dictionary."""
        return self.attrs.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set attribute value like a dictionary."""
        self.attrs[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if attribute exists."""
        return key in self.attrs

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Tag):
            return False
        return (self.name == other.name and
                self.attrs == other.attrs and
                self.contents == other.contents)

    def __hash__(self) -> int:
        return id(self)

    def __getattr__(self, name: str) -> Optional['Tag']:
        """Allow accessing first child tag by name (e.g., tag.div, tag.p)."""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        return self.find(name)

    @property
    def string(self) -> Optional[str]:
        """
        Get the single string within this tag, if there is one.
        Returns None if there are multiple strings or nested tags.
        """
        strings = list(self.strings)
        if len(strings) == 1:
            return strings[0]
        return None

    @property
    def strings(self) -> Iterator[str]:
        """Yield all strings within this tag."""
        for child in self.descendants:
            if isinstance(child, NavigableString) and not isinstance(child, Comment):
                if str(child).strip():
                    yield str(child)

    @property
    def stripped_strings(self) -> Iterator[str]:
        """Yield all strings within this tag, with whitespace stripped."""
        for s in self.strings:
            stripped = s.strip()
            if stripped:
                yield stripped

    @property
    def text(self) -> str:
        """Get all text content concatenated."""
        return self.get_text()

    @property
    def children(self) -> Iterator[Union['Tag', NavigableString]]:
        """Iterate over direct children."""
        return iter(self.contents)

    @property
    def descendants(self) -> Iterator[Union['Tag', NavigableString]]:
        """Iterate over all descendants (recursive)."""
        for child in self.contents:
            yield child
            if isinstance(child, Tag):
                yield from child.descendants

    @property
    def parents(self) -> Iterator['Tag']:
        """Iterate over all parent tags."""
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent

    @property
    def next_siblings(self) -> Iterator[Union['Tag', NavigableString]]:
        """Iterate over next siblings."""
        sibling = self.next_sibling
        while sibling is not None:
            yield sibling
            sibling = sibling.next_sibling

    @property
    def previous_siblings(self) -> Iterator[Union['Tag', NavigableString]]:
        """Iterate over previous siblings."""
        sibling = self.previous_sibling
        while sibling is not None:
            yield sibling
            sibling = sibling.previous_sibling

    def get(self, key: str, default: Any = None) -> Any:
        """Get attribute value with default."""
        return self.attrs.get(key, default)

    def get_text(self, separator: str = '', strip: bool = False) -> str:
        """Get all text content, optionally with separator and stripping."""
        if strip:
            return separator.join(self.stripped_strings)
        return separator.join(self.strings)

    def has_attr(self, key: str) -> bool:
        """Check if this tag has a specific attribute."""
        return key in self.attrs

    def get_attribute_list(self, key: str) -> List[str]:
        """Get attribute value as a list (for class, etc.)."""
        value = self.attrs.get(key, [])
        if isinstance(value, list):
            return value
        return value.split() if value else []

    def append(self, child: Union['Tag', NavigableString, str]) -> None:
        """Append a child element."""
        if isinstance(child, str) and not isinstance(child, NavigableString):
            child = NavigableString(child)

        if self.contents:
            last_child = self.contents[-1]
            last_child.next_sibling = child
            child.previous_sibling = last_child

        child.parent = self
        self.contents.append(child)

    def insert(self, position: int, child: Union['Tag', NavigableString, str]) -> None:
        """Insert a child at a specific position."""
        if isinstance(child, str) and not isinstance(child, NavigableString):
            child = NavigableString(child)

        child.parent = self
        self.contents.insert(position, child)
        self._update_sibling_links()

    def extend(self, children: List[Union['Tag', NavigableString, str]]) -> None:
        """Append multiple children."""
        for child in children:
            self.append(child)

    def clear(self) -> None:
        """Remove all children."""
        for child in self.contents:
            child.parent = None
            child.previous_sibling = None
            child.next_sibling = None
        self.contents.clear()

    def extract(self) -> 'Tag':
        """Remove this element from the tree and return it."""
        if self.parent:
            self.parent.contents.remove(self)
            self.parent._update_sibling_links()

        self.parent = None
        if self.previous_sibling:
            self.previous_sibling.next_sibling = self.next_sibling
        if self.next_sibling:
            self.next_sibling.previous_sibling = self.previous_sibling
        self.previous_sibling = None
        self.next_sibling = None

        return self

    def decompose(self) -> None:
        """Remove this element from the tree and destroy it."""
        self.extract()
        self.contents.clear()

    def replace_with(self, replacement: Union['Tag', NavigableString, str]) -> 'Tag':
        """Replace this element with another."""
        if isinstance(replacement, str) and not isinstance(replacement, NavigableString):
            replacement = NavigableString(replacement)

        if self.parent:
            idx = self.parent.contents.index(self)
            self.parent.contents[idx] = replacement
            replacement.parent = self.parent
            replacement.previous_sibling = self.previous_sibling
            replacement.next_sibling = self.next_sibling

            if self.previous_sibling:
                self.previous_sibling.next_sibling = replacement
            if self.next_sibling:
                self.next_sibling.previous_sibling = replacement

        self.parent = None
        self.previous_sibling = None
        self.next_sibling = None

        return self

    def wrap(self, wrapper: 'Tag') -> 'Tag':
        """Wrap this element in another element."""
        self.replace_with(wrapper)
        wrapper.append(self)
        return wrapper

    def unwrap(self) -> 'Tag':
        """Replace this element with its contents."""
        if self.parent:
            idx = self.parent.contents.index(self)
            self.parent.contents[idx:idx+1] = self.contents
            for child in self.contents:
                child.parent = self.parent
            self.parent._update_sibling_links()

        self.parent = None
        self.contents = []
        return self

    def _update_sibling_links(self) -> None:
        """Update sibling links for all children."""
        for i, child in enumerate(self.contents):
            child.previous_sibling = self.contents[i-1] if i > 0 else None
            child.next_sibling = self.contents[i+1] if i < len(self.contents) - 1 else None

    def find(
        self,
        name: Optional[Union[str, List[str], re.Pattern, Callable]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        recursive: bool = True,
        string: Optional[Union[str, re.Pattern]] = None,
        **kwargs
    ) -> Optional['Tag']:
        """Find the first matching tag."""
        results = self.find_all(name, attrs, recursive, string, limit=1, **kwargs)
        return results[0] if results else None

    def find_all(
        self,
        name: Optional[Union[str, List[str], re.Pattern, Callable]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        recursive: bool = True,
        string: Optional[Union[str, re.Pattern]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List['Tag']:
        """Find all matching tags."""
        results = []
        attrs = attrs or {}
        attrs.update(kwargs)

        # Handle class_ argument
        if 'class_' in attrs:
            attrs['class'] = attrs.pop('class_')

        iterator = self.descendants if recursive else self.children

        for element in iterator:
            if not isinstance(element, Tag):
                continue

            if self._matches(element, name, attrs, string):
                results.append(element)
                if limit and len(results) >= limit:
                    break

        return results

    def find_parent(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional['Tag']:
        """Find the first matching parent."""
        attrs = attrs or {}
        attrs.update(kwargs)

        for parent in self.parents:
            if self._matches(parent, name, attrs):
                return parent
        return None

    def find_parents(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List['Tag']:
        """Find all matching parents."""
        results = []
        attrs = attrs or {}
        attrs.update(kwargs)

        for parent in self.parents:
            if self._matches(parent, name, attrs):
                results.append(parent)
                if limit and len(results) >= limit:
                    break
        return results

    def find_next_sibling(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional['Tag']:
        """Find the next matching sibling."""
        attrs = attrs or {}
        attrs.update(kwargs)

        for sibling in self.next_siblings:
            if isinstance(sibling, Tag) and self._matches(sibling, name, attrs):
                return sibling
        return None

    def find_next_siblings(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List['Tag']:
        """Find all next matching siblings."""
        results = []
        attrs = attrs or {}
        attrs.update(kwargs)

        for sibling in self.next_siblings:
            if isinstance(sibling, Tag) and self._matches(sibling, name, attrs):
                results.append(sibling)
                if limit and len(results) >= limit:
                    break
        return results

    def find_previous_sibling(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional['Tag']:
        """Find the previous matching sibling."""
        attrs = attrs or {}
        attrs.update(kwargs)

        for sibling in self.previous_siblings:
            if isinstance(sibling, Tag) and self._matches(sibling, name, attrs):
                return sibling
        return None

    def find_previous_siblings(
        self,
        name: Optional[Union[str, List[str], re.Pattern]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List['Tag']:
        """Find all previous matching siblings."""
        results = []
        attrs = attrs or {}
        attrs.update(kwargs)

        for sibling in self.previous_siblings:
            if isinstance(sibling, Tag) and self._matches(sibling, name, attrs):
                results.append(sibling)
                if limit and len(results) >= limit:
                    break
        return results

    def select(self, selector: str) -> List['Tag']:
        """Select elements using CSS selector syntax."""
        return self._css_select(selector)

    def select_one(self, selector: str) -> Optional['Tag']:
        """Select the first element matching CSS selector."""
        results = self.select(selector)
        return results[0] if results else None

    def _css_select(self, selector: str) -> List['Tag']:
        """Parse and apply CSS selector."""
        results = []

        # Split by comma for multiple selectors
        selectors = [s.strip() for s in selector.split(',')]

        for sel in selectors:
            results.extend(self._apply_single_selector(sel))

        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for tag in results:
            if id(tag) not in seen:
                seen.add(id(tag))
                unique_results.append(tag)

        return unique_results

    def _apply_single_selector(self, selector: str) -> List['Tag']:
        """Apply a single CSS selector."""
        parts = selector.split()

        if not parts:
            return []

        # Start with all descendants or the root
        current = list(self.descendants)
        current = [e for e in current if isinstance(e, Tag)]

        for part in parts:
            if part == '>':
                continue  # Handle in next iteration

            current = self._filter_by_selector_part(current, part)

        return current

    def _filter_by_selector_part(self, elements: List['Tag'], part: str) -> List['Tag']:
        """Filter elements by a single selector part."""
        results = []

        # Parse the selector part
        # Handle ID selector
        if '#' in part:
            tag_name, _, id_val = part.partition('#')
            if '.' in id_val:
                id_val, _, class_part = id_val.partition('.')
                for elem in elements:
                    if (not tag_name or elem.name == tag_name.lower()) and \
                       elem.get('id') == id_val and \
                       class_part in elem.get_attribute_list('class'):
                        results.append(elem)
            else:
                for elem in elements:
                    if (not tag_name or elem.name == tag_name.lower()) and \
                       elem.get('id') == id_val:
                        results.append(elem)

        # Handle class selector
        elif '.' in part:
            parts = part.split('.')
            tag_name = parts[0] if parts[0] else None
            classes = parts[1:]

            for elem in elements:
                if tag_name and elem.name != tag_name.lower():
                    continue
                elem_classes = elem.get_attribute_list('class')
                if all(c in elem_classes for c in classes):
                    results.append(elem)

        # Handle attribute selector
        elif '[' in part:
            match = re.match(r'(\w*)?\[([^\]]+)\]', part)
            if match:
                tag_name, attr_selector = match.groups()

                # Parse attribute selector
                if '=' in attr_selector:
                    if '~=' in attr_selector:
                        attr_name, attr_value = attr_selector.split('~=')
                        attr_value = attr_value.strip('"\'')
                        for elem in elements:
                            if (not tag_name or elem.name == tag_name.lower()) and \
                               attr_value in elem.get_attribute_list(attr_name):
                                results.append(elem)
                    elif '^=' in attr_selector:
                        attr_name, attr_value = attr_selector.split('^=')
                        attr_value = attr_value.strip('"\'')
                        for elem in elements:
                            if (not tag_name or elem.name == tag_name.lower()) and \
                               str(elem.get(attr_name, '')).startswith(attr_value):
                                results.append(elem)
                    elif '$=' in attr_selector:
                        attr_name, attr_value = attr_selector.split('$=')
                        attr_value = attr_value.strip('"\'')
                        for elem in elements:
                            if (not tag_name or elem.name == tag_name.lower()) and \
                               str(elem.get(attr_name, '')).endswith(attr_value):
                                results.append(elem)
                    elif '*=' in attr_selector:
                        attr_name, attr_value = attr_selector.split('*=')
                        attr_value = attr_value.strip('"\'')
                        for elem in elements:
                            if (not tag_name or elem.name == tag_name.lower()) and \
                               attr_value in str(elem.get(attr_name, '')):
                                results.append(elem)
                    else:
                        attr_name, attr_value = attr_selector.split('=')
                        attr_value = attr_value.strip('"\'')
                        for elem in elements:
                            if (not tag_name or elem.name == tag_name.lower()) and \
                               elem.get(attr_name) == attr_value:
                                results.append(elem)
                else:
                    # Just checking for attribute existence
                    for elem in elements:
                        if (not tag_name or elem.name == tag_name.lower()) and \
                           attr_selector in elem.attrs:
                            results.append(elem)

        # Handle tag name only
        else:
            tag_name = part.lower()
            for elem in elements:
                if elem.name == tag_name:
                    results.append(elem)

        return results

    def _matches(
        self,
        tag: 'Tag',
        name: Optional[Union[str, List[str], re.Pattern, Callable]] = None,
        attrs: Optional[Dict[str, Any]] = None,
        string: Optional[Union[str, re.Pattern]] = None
    ) -> bool:
        """Check if a tag matches the given criteria."""
        # Check name
        if name is not None:
            if callable(name):
                if not name(tag.name):
                    return False
            elif isinstance(name, re.Pattern):
                if not name.search(tag.name):
                    return False
            elif isinstance(name, list):
                if tag.name not in [n.lower() for n in name]:
                    return False
            elif isinstance(name, str):
                if tag.name != name.lower():
                    return False

        # Check attrs
        if attrs:
            for key, value in attrs.items():
                tag_value = tag.get(key)

                if value is True:
                    # Just check attribute exists
                    if key not in tag.attrs:
                        return False
                elif value is False or value is None:
                    # Check attribute doesn't exist
                    if key in tag.attrs:
                        return False
                elif callable(value):
                    if not value(tag_value):
                        return False
                elif isinstance(value, re.Pattern):
                    if not tag_value or not value.search(str(tag_value)):
                        return False
                elif isinstance(value, list):
                    # For class matching, check if all classes are present
                    tag_classes = tag.get_attribute_list(key)
                    if not all(v in tag_classes for v in value):
                        return False
                else:
                    # Check for class membership or exact match
                    if key == 'class':
                        tag_classes = tag.get_attribute_list('class')
                        if value not in tag_classes:
                            return False
                    elif tag_value != value:
                        return False

        # Check string content
        if string is not None:
            tag_string = tag.string
            if tag_string is None:
                return False
            if isinstance(string, re.Pattern):
                if not string.search(tag_string):
                    return False
            elif tag_string != string:
                return False

        return True

    def decode(self, indent_level: int = 0, formatter: str = 'minimal') -> str:
        """Render the tag as a string."""
        indent = '  ' * indent_level if formatter == 'pretty' else ''
        newline = '\n' if formatter == 'pretty' else ''

        # Build opening tag
        attrs_str = ''
        for key, value in self.attrs.items():
            if isinstance(value, list):
                value = ' '.join(value)
            if value is True:
                attrs_str += f' {key}'
            elif value is not False and value is not None:
                attrs_str += f' {key}="{value}"'

        # Self-closing tags
        if self.name in self.SELF_CLOSING_TAGS and not self.contents:
            return f'{indent}<{self.name}{attrs_str}/>{newline}'

        # Opening tag
        result = f'{indent}<{self.name}{attrs_str}>'

        # Contents
        if self.contents:
            if formatter == 'pretty':
                result += newline
                for child in self.contents:
                    if isinstance(child, Tag):
                        result += child.decode(indent_level + 1, formatter)
                    else:
                        child_text = str(child).strip()
                        if child_text:
                            result += f'{"  " * (indent_level + 1)}{child_text}{newline}'
                result += indent
            else:
                for child in self.contents:
                    if isinstance(child, Tag):
                        result += child.decode(0, formatter)
                    else:
                        result += str(child)

        # Closing tag
        result += f'</{self.name}>'
        if formatter == 'pretty':
            result += newline

        return result

    def prettify(self, formatter: str = 'pretty') -> str:
        """Return a nicely formatted string representation."""
        return self.decode(formatter=formatter)

    # Aliases
    findAll = find_all
    findParent = find_parent
    findParents = find_parents
    findNextSibling = find_next_sibling
    findNextSiblings = find_next_siblings
    findPreviousSibling = find_previous_sibling
    findPreviousSiblings = find_previous_siblings
    getText = get_text
