---
title: To-Do List
order: 3
icon: ✅
time: 2-3 hours
summary: A to-do list with priorities, due dates, tags and search, saved to a JSON file. Your first project with persistent data and a separate storage layer.
python_skills:
  - dataclasses, asdict and replace
  - Dates with datetime.date and ISO strings
  - Reading and writing JSON files with pathlib
  - argparse sub-commands (todo add / list / done)
  - Sorting with a key function and tuples
oop_concepts:
  - Immutable value objects (frozen Task)
  - A collection class with a clear API (TodoList)
  - Separation of model and storage (a repository class)
  - __post_init__ validation
clean_code:
  - The model never touches files or user input
  - Atomic file writes (write temp file, then rename)
  - Keyword-only arguments for readable calls (`view(show_done=False)`)
  - Pytest fixtures for shared test data
features:
  - Add, complete, delete and search tasks
  - High/medium/low priority, due dates with overdue warnings, tags
  - Smart ordering - open first, then priority, then due date
  - Same data from the terminal (`todo add …`) and the web UI
architecture: |
  classDiagram
    class Priority {
      <<IntEnum>>
      LOW = 1
      MEDIUM = 2
      HIGH = 3
    }
    class Task {
      <<frozen dataclass>>
      +id int
      +title str
      +priority Priority
      +due date
      +done bool
      +tags tuple
      +is_overdue(today) bool
      +to_dict() dict
      +from_dict(data)$ Task
    }
    class TodoList {
      +tasks dict~int, Task~
      +add(title, priority, due, tags) Task
      +toggle(id) Task
      +update(id, **changes) Task
      +remove(id)
      +view(show_done, tag, query) list~Task~
      +stats(today) dict
    }
    class JsonTodoStore {
      +path Path
      +load() TodoList
      +save(todo)
    }
    TodoList "1" *-- "*" Task
    Task --> Priority
    JsonTodoStore ..> TodoList : loads / saves
flow: |
  flowchart LR
    R[POST /3/toggle] --> L[store.load]
    L --> M["todo.toggle(3)<br/>(model rule)"]
    M --> S[store.save<br/>atomic write]
    S --> RD[redirect → GET /]
steps:
  - title: Design the Task value object
    files: [models.py]
    body: |
      A task is *data*: a frozen dataclass with an id, title, priority, due date, done flag and tags. Being frozen
      means nothing can modify a task behind your back. To change one, you build a new copy with
      `dataclasses.replace(task, done=True)`. `__post_init__` rejects empty titles at creation time.
  - title: Make priorities sortable with IntEnum
    files: [models.py]
    body: |
      `IntEnum` members compare like numbers, so `-t.priority` in a sort key puts HIGH first. The sort key
      `(t.done, -t.priority, t.due or date.max, t.id)` reads like the rule: open before done, important first,
      soonest first, tasks without a date last.
  - title: Write the TodoList collection
    files: [models.py]
    body: |
      `TodoList` owns a `dict[int, Task]` and exposes verbs: `add`, `toggle`, `update`, `remove`, `view`, `stats`.
      Each method does one thing. `get` turns a missing key into a domain error (`TaskNotFoundError`) so callers
      never see a bare `KeyError`. `today` is a *parameter* of `stats()`, never `date.today()` inside, so tests control time.
  - title: Persist with a separate storage class
    files: [storage.py]
    body: |
      `JsonTodoStore` knows the file format; `TodoList` doesn't. That's the **repository** idea: swap JSON for SQLite
      later without touching the model. `save` writes to a temp file and then `os.replace`s it, an atomic rename,
      so a crash can't leave a half-written file.
  - title: Test model and storage
    files: [tests/test_todo.py]
    body: |
      A `@pytest.fixture` builds the same three-task list for every test. Storage tests use pytest's built-in `tmp_path`,
      so they never touch your real data. The round-trip test (`save` then `load` gives an equal list) catches every
      serialisation bug at once.
  - title: A real command-line tool with argparse
    files: [cli.py]
    body: |
      `argparse` sub-commands give you `python -m projects.beginner.todo_list add "Buy milk" -p high -t shop`,
      with `--help` for free. `type=date.fromisoformat` validates dates while parsing. The CLI follows the same
      pattern as the web: load → one model call → save.
  - title: The web UI and the POST-redirect-GET pattern
    files: [web.py, templates/todo_list/index.html]
    body: |
      Changing data uses **POST**; showing data uses **GET**. After every POST we redirect, so refreshing never
      re-submits. Filters (tag, search, show completed) are GET query parameters. The template only *displays*;
      sorting and filtering stay in `TodoList.view`.
exercises:
  - Add **sub-tasks** (a task can have child tasks). How should `toggle` behave on a parent?
  - Replace `JsonTodoStore` with an `SqliteTodoStore` that has the same two methods. The rest of the code shouldn't change.
  - Add **recurring tasks** ("every Monday"). When one is completed, create the next occurrence.
  - Add an `edit` command and an inline edit form, both using `TodoList.update`.
---

## The key idea: model ↔ storage ↔ interface

```mermaid
flowchart LR
  CLI[cli.py] --> M[models.py<br/>Task · TodoList]
  WEB[web.py] --> M
  CLI --> ST[storage.py<br/>JsonTodoStore]
  WEB --> ST
  ST <--> F[(instance/todo.json)]
```

Both interfaces share **one** data file (`instance/todo.json`). Add a task in the terminal and refresh the browser.
