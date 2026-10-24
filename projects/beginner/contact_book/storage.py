"""JSON persistence for the contact book."""

from __future__ import annotations

import json
from pathlib import Path

from .contacts import Contact, ContactBook


class JsonContactStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> ContactBook:
        if not self.path.exists():
            return ContactBook()
        return ContactBook([Contact.from_dict(d) for d in json.loads(self.path.read_text(encoding="utf-8"))])

    def save(self, book: ContactBook) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps([c.to_dict() for c in book], indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
