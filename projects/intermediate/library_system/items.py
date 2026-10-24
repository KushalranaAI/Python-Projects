"""Things a library lends. An abstract base class defines what every item has; subclasses add their own details
and override the rules that differ (loan period, fines, whether it can be borrowed at all)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


def isbn13_is_valid(isbn: str) -> bool:
    """ISBN-13 checksum: weights 1,3,1,3,… over 13 digits must sum to a multiple of 10."""
    digits = [int(c) for c in isbn if c.isdigit()]
    return len(digits) == 13 and sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits)) % 10 == 0


class LibraryItem(ABC):
    kind: ClassVar[str] = "item"
    icon: ClassVar[str] = "📦"
    loan_days: ClassVar[int] = 14
    daily_fine_cents: ClassVar[int] = 25

    def __init__(self, item_id: str, title: str, year: int):
        if not title.strip():
            raise ValueError("An item needs a title.")
        if not 1450 <= year <= 2100:
            raise ValueError(f"{year} doesn't look like a publication year.")
        self.id = item_id
        self.title = title.strip()
        self.year = year

    @property
    def can_borrow(self) -> bool:
        return True

    @abstractmethod
    def creator(self) -> str:
        """Who made it - author, director, publisher…"""

    def describe(self) -> str:
        return f"{self.icon} {self.title} ({self.year}) - {self.creator()}"

    def matches(self, query: str) -> bool:
        return query.lower() in f"{self.title} {self.creator()} {self.kind}".lower()

    def to_dict(self) -> dict:
        return {"type": self.kind, "id": self.id, "title": self.title, "year": self.year}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.id!r}, {self.title!r})"

    def __eq__(self, other) -> bool:
        return isinstance(other, LibraryItem) and type(self) is type(other) and self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        return hash((type(self), self.id))


class Book(LibraryItem):
    kind = "book"
    icon = "📕"

    def __init__(self, item_id: str, title: str, year: int, author: str, isbn: str = ""):
        super().__init__(item_id, title, year)          # let the parent set up the shared attributes
        if isbn and not isbn13_is_valid(isbn):
            raise ValueError(f"{isbn} is not a valid ISBN-13.")
        self.author = author
        self.isbn = isbn

    def creator(self) -> str:
        return self.author

    def to_dict(self) -> dict:
        return {**super().to_dict(), "author": self.author, "isbn": self.isbn}


class ReferenceBook(Book):
    """Dictionaries, encyclopedias: you can read them in the library but not take them home."""

    kind = "reference"
    icon = "📚"

    @property
    def can_borrow(self) -> bool:
        return False


class DVD(LibraryItem):
    kind = "dvd"
    icon = "📀"
    loan_days = 7
    daily_fine_cents = 100

    def __init__(self, item_id: str, title: str, year: int, director: str, minutes: int):
        super().__init__(item_id, title, year)
        if minutes <= 0:
            raise ValueError("Running time must be positive.")
        self.director = director
        self.minutes = minutes

    def creator(self) -> str:
        return f"dir. {self.director}, {self.minutes} min"

    def to_dict(self) -> dict:
        return {**super().to_dict(), "director": self.director, "minutes": self.minutes}


class Magazine(LibraryItem):
    kind = "magazine"
    icon = "📰"
    loan_days = 7
    daily_fine_cents = 10

    def __init__(self, item_id: str, title: str, year: int, issue: str, publisher: str = ""):
        super().__init__(item_id, title, year)
        self.issue = issue
        self.publisher = publisher

    def creator(self) -> str:
        return f"{self.publisher}, issue {self.issue}" if self.publisher else f"issue {self.issue}"

    def to_dict(self) -> dict:
        return {**super().to_dict(), "issue": self.issue, "publisher": self.publisher}


# Registry for loading from JSON: the "type" field picks the class. Adding a new item type = one new class + one entry.
ITEM_TYPES: dict[str, type[LibraryItem]] = {cls.kind: cls for cls in (Book, ReferenceBook, DVD, Magazine)}


def item_from_dict(data: dict) -> LibraryItem:
    data = dict(data)
    cls = ITEM_TYPES[data.pop("type")]
    return cls(data.pop("id"), data.pop("title"), data.pop("year"), **data)
