"""Layer 2 - persistence: SQL in one place. Returns domain objects, never database rows."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .domain import Board, Card, Column, NotFound, Priority

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS boards  (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS columns (id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
                                    name TEXT NOT NULL, position INTEGER NOT NULL, wip_limit INTEGER);
CREATE TABLE IF NOT EXISTS cards   (id INTEGER PRIMARY KEY, column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
                                    title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', priority TEXT NOT NULL,
                                    position INTEGER NOT NULL, tags TEXT NOT NULL DEFAULT '');
"""


class KanbanRepository:
    def __init__(self, path: Path | str):
        self.path = str(path)
        with self.transaction() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def transaction(self):
        """One connection = one transaction: everything inside commits together or not at all."""
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # --- reads
    def board(self, board_id: int) -> Board:
        with self.transaction() as db:
            row = db.execute("SELECT * FROM boards WHERE id = ?", (board_id,)).fetchone()
            if row is None:
                raise NotFound(f"Board {board_id} not found.")
            columns = [Column(r["id"], r["board_id"], r["name"], r["position"], r["wip_limit"])
                       for r in db.execute("SELECT * FROM columns WHERE board_id = ? ORDER BY position", (board_id,))]
            cards = [self._card(r) for r in db.execute(
                "SELECT cards.* FROM cards JOIN columns ON columns.id = cards.column_id WHERE columns.board_id = ?", (board_id,))]
        return Board(row["id"], row["name"], columns, cards)

    def boards(self) -> list[tuple[int, str]]:
        with self.transaction() as db:
            return [(r["id"], r["name"]) for r in db.execute("SELECT * FROM boards ORDER BY id")]

    def card(self, card_id: int) -> Card:
        with self.transaction() as db:
            row = db.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if row is None:
            raise NotFound(f"Card {card_id} not found.")
        return self._card(row)

    def column(self, column_id: int) -> Column:
        with self.transaction() as db:
            r = db.execute("SELECT * FROM columns WHERE id = ?", (column_id,)).fetchone()
        if r is None:
            raise NotFound(f"Column {column_id} not found.")
        return Column(r["id"], r["board_id"], r["name"], r["position"], r["wip_limit"])

    @staticmethod
    def _card(r) -> Card:
        return Card(r["id"], r["column_id"], r["title"], r["description"], Priority(r["priority"]), r["position"],
                    tuple(t for t in r["tags"].split(",") if t))

    # --- writes
    def create_board(self, name: str, columns: list[tuple[str, int | None]]) -> int:
        with self.transaction() as db:
            board_id = db.execute("INSERT INTO boards (name) VALUES (?)", (name,)).lastrowid
            db.executemany("INSERT INTO columns (board_id, name, position, wip_limit) VALUES (?, ?, ?, ?)",
                           [(board_id, n, i, w) for i, (n, w) in enumerate(columns)])
        return board_id

    def insert_card(self, column_id: int, title: str, description: str, priority: Priority, tags: tuple[str, ...]) -> int:
        with self.transaction() as db:
            position = db.execute("SELECT COALESCE(MAX(position) + 1, 0) FROM cards WHERE column_id = ?", (column_id,)).fetchone()[0]
            return db.execute("INSERT INTO cards (column_id, title, description, priority, position, tags) VALUES (?, ?, ?, ?, ?, ?)",
                              (column_id, title, description, priority.value, position, ",".join(tags))).lastrowid

    def update_card(self, card: Card) -> None:
        with self.transaction() as db:
            db.execute("UPDATE cards SET title = ?, description = ?, priority = ?, tags = ? WHERE id = ?",
                       (card.title, card.description, card.priority.value, ",".join(card.tags), card.id))

    def move_card(self, card_id: int, to_column: int, to_position: int) -> None:
        """Re-number both columns so positions stay 0, 1, 2… - all in a single transaction."""
        with self.transaction() as db:
            from_column = db.execute("SELECT column_id FROM cards WHERE id = ?", (card_id,)).fetchone()["column_id"]
            target = [r["id"] for r in db.execute("SELECT id FROM cards WHERE column_id = ? AND id != ? ORDER BY position",
                                                  (to_column, card_id))]
            target.insert(max(0, min(to_position, len(target))), card_id)
            db.executemany("UPDATE cards SET column_id = ?, position = ? WHERE id = ?", [(to_column, i, cid) for i, cid in enumerate(target)])
            if from_column != to_column:
                source = [r["id"] for r in db.execute("SELECT id FROM cards WHERE column_id = ? ORDER BY position", (from_column,))]
                db.executemany("UPDATE cards SET position = ? WHERE id = ?", [(i, cid) for i, cid in enumerate(source)])

    def delete_card(self, card_id: int) -> None:
        with self.transaction() as db:
            if db.execute("DELETE FROM cards WHERE id = ?", (card_id,)).rowcount == 0:
                raise NotFound(f"Card {card_id} not found.")
