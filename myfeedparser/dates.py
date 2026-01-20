"""
Date parsing utilities for feedparser.
Handles RFC 822, ISO 8601, and various other date formats.
"""

import re
import time
from email.utils import parsedate_tz, mktime_tz

# Month name mappings
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

# Timezone offset mappings (in seconds)
TIMEZONES = {
    "ut": 0, "utc": 0, "gmt": 0, "z": 0,
    "est": -18000, "edt": -14400,
    "cst": -21600, "cdt": -18000,
    "mst": -25200, "mdt": -21600,
    "pst": -28800, "pdt": -25200,
}

# ISO 8601 pattern
ISO8601_RE = re.compile(
    r"(\d{4})-?(\d{2})?-?(\d{2})?"
    r"[T\s]?"
    r"(\d{2})?:?(\d{2})?:?(\d{2})?"
    r"(?:\.(\d+))?"
    r"(Z|[+-]\d{2}:?\d{2})?",
    re.IGNORECASE
)

# RFC 822 pattern (e.g., "Mon, 01 Jan 2024 12:00:00 GMT")
RFC822_RE = re.compile(
    r"(?:\w+,\s*)?"
    r"(\d{1,2})\s+(\w{3})\s+(\d{2,4})\s+"
    r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*"
    r"([A-Z]{2,4}|[+-]\d{4})?",
    re.IGNORECASE
)


def _parse_date(date_string):
    """
    Parse a date string into a time.struct_time.

    Supports:
    - RFC 822 (email format)
    - ISO 8601
    - Various common formats

    Args:
        date_string: Date string to parse

    Returns:
        time.struct_time or None if parsing fails
    """
    if not date_string:
        return None

    date_string = date_string.strip()

    # Try email.utils first (handles RFC 822 well)
    try:
        parsed = parsedate_tz(date_string)
        if parsed:
            timestamp = mktime_tz(parsed)
            return time.gmtime(timestamp)
    except (ValueError, TypeError, OverflowError):
        pass

    # Try ISO 8601
    result = _parse_iso8601(date_string)
    if result:
        return result

    # Try RFC 822 manually
    result = _parse_rfc822(date_string)
    if result:
        return result

    return None


def _parse_iso8601(date_string):
    """
    Parse ISO 8601 date format.

    Args:
        date_string: ISO 8601 date string

    Returns:
        time.struct_time or None
    """
    match = ISO8601_RE.match(date_string)
    if not match:
        return None

    groups = match.groups()
    year = int(groups[0])
    month = int(groups[1]) if groups[1] else 1
    day = int(groups[2]) if groups[2] else 1
    hour = int(groups[3]) if groups[3] else 0
    minute = int(groups[4]) if groups[4] else 0
    second = int(groups[5]) if groups[5] else 0
    tz_str = groups[7]

    # Calculate timezone offset
    tz_offset = 0
    if tz_str:
        if tz_str.upper() == "Z":
            tz_offset = 0
        elif tz_str[0] in "+-":
            sign = 1 if tz_str[0] == "+" else -1
            tz_clean = tz_str[1:].replace(":", "")
            if len(tz_clean) >= 2:
                hours = int(tz_clean[:2])
                minutes = int(tz_clean[2:4]) if len(tz_clean) >= 4 else 0
                tz_offset = sign * (hours * 3600 + minutes * 60)

    try:
        # Create time tuple
        timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0, -1))
        # Adjust for timezone
        timestamp -= tz_offset
        timestamp -= time.timezone  # Adjust for local timezone
        return time.gmtime(timestamp)
    except (ValueError, OverflowError):
        return None


def _parse_rfc822(date_string):
    """
    Parse RFC 822 date format.

    Args:
        date_string: RFC 822 date string

    Returns:
        time.struct_time or None
    """
    match = RFC822_RE.match(date_string)
    if not match:
        return None

    day, month_str, year, hour, minute, second, tz_str = match.groups()

    day = int(day)
    month = MONTHS.get(month_str.lower()[:3])
    if not month:
        return None

    year = int(year)
    if year < 100:
        year += 2000 if year < 50 else 1900

    hour = int(hour)
    minute = int(minute)
    second = int(second) if second else 0

    # Calculate timezone offset
    tz_offset = 0
    if tz_str:
        tz_lower = tz_str.lower()
        if tz_lower in TIMEZONES:
            tz_offset = TIMEZONES[tz_lower]
        elif tz_str[0] in "+-":
            sign = 1 if tz_str[0] == "+" else -1
            hours = int(tz_str[1:3])
            minutes = int(tz_str[3:5]) if len(tz_str) >= 5 else 0
            tz_offset = sign * (hours * 3600 + minutes * 60)

    try:
        timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0, -1))
        timestamp -= tz_offset
        timestamp -= time.timezone
        return time.gmtime(timestamp)
    except (ValueError, OverflowError):
        return None


def format_date(struct_time):
    """
    Format a time.struct_time as ISO 8601.

    Args:
        struct_time: time.struct_time object

    Returns:
        ISO 8601 formatted string
    """
    if not struct_time:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", struct_time)
