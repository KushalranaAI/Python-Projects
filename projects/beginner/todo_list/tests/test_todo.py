from datetime import date

import pytest

from projects.beginner.todo_list.models import Priority, Task, TaskNotFoundError, TodoList
from projects.beginner.todo_list.storage import JsonTodoStore


@pytest.fixture
def todo() -> TodoList:
    t = TodoList()
    t.add("Write tests", Priority.HIGH, date(2026, 1, 10), ("work",))
    t.add("Buy milk", Priority.LOW)
    t.add("Call mum", Priority.HIGH, date(2026, 1, 5), ("family",))
    return t


def test_ids_increase(todo):
    assert [t.id for t in todo.tasks.values()] == [1, 2, 3]


def test_empty_title_is_rejected():
    with pytest.raises(ValueError):
        TodoList().add("   ")


def test_view_orders_by_status_priority_then_due(todo):
    todo.toggle(1)
    assert [t.title for t in todo.view()] == ["Call mum", "Buy milk", "Write tests"]


def test_filters(todo):
    assert [t.id for t in todo.view(tag="work")] == [1]
    assert [t.id for t in todo.view(query="MILK")] == [2]
    todo.toggle(2)
    assert 2 not in [t.id for t in todo.view(show_done=False)]


def test_tasks_are_immutable_updates_replace_them(todo):
    before = todo.get(2)
    after = todo.update(2, title="Buy oat milk")
    assert before.title == "Buy milk" and after.title == "Buy oat milk"
    with pytest.raises(AttributeError):
        before.title = "x"


def test_overdue_and_stats(todo):
    stats = todo.stats(today=date(2026, 1, 7))
    assert stats == {"total": 3, "done": 0, "open": 3, "overdue": 1}


def test_missing_task_raises(todo):
    with pytest.raises(TaskNotFoundError):
        todo.toggle(99)


def test_clear_completed(todo):
    todo.toggle(1)
    todo.toggle(3)
    assert todo.clear_completed() == 2 and list(todo.tasks) == [2]


def test_json_round_trip(tmp_path, todo):
    store = JsonTodoStore(tmp_path / "todo.json")
    store.save(todo)
    assert store.load() == todo


def test_loading_a_missing_file_gives_an_empty_list(tmp_path):
    assert JsonTodoStore(tmp_path / "nope.json").load().tasks == {}


def test_task_dict_round_trip():
    task = Task(7, "x", Priority.HIGH, date(2026, 3, 1), True, ("a",))
    assert Task.from_dict(task.to_dict()) == task
