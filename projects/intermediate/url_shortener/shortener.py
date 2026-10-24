"""The service: shorten, resolve (and count the click), statistics. Storage is SQLite via a small repository."""

from __future__ import annotations

import sqlite3
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .codes import code_for_id, normalize_url, validate_alias

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    url TEXT NOT NULL,
    custom INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clicks (
    link_id INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    at TEXT NOT NULL,
    referrer TEXT
);
CREATE INDEX IF NOT EXISTS idx_clicks_link ON clicks(link_id);
"""


class LinkNotFoundError(LookupError):
    pass


class AliasTakenError(ValueError):
    pass


@dataclass(frozen=True)
class Link:
    id: int
    code: str
    url: str
    custom: bool
    created_at: datetime
    clicks: int = 0


@dataclass(frozen=True)
class LinkStats:
    link: Link
    clicks_by_day: list[tuple[str, int]]
    top_referrers: list[tuple[str, int]]
    last_click: datetime | None


class Shortener:
    def __init__(self, db_path: Path | str, clock=lambda: datetime.now(timezone.utc)):
        self.db_path = str(db_path)
        self.clock = clock                      # injectable, so tests control time
        with self._db() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _link(self, row) -> Link:
        return Link(row["id"], row["code"], row["url"], bool(row["custom"]), datetime.fromisoformat(row["created_at"]),
                    row["clicks"] if "clicks" in row.keys() else 0)

    def shorten(self, raw_url: str, alias: str | None = None) -> Link:
        url = normalize_url(raw_url)
        with self._db() as db:
            if alias:
                alias = validate_alias(alias)
                if db.execute("SELECT 1 FROM links WHERE code = ?", (alias,)).fetchone():
                    raise AliasTakenError(f"'{alias}' is already taken.")
            else:
                existing = db.execute("SELECT * FROM links WHERE url = ? AND custom = 0", (url,)).fetchone()
                if existing:                                   # same URL → same short code, no duplicates
                    return self._link(existing)
            cursor = db.execute("INSERT INTO links (url, custom, created_at) VALUES (?, ?, ?)",
                                (url, int(bool(alias)), self.clock().isoformat()))
            code = alias or code_for_id(cursor.lastrowid)       # the id is only known after the INSERT
            db.execute("UPDATE links SET code = ? WHERE id = ?", (code, cursor.lastrowid))
            row = db.execute("SELECT * FROM links WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._link(row)

    def resolve(self, code: str, referrer: str | None = None) -> str:
        """Return the long URL and record the click."""
        with self._db() as db:
            row = db.execute("SELECT id, url FROM links WHERE code = ?", (code,)).fetchone()
            if row is None:
                raise LinkNotFoundError(code)
            db.execute("INSERT INTO clicks (link_id, at, referrer) VALUES (?, ?, ?)", (row["id"], self.clock().isoformat(), referrer))
        return row["url"]

    def all_links(self) -> list[Link]:
        with self._db() as db:
            rows = db.execute("""SELECT links.*, COUNT(clicks.link_id) AS clicks FROM links
                                 LEFT JOIN clicks ON clicks.link_id = links.id
                                 GROUP BY links.id ORDER BY links.id DESC""").fetchall()
        return [self._link(r) for r in rows]

    def delete(self, code: str) -> None:
        with self._db() as db:
            if db.execute("DELETE FROM links WHERE code = ?", (code,)).rowcount == 0:
                raise LinkNotFoundError(code)

    def stats(self, code: str) -> LinkStats:
        link = next((l for l in self.all_links() if l.code == code), None)
        if link is None:
            raise LinkNotFoundError(code)
        with self._db() as db:
            clicks = db.execute("SELECT at, referrer FROM clicks WHERE link_id = ? ORDER BY at", (link.id,)).fetchall()
        days = Counter(c["at"][:10] for c in clicks)
        referrers = Counter(c["referrer"] or "direct" for c in clicks)
        return LinkStats(link, sorted(days.items()), referrers.most_common(5),
                         datetime.fromisoformat(clicks[-1]["at"]) if clicks else None)
