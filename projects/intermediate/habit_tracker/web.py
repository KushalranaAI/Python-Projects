"""Flask interface: a week grid you click to check in, streak badges and a 12-week heatmap per habit."""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from projects.ui_kit import data_path, run_standalone

from .habits import Frequency, JsonHabitStore, week_start

bp = Blueprint("habit_tracker", __name__, template_folder="templates")


def store() -> JsonHabitStore:
    return JsonHabitStore(data_path("habits.json"))


@bp.get("/")
def index():
    tracker, today = store().load(), date.today()
    week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    first = week_start(today) - timedelta(weeks=11)
    heat_weeks = [[first + timedelta(weeks=w, days=d) for d in range(7)] for w in range(12)]
    return render_template("habit_tracker/index.html", habits=list(tracker.habits.values()), today=today, week=week,
                           heat_weeks=heat_weeks, progress=tracker.today_progress(today), Frequency=Frequency)


@bp.post("/add")
def add():
    s = store()
    tracker = s.load()
    try:
        weekly = request.form.get("frequency") == "weekly"
        tracker.add(request.form.get("name", ""), request.form.get("icon", "✅"),
                    Frequency.WEEKLY if weekly else Frequency.DAILY, int(request.form.get("per_week") or 1))
        s.save(tracker)
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for(".index"))


@bp.post("/<int:habit_id>/toggle/<day>")
def toggle(habit_id: int, day: str):
    s = store()
    tracker = s.load()
    try:
        tracker.get(habit_id).toggle(date.fromisoformat(day), date.today())
        s.save(tracker)
    except (ValueError, LookupError) as error:
        flash(str(error), "error")
    return redirect(url_for(".index"))


@bp.post("/<int:habit_id>/delete")
def delete(habit_id: int):
    s = store()
    tracker = s.load()
    try:
        tracker.remove(habit_id)
        s.save(tracker)
    except LookupError:
        pass
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Habit Tracker")
