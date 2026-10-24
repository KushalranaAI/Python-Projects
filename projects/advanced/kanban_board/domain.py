"""Layer 1 - domain: entities and the errors the business rules can raise. No Flask, no SQL."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class DomainError(Exception):
    status = 400                         # the API layer turns this into an HTTP status code


class NotFound(DomainError):
    status = 404


class WipLimitReached(DomainError):
    status = 409


@dataclass(frozen=True)
class Column:
    id: int
    board_id: int
    name: str
    position: int
    wip_limit: int | None = None         # max cards allowed ("work in progress" limit)


@dataclass(frozen=True)
class Card:
    id: int
    column_id: int
    title: str
    description: str = ""
    priority: Priority = Priority.NORMAL
    position: int = 0
    tags: tuple[str, ...] = ()

    def to_json(self) -> dict:
        data = asdict(self)
        data["priority"] = self.priority.value
        data["tags"] = list(self.tags)
        return data


@dataclass(frozen=True)
class Board:
    id: int
    name: str
    columns: list[Column] = field(default_factory=list)
    cards: list[Card] = field(default_factory=list)

    def cards_in(self, column_id: int) -> list[Card]:
        return sorted((c for c in self.cards if c.column_id == column_id), key=lambda c: c.position)

    def to_json(self) -> dict:
        return {"id": self.id, "name": self.name,
                "columns": [{**asdict(col), "cards": [c.to_json() for c in self.cards_in(col.id)]} for col in self.columns]}


def validate_title(title: str) -> str:
    title = " ".join(title.split())
    if not 1 <= len(title) <= 120:
        raise DomainError("A card title needs 1-120 characters.")
    return title
