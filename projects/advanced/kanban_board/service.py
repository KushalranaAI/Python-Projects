"""Layer 3 - the service: business rules (validation, WIP limits). It talks to the repository, never to Flask."""

from __future__ import annotations

from dataclasses import replace

from .domain import Board, Card, DomainError, Priority, WipLimitReached, validate_title
from .repository import KanbanRepository

DEFAULT_COLUMNS = [("To do", None), ("In progress", 3), ("Review", 2), ("Done", None)]


class KanbanService:
    def __init__(self, repo: KanbanRepository):
        self.repo = repo

    def ensure_demo_board(self) -> int:
        boards = self.repo.boards()
        if boards:
            return boards[0][0]
        board_id = self.repo.create_board("My project", DEFAULT_COLUMNS)
        board = self.repo.board(board_id)
        todo, doing, _, done = (c.id for c in board.columns)
        for column, title, priority, tags in [
            (todo, "Write the domain model", Priority.HIGH, ("design",)), (todo, "Add pagination to the API", Priority.NORMAL, ("api",)),
            (doing, "Drag and drop between columns", Priority.HIGH, ("ui",)), (done, "Set up the SQLite schema", Priority.NORMAL, ("db",)),
        ]:
            self.repo.insert_card(column, title, "", priority, tags)
        return board_id

    def board(self, board_id: int) -> Board:
        return self.repo.board(board_id)

    def add_card(self, column_id: int, title: str, description: str = "", priority: str = "normal", tags: list[str] | None = None) -> Card:
        column = self.repo.column(column_id)
        self._check_wip(column.board_id, column_id)
        clean_tags = tuple(sorted({t.strip().lower() for t in tags or [] if t.strip()}))
        card_id = self.repo.insert_card(column_id, validate_title(title), description.strip()[:2000], self._priority(priority), clean_tags)
        return self.repo.card(card_id)

    def edit_card(self, card_id: int, **changes) -> Card:
        card = self.repo.card(card_id)
        allowed = {"title", "description", "priority", "tags"}
        unknown = set(changes) - allowed
        if unknown:
            raise DomainError(f"Can't change: {', '.join(sorted(unknown))}.")
        if "title" in changes:
            changes["title"] = validate_title(changes["title"])
        if "priority" in changes:
            changes["priority"] = self._priority(changes["priority"])
        if "tags" in changes:
            changes["tags"] = tuple(sorted({t.strip().lower() for t in changes["tags"] if t.strip()}))
        updated = replace(card, **changes)
        self.repo.update_card(updated)
        return updated

    def move_card(self, card_id: int, to_column: int, position: int) -> Card:
        card, target = self.repo.card(card_id), self.repo.column(to_column)
        if self.repo.column(card.column_id).board_id != target.board_id:
            raise DomainError("Cards can only move within their board.")
        if card.column_id != to_column:
            self._check_wip(target.board_id, to_column)
        self.repo.move_card(card_id, to_column, position)
        return self.repo.card(card_id)

    def delete_card(self, card_id: int) -> None:
        self.repo.delete_card(card_id)

    # --- rules
    def _check_wip(self, board_id: int, column_id: int) -> None:
        board = self.repo.board(board_id)
        column = next(c for c in board.columns if c.id == column_id)
        if column.wip_limit is not None and len(board.cards_in(column_id)) >= column.wip_limit:
            raise WipLimitReached(f"“{column.name}” is at its limit of {column.wip_limit} cards - finish something first.")

    @staticmethod
    def _priority(value: str) -> Priority:
        try:
            return Priority(value)
        except ValueError:
            raise DomainError(f"Priority must be one of: {', '.join(p.value for p in Priority)}.") from None
