"""Terminal interface built on argparse sub-commands:  add, list, done, remove, clear."""

from __future__ import annotations

import argparse
from datetime import date

from projects.ui_kit import data_path

from .models import Priority, TaskNotFoundError
from .storage import JsonTodoStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="A small to-do list.")
    sub = parser.add_subparsers(dest="command")
    add = sub.add_parser("add", help="add a task")
    add.add_argument("title")
    add.add_argument("-p", "--priority", choices=[p.name.lower() for p in Priority], default="medium")
    add.add_argument("-d", "--due", type=date.fromisoformat, help="YYYY-MM-DD")
    add.add_argument("-t", "--tag", action="append", default=[])
    ls = sub.add_parser("list", help="show tasks")
    ls.add_argument("--all", action="store_true", help="include completed tasks")
    ls.add_argument("--tag")
    for name in ("done", "remove"):
        sub.add_parser(name).add_argument("id", type=int)
    sub.add_parser("clear", help="delete completed tasks")
    return parser


def print_tasks(tasks, today: date) -> None:
    if not tasks:
        print("Nothing to do 🎉")
    for t in tasks:
        due = f" (due {t.due}{' ⚠ overdue' if t.is_overdue(today) else ''})" if t.due else ""
        tags = " " + " ".join(f"#{tag}" for tag in t.tags) if t.tags else ""
        print(f"{'✔' if t.done else '○'} {t.id:>3}  [{t.priority.name[0]}] {t.title}{due}{tags}")


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    store = JsonTodoStore(data_path("todo.json"))
    todo, today = store.load(), date.today()
    try:
        if args.command == "add":
            task = todo.add(args.title, Priority[args.priority.upper()], args.due, tuple(args.tag))
            print(f"Added #{task.id}: {task.title}")
        elif args.command == "done":
            print(f"#{args.id} is now {'done' if todo.toggle(args.id).done else 'open'}")
        elif args.command == "remove":
            todo.remove(args.id)
            print(f"Removed #{args.id}")
        elif args.command == "clear":
            print(f"Removed {todo.clear_completed()} completed task(s)")
        else:
            print_tasks(todo.view(show_done=getattr(args, "all", False), tag=getattr(args, "tag", None)), today)
    except (TaskNotFoundError, ValueError) as error:
        raise SystemExit(f"error: {error}")
    store.save(todo)


if __name__ == "__main__":
    main()
