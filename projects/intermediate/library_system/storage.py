"""JSON persistence, including polymorphic items (the "type" field decides the class), plus sample data."""

from __future__ import annotations

import json
from collections import deque
from datetime import date
from pathlib import Path

from .items import DVD, Book, Magazine, ReferenceBook, item_from_dict
from .library import Library, Loan, Member


def save(library: Library, path: Path) -> None:
    data = {
        "items": [i.to_dict() for i in library.items.values()],
        "members": [vars(m) for m in library.members.values()],
        "loans": [{**vars(l), "borrowed_on": l.borrowed_on.isoformat(), "due_on": l.due_on.isoformat(),
                   "returned_on": l.returned_on.isoformat() if l.returned_on else None} for l in library.loans],
        "holds": {k: list(v) for k, v in library.holds.items() if v},
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load(path: Path) -> Library:
    if not Path(path).exists():
        return sample_library()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    library = Library()
    for item in data["items"]:
        library.add_item(item_from_dict(item))
    for m in data["members"]:
        library.add_member(Member(**m))
    library.loans = [Loan(l["item_id"], l["member_id"], date.fromisoformat(l["borrowed_on"]), date.fromisoformat(l["due_on"]),
                          date.fromisoformat(l["returned_on"]) if l["returned_on"] else None) for l in data["loans"]]
    library.holds = {k: deque(v) for k, v in data.get("holds", {}).items()}
    return library


def sample_library() -> Library:
    lib = Library()
    for item in [
        Book("B1", "Fluent Python", 2022, "Luciano Ramalho", "9781492056355"),
        Book("B2", "Clean Code", 2008, "Robert C. Martin", "9780132350884"),
        Book("B3", "Python Crash Course", 2023, "Eric Matthes", "9781718502703"),
        Book("B4", "The Pragmatic Programmer", 2019, "David Thomas & Andrew Hunt", "9780135957059"),
        Book("B5", "Design Patterns", 1994, "Gamma, Helm, Johnson, Vlissides", "9780201633610"),
        ReferenceBook("R1", "Oxford English Dictionary", 1989, "Oxford University Press"),
        DVD("D1", "The Imitation Game", 2014, "Morten Tyldum", 114),
        DVD("D2", "Hidden Figures", 2016, "Theodore Melfi", 127),
        Magazine("M1", "Python Monthly", 2026, "March", "PSF Press"),
    ]:
        lib.add_item(item)
    for member in [Member("U1", "Ada Lovelace"), Member("U2", "Alan Turing", max_loans=5), Member("U3", "Grace Hopper")]:
        lib.add_member(member)
    return lib
