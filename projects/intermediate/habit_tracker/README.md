---
title: Habit Tracker
order: 5
icon: 🔥
time: 3-4 hours
summary: Daily and weekly habits with one-click check-ins, current and best streaks, completion rates and a 12-week heatmap. A deep dive into date logic and testable time.
python_skills:
  - datetime.date, timedelta, weekday()
  - Sets of dates for fast membership checks
  - Sorting and scanning for consecutive runs
  - Enums with string values for JSON
oop_concepts:
  - Behaviour lives with the data (streak methods on Habit)
  - Private helper methods (_period_done, _step) that unify daily and weekly logic
  - A collection class and a separate store
  - Alternative constructor from_dict
clean_code:
  - Never call date.today() inside logic - pass `today` in
  - Name the tricky rule in a docstring ("today is still in progress")
  - One algorithm for two frequencies via small helpers
  - Tests with a fixed date and readable helpers (`days_ago(0, 1, 2)`)
features:
  - Daily habits and "N times per week" habits
  - Click a day to check in or undo
  - Current streak 🔥, best streak 🏆 and 30-day completion rate
  - GitHub-style heatmap of the last 12 weeks
architecture: |
  classDiagram
    class Frequency {
      <<enum>>
      DAILY
      WEEKLY
    }
    class Habit {
      +id int
      +name str
      +icon str
      +frequency Frequency
      +target int
      +created_on date
      +check_ins set~date~
      +toggle(day, today) bool
      +current_streak(today) int
      +longest_streak() int
      +completion_rate(today, days) float
      -_period_done(start) bool
      -_period_of(day) date
      -_step() timedelta
    }
    class HabitTracker {
      +habits dict
      +add(...) Habit
      +get(id) Habit
      +remove(id)
      +today_progress(today) tuple
    }
    class JsonHabitStore {
      +load() HabitTracker
      +save(tracker)
    }
    HabitTracker "1" *-- "*" Habit
    Habit --> Frequency
    JsonHabitStore ..> HabitTracker
flow: |
  flowchart TD
    S["current_streak(today)"] --> P["period = this day / this week"]
    P --> Q{period done?}
    Q -->|no| B["step back one period<br/>(today is still in progress)"]
    Q -->|yes| L
    B --> L{"period done?"}
    L -->|yes| C["streak += 1, step back"] --> L
    L -->|no| R[return streak]
steps:
  - title: Store check-ins as a set of dates
    files: [habits.py]
    body: |
      A habit is its settings plus `check_ins: set[date]`. "Was it done on Tuesday?" is `day in check_ins`, an O(1)
      lookup, and toggling is add/remove. Streaks and rates are computed from this set, never stored.
  - title: Define the streak rule precisely
    files: [habits.py]
    body: |
      Ambiguity is where bugs hide. *If today isn't checked yet, is the streak broken?* No: today is still in progress.
      The docstring states the rule and the tests pin it down: done yesterday and the day before → streak 2, even at 8 am.
  - title: One algorithm for daily and weekly habits
    files: [habits.py]
    body: |
      Three helpers abstract the difference: `_period_of(day)` (the day itself, or the Monday of its week), `_step()` (1 day or
      7) and `_period_done(start)` (checked that day, or ≥ target check-ins that week). `current_streak` and
      `longest_streak` are then written once and work for both.
  - title: Make time a parameter
    files: [habits.py, tests/test_habits.py]
    body: |
      Every method takes `today`. The tests fix `TODAY = date(2026, 3, 18)` and use `days_ago(0, 1, 2)` to build histories.
      The suite passes on any day of the year, forever.
  - title: Persist and wire up the interfaces
    files: [cli.py, web.py]
    body: |
      The JSON store saves dates as ISO strings. The CLI (`habits done 1`) and the web page share the same file.
  - title: Visualise with plain HTML
    files: [templates/habit_tracker/index.html]
    body: |
      The week grid is seven POST buttons per habit, one per day. The heatmap is 12 columns × 7 small squares, coloured by
      `h.done_on(day)`. The view computes the dates; the template just paints them.
exercises:
  - Add **reminders** - list habits not yet done today after 6 pm.
  - Support **"every N days"** habits (e.g. every 3 days). Which helper methods change?
  - Add **notes** per check-in (a dict of date → note instead of a set). What's the migration plan for existing JSON files?
  - Show a weekly summary chart of completion rate over the last 12 weeks.
---

## Why `today` is a parameter

Code that calls `date.today()` deep inside gives different answers on different days, so its tests are flaky
(they fail at midnight, on Mondays, in February…). Passing `today` in makes every function **deterministic**:
same inputs, same output. The web route is the only place that asks the real clock.
