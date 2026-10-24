"""Saving and loading a TodoList as JSON. Kept separate so the model never touches the file system."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Task, TodoList


class JsonTodoStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> TodoList:
        if not self.path.exists():
            return TodoList()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return TodoList({t["id"]: Task.from_dict(t) for t in data["tasks"]})

    def save(self, todo: TodoList) -> None:
        """Write to a temporary file first, then rename: a crash mid-write can't corrupt your list."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "tasks": [t.to_dict() for t in todo.tasks.values()]}
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, self.path)
