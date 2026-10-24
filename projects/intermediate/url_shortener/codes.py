"""Short codes: base62-encode the database id, and validate URLs and custom aliases."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)                        # 62
OFFSET = BASE ** 2                          # start at "100" so every code has at least 3 characters
ALIAS = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
RESERVED = {"api", "admin", "stats", "go", "new", "static", "login"}


def encode(number: int) -> str:
    """Repeated division by 62, like converting to binary but with 62 digits. 125 → '21'."""
    if number < 0:
        raise ValueError("Only non-negative numbers can be encoded.")
    digits = []
    while True:
        number, remainder = divmod(number, BASE)
        digits.append(ALPHABET[remainder])
        if number == 0:
            return "".join(reversed(digits))


def decode(code: str) -> int:
    number = 0
    for char in code:
        index = ALPHABET.find(char)
        if index < 0:
            raise ValueError(f"'{char}' isn't a valid code character.")
        number = number * BASE + index
    return number


def code_for_id(link_id: int) -> str:
    return encode(link_id + OFFSET)


class InvalidURLError(ValueError):
    pass


def normalize_url(raw: str) -> str:
    """Accept 'example.com/page', return 'https://example.com/page'. Reject anything that isn't a web address."""
    url = raw.strip()
    if not url:
        raise InvalidURLError("Paste a URL to shorten.")
    if len(url) > 2048:
        raise InvalidURLError("That URL is too long (max 2048 characters).")
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        raise InvalidURLError("Only http:// and https:// links can be shortened.")
    host = parts.hostname or ""
    if not host or (" " in url) or ("." not in host and host != "localhost"):
        raise InvalidURLError(f"'{raw}' doesn't look like a web address.")
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", parts.query, parts.fragment))


def validate_alias(alias: str) -> str:
    alias = alias.strip()
    if not ALIAS.match(alias):
        raise ValueError("Aliases use 3-32 letters, digits, '-' or '_'.")
    if alias.lower() in RESERVED:
        raise ValueError(f"'{alias}' is reserved.")
    return alias
