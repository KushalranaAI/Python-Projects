---
title: Kanban Board
order: 3
icon: 📋
time: 6-8 hours
summary: A Trello-style board with drag and drop, built in four layers - domain, repository, service and a JSON REST API - with WIP limits enforced by the service and translated into HTTP status codes.
python_skills:
  - Designing a REST API (GET / POST / PATCH / DELETE, 201 / 204 / 404 / 409)
  - Flask JSON endpoints and blueprint error handlers
  - SQLite transactions, executemany, JOINs, COALESCE
  - Flask's test client for API tests
  - A little JavaScript - fetch() and drag-and-drop events
oop_concepts:
  - Layered architecture (domain → repository → service → HTTP)
  - Exceptions that carry an HTTP status as a class attribute
  - Immutable entities updated with dataclasses.replace
  - Dependency injection (service receives a repository)
clean_code:
  - Each layer only talks to the one below it
  - Business rules live in the service, not in routes or SQL
  - One error handler instead of try/except in every route
  - Allow-list of editable fields (no mass-assignment)
  - textContent, never innerHTML, for user text in JavaScript
features:
  - Four columns with drag and drop between and within them
  - WIP (work-in-progress) limits that block overloading a column
  - Add, edit and delete cards with priority and tags
  - A documented JSON API you can call from curl or any client
architecture: |
  classDiagram
    class Card {
      <<frozen>>
      +id int
      +column_id int
      +title str
      +priority Priority
      +position int
      +tags tuple
    }
    class Column {
      <<frozen>>
      +id int
      +name str
      +position int
      +wip_limit int
    }
    class Board {
      +columns list
      +cards list
      +cards_in(column) list
      +to_json() dict
    }
    class KanbanRepository {
      +transaction()
      +board(id) Board
      +insert_card(...) int
      +move_card(id, column, position)
      +delete_card(id)
    }
    class KanbanService {
      -repo KanbanRepository
      +add_card(column, title, ...) Card
      +edit_card(id, **changes) Card
      +move_card(id, column, position) Card
      -_check_wip(board, column)
    }
    class DomainError {
      +status = 400
    }
    class NotFound {
      +status = 404
    }
    class WipLimitReached {
      +status = 409
    }
    Board *-- Column
    Board *-- Card
    KanbanService --> KanbanRepository
    KanbanRepository ..> Board
    DomainError <|-- NotFound
    DomainError <|-- WipLimitReached
flow: |
  sequenceDiagram
    participant JS as Browser (fetch)
    participant API as web.py route
    participant S as KanbanService
    participant R as KanbanRepository
    participant DB as SQLite
    JS->>API: PATCH /api/cards/7 {"column_id": 3, "position": 0}
    API->>S: move_card(7, 3, 0)
    S->>R: board(...) - check WIP limit
    alt column full
      S-->>API: raise WipLimitReached
      API-->>JS: 409 {"error": "“Review” is at its limit…"}
    else ok
      S->>R: move_card(7, 3, 0)
      R->>DB: UPDATE … (one transaction)
      API-->>JS: 200 {card}
    end
steps:
  - title: Draw the layers before writing code
    body: |
      **Domain** (what a card is, which errors exist) → **Repository** (SQL) → **Service** (rules) → **HTTP** (JSON in and out).
      Each layer only imports the one below. You can test the service without Flask, and swap SQLite without touching the rules.
  - title: Domain entities and errors
    files: [domain.py]
    body: |
      `Card`, `Column` and `Board` are frozen dataclasses with `to_json`. Errors subclass `DomainError` and declare their HTTP
      `status` as a class attribute (404, 409). The domain knows the *meaning* of the failure; the web layer only reads the number.
  - title: A repository with real transactions
    files: [repository.py]
    body: |
      `transaction()` commits everything inside it or rolls it all back. `move_card` re-numbers the positions of two columns
      in **one** transaction, so a crash can't leave two cards at position 0.
  - title: Business rules in the service
    files: [service.py]
    body: |
      `KanbanService` validates titles and priorities, enforces **WIP limits**, stops cards moving between boards, and
      allows only whitelisted fields in `edit_card`. Routes never contain rules, and SQL never contains rules.
  - title: A REST API with one error handler
    files: [web.py]
    body: |
      Routes are 2-4 lines: parse JSON → call the service → `jsonify`. `@bp.errorhandler(DomainError)` turns *any* rule
      violation into `{"error": "..."}` with the right status. Creation returns **201**, deletion **204 No Content**.
  - title: Test the service and the API separately
    files: [tests/test_kanban.py]
    body: |
      Service tests use a temp database. API tests use Flask's **test client** to send real HTTP requests, including bad
      JSON, a full column (409) and a missing board (404). `monkeypatch.setenv` points the app at a temp data folder.
  - title: The front end calls your API
    files: [templates/kanban_board/index.html]
    body: |
      The page is rendered once. After that, JavaScript calls `fetch()` for every change and re-draws the board from the
      JSON. Card titles are inserted with `textContent`, so a card titled `<img onerror=…>` is shown as text, not executed.
exercises:
  - Add **multiple boards** with a board switcher and a `POST /api/boards` endpoint.
  - Add **optimistic concurrency** - each card has a `version`; a PATCH with an old version gets 409.
  - Write an **OpenAPI** (Swagger) description of the API and validate requests against it.
  - Add an **activity log** table written by the service ("Ada moved X to Done"), shown in a side panel.
---

## Status codes this API uses

| Code | Meaning | When |
|---|---|---|
| 200 OK | here's the result | GET, PATCH |
| 201 Created | a new resource exists | POST a card |
| 204 No Content | done, nothing to return | DELETE |
| 400 Bad Request | your input is invalid | empty title, bad JSON, unknown field |
| 404 Not Found | no such board/card/column | wrong id |
| 409 Conflict | valid request, but the current state forbids it | WIP limit reached |

Try it from a terminal while the site runs:
`curl -X POST localhost:5050/play/kanban_board/api/columns/1/cards -H 'Content-Type: application/json' -d '{"title": "From curl"}'`
