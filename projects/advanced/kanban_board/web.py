"""Layer 4 - HTTP: a JSON REST API plus one HTML page whose JavaScript calls that API.

    GET    /api/boards/<id>          the board with its columns and cards
    POST   /api/columns/<id>/cards   {"title", "description"?, "priority"?, "tags"?}        → 201
    PATCH  /api/cards/<id>           {"title"?, ...} to edit, or {"column_id", "position"} to move
    DELETE /api/cards/<id>                                                                  → 204
"""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from projects.ui_kit import data_path, run_standalone

from .domain import DomainError
from .repository import KanbanRepository
from .service import KanbanService

bp = Blueprint("kanban_board", __name__, template_folder="templates")


def service() -> KanbanService:
    return KanbanService(KanbanRepository(data_path("kanban.db")))


@bp.errorhandler(DomainError)
def domain_error(error: DomainError):
    """Every business-rule failure becomes JSON with the right status code - in one place."""
    return jsonify(error=str(error)), error.status


def body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise DomainError("Send a JSON object.")
    return data


@bp.get("/")
def index():
    board_id = service().ensure_demo_board()
    return render_template("kanban_board/index.html", board_id=board_id)


@bp.get("/api/boards/<int:board_id>")
def get_board(board_id: int):
    return jsonify(service().board(board_id).to_json())


@bp.post("/api/columns/<int:column_id>/cards")
def create_card(column_id: int):
    data = body()
    card = service().add_card(column_id, str(data.get("title", "")), str(data.get("description", "")),
                              str(data.get("priority", "normal")), list(data.get("tags", [])))
    return jsonify(card.to_json()), 201


@bp.patch("/api/cards/<int:card_id>")
def update_card(card_id: int):
    data = body()
    svc = service()
    if "column_id" in data:
        card = svc.move_card(card_id, int(data["column_id"]), int(data.get("position", 0)))
    else:
        card = svc.edit_card(card_id, **data)
    return jsonify(card.to_json())


@bp.delete("/api/cards/<int:card_id>")
def delete_card(card_id: int):
    service().delete_card(card_id)
    return "", 204


if __name__ == "__main__":
    run_standalone(bp, "Kanban Board")
