"""Flask interface. Every request: load the list → change it through the model → save → redirect."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from projects.ui_kit import data_path, run_standalone

from .models import Priority, TaskNotFoundError
from .storage import JsonTodoStore

bp = Blueprint("todo_list", __name__, template_folder="templates")


def store() -> JsonTodoStore:
    return JsonTodoStore(data_path("todo.json"))


@bp.get("/")
def index():
    todo = store().load()
    tag = request.args.get("tag") or None
    query = request.args.get("q", "")
    show_done = "hide_done" not in request.args
    return render_template("todo_list/index.html", tasks=todo.view(show_done=show_done, tag=tag, query=query),
                           stats=todo.stats(date.today()), tags=todo.all_tags(), tag=tag, query=query,
                           show_done=show_done, priorities=list(Priority), today=date.today())


@bp.post("/add")
def add():
    s = store()
    todo = s.load()
    try:
        due = date.fromisoformat(request.form["due"]) if request.form.get("due") else None
        tags = tuple(request.form.get("tags", "").split(","))
        task = todo.add(request.form.get("title", ""), Priority[request.form.get("priority", "MEDIUM")], due, tags)
        s.save(todo)
        flash(f"Added “{task.title}”", "success")
    except (ValueError, KeyError) as error:
        flash(str(error) if isinstance(error, ValueError) else "Invalid priority", "error")
    return redirect(url_for(".index"))


@bp.post("/<int:task_id>/<action>")
def change(task_id: int, action: str):
    s = store()
    todo = s.load()
    try:
        if action == "toggle":
            todo.toggle(task_id)
        elif action == "delete":
            todo.remove(task_id)
        s.save(todo)
    except TaskNotFoundError as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for(".index"))


@bp.post("/clear")
def clear():
    s = store()
    todo = s.load()
    flash(f"Removed {todo.clear_completed()} completed task(s)", "success")
    s.save(todo)
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "To-Do List")
