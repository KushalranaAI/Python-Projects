"""Terminal interface: print the board as columns of text (reads through the same service layer)."""

from __future__ import annotations

from projects.ui_kit import data_path

from .repository import KanbanRepository
from .service import KanbanService


def main() -> None:
    svc = KanbanService(KanbanRepository(data_path("kanban.db")))
    board = svc.board(svc.ensure_demo_board())
    print(f"📋 {board.name}\n")
    for column in board.columns:
        limit = f" (WIP {column.wip_limit})" if column.wip_limit else ""
        print(f"■ {column.name}{limit}")
        for card in board.cards_in(column.id):
            print(f"   [{card.id}] {card.title}  ·{card.priority.value}  {' '.join('#' + t for t in card.tags)}")
    print("\nThe web UI (python -m projects.advanced.kanban_board.web) lets you drag cards between columns.")


if __name__ == "__main__":
    main()
