"""What a task *is*, and the rules for a list of them. No files, no input/output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import date
from enum import IntEnum


class Priority(IntEnum):
    """IntEnum so priorities sort naturally: HIGH (3) > MEDIUM (2) > LOW (1)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class TaskNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    priority: Priority = Priority.MEDIUM
    due: date | None = None
    done: bool = False
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("A task needs a title.")

    def is_overdue(self, today: date) -> bool:
        return not self.done and self.due is not None and self.due < today

    def to_dict(self) -> dict:
        data = asdict(self)
        data["priority"] = self.priority.name
        data["due"] = self.due.isoformat() if self.due else None
        data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(id=data["id"], title=data["title"], priority=Priority[data["priority"]],
                   due=date.fromisoformat(data["due"]) if data.get("due") else None,
                   done=data.get("done", False), tags=tuple(data.get("tags", ())))


@dataclass
class TodoList:
    """A collection of tasks. Tasks are immutable, so 'editing' one replaces it with an updated copy."""

    tasks: dict[int, Task] = field(default_factory=dict)

    @property
    def next_id(self) -> int:
        return max(self.tasks, default=0) + 1

    def add(self, title: str, priority: Priority = Priority.MEDIUM, due: date | None = None, tags: tuple[str, ...] = ()) -> Task:
        task = Task(self.next_id, title.strip(), priority, due, tags=tuple(t.strip().lower() for t in tags if t.strip()))
        self.tasks[task.id] = task
        return task

    def get(self, task_id: int) -> Task:
        try:
            return self.tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(f"No task #{task_id}") from None

    def update(self, task_id: int, **changes) -> Task:
        task = replace(self.get(task_id), **changes)   # dataclasses.replace builds a modified copy
        self.tasks[task_id] = task
        return task

    def toggle(self, task_id: int) -> Task:
        return self.update(task_id, done=not self.get(task_id).done)

    def remove(self, task_id: int) -> None:
        self.get(task_id)
        del self.tasks[task_id]

    def clear_completed(self) -> int:
        done = [t.id for t in self.tasks.values() if t.done]
        for task_id in done:
            del self.tasks[task_id]
        return len(done)

    def view(self, *, show_done: bool = True, tag: str | None = None, query: str = "") -> list[Task]:
        """Open tasks first, then by priority (high first), then by due date (soonest first, none last)."""
        items = [t for t in self.tasks.values()
                 if (show_done or not t.done) and (tag is None or tag in t.tags) and query.lower() in t.title.lower()]
        return sorted(items, key=lambda t: (t.done, -t.priority, t.due or date.max, t.id))

    def stats(self, today: date) -> dict[str, int]:
        tasks = self.tasks.values()
        return {"total": len(self.tasks), "done": sum(t.done for t in tasks),
                "open": sum(not t.done for t in tasks), "overdue": sum(t.is_overdue(today) for t in tasks)}

    def all_tags(self) -> list[str]:
        return sorted({tag for t in self.tasks.values() for tag in t.tags})
