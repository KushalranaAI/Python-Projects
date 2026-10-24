import pytest

from projects.advanced.kanban_board.domain import DomainError, NotFound, WipLimitReached
from projects.advanced.kanban_board.repository import KanbanRepository
from projects.advanced.kanban_board.service import KanbanService
from projects.ui_kit import create_standalone_app


@pytest.fixture
def svc(tmp_path) -> KanbanService:
    s = KanbanService(KanbanRepository(tmp_path / "k.db"))
    s.board_id = s.ensure_demo_board()
    s.cols = [c.id for c in s.board(s.board_id).columns]      # To do, In progress (3), Review (2), Done
    return s


def titles(svc, column):
    return [c.title for c in svc.board(svc.board_id).cards_in(column)]


def test_demo_board(svc):
    board = svc.board(svc.board_id)
    assert [c.name for c in board.columns] == ["To do", "In progress", "Review", "Done"] and len(board.cards) == 4
    assert svc.ensure_demo_board() == svc.board_id                      # idempotent


def test_add_and_validate(svc):
    card = svc.add_card(svc.cols[0], "  Write   docs ", tags=["Docs", "docs", " "])
    assert card.title == "Write docs" and card.tags == ("docs",) and card.position == 2
    with pytest.raises(DomainError):
        svc.add_card(svc.cols[0], "")
    with pytest.raises(DomainError):
        svc.add_card(svc.cols[0], "x", priority="urgent")
    with pytest.raises(NotFound):
        svc.add_card(999, "x")


def test_move_reorders_both_columns(svc):
    todo, doing = svc.cols[0], svc.cols[1]
    first = svc.board(svc.board_id).cards_in(todo)[0]
    svc.move_card(first.id, doing, 0)
    assert titles(svc, doing) == ["Write the domain model", "Drag and drop between columns"]
    assert [c.position for c in svc.board(svc.board_id).cards_in(todo)] == [0]
    svc.move_card(first.id, doing, 99)                                  # within the same column, to the end
    assert titles(svc, doing)[-1] == "Write the domain model"


def test_wip_limit(svc):
    review = svc.cols[2]
    svc.add_card(review, "a")
    svc.add_card(review, "b")
    with pytest.raises(WipLimitReached):
        svc.add_card(review, "c")
    todo_card = svc.board(svc.board_id).cards_in(svc.cols[0])[0]
    with pytest.raises(WipLimitReached):
        svc.move_card(todo_card.id, review, 0)


def test_edit_rejects_unknown_fields(svc):
    card = svc.board(svc.board_id).cards[0]
    assert svc.edit_card(card.id, title="Renamed", priority="low").title == "Renamed"
    with pytest.raises(DomainError):
        svc.edit_card(card.id, column_id=1)


# ---- the HTTP layer, through Flask's test client
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PP_DATA_DIR", str(tmp_path))
    from projects.advanced.kanban_board.web import bp
    app = create_standalone_app(bp, "Kanban")
    c = app.test_client()
    assert c.get("/").status_code == 200                            # creates the demo board
    return c


def test_api_round_trip(client):
    board = client.get("/api/boards/1").get_json()
    todo = board["columns"][0]["id"]
    created = client.post(f"/api/columns/{todo}/cards", json={"title": "From the API", "tags": ["api"]})
    assert created.status_code == 201
    card_id = created.get_json()["id"]
    moved = client.patch(f"/api/cards/{card_id}", json={"column_id": board["columns"][3]["id"], "position": 0})
    assert moved.status_code == 200 and moved.get_json()["position"] == 0
    assert client.delete(f"/api/cards/{card_id}").status_code == 204
    assert client.delete(f"/api/cards/{card_id}").status_code == 404


def test_api_errors_are_json_with_status_codes(client):
    board = client.get("/api/boards/1").get_json()
    review = board["columns"][2]["id"]
    for title in ("a", "b"):
        client.post(f"/api/columns/{review}/cards", json={"title": title})
    full = client.post(f"/api/columns/{review}/cards", json={"title": "c"})
    assert full.status_code == 409 and "limit" in full.get_json()["error"]
    assert client.post(f"/api/columns/{review}/cards", data="nope").status_code == 400
    assert client.get("/api/boards/42").status_code == 404
