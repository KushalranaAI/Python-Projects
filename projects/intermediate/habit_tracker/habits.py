"""Habits, check-ins and streaks. Every calculation receives `today`, so the logic never reads the clock itself."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"          # at least `target` check-ins per calendar week (Mon-Sun)


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


@dataclass
class Habit:
    id: int
    name: str
    icon: str = "✅"
    frequency: Frequency = Frequency.DAILY
    target: int = 1                         # check-ins per week for WEEKLY habits
    created_on: date = field(default_factory=date.today)
    check_ins: set[date] = field(default_factory=set)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Give the habit a name.")
        if self.frequency is Frequency.WEEKLY and not 1 <= self.target <= 7:
            raise ValueError("A weekly target is between 1 and 7 days.")

    # --- changing state
    def toggle(self, day: date, today: date) -> bool:
        """Check in (or undo a check-in) for `day`. Returns True if the day is now checked."""
        if day > today:
            raise ValueError("You can't check in for a future day.")
        if day in self.check_ins:
            self.check_ins.remove(day)
            return False
        self.check_ins.add(day)
        return True

    # --- streaks: the interesting algorithms
    def _period_done(self, start: date) -> bool:
        if self.frequency is Frequency.DAILY:
            return start in self.check_ins
        return sum(1 for d in self.check_ins if week_start(d) == start) >= self.target

    def _step(self) -> timedelta:
        return timedelta(days=1 if self.frequency is Frequency.DAILY else 7)

    def _period_of(self, day: date) -> date:
        return day if self.frequency is Frequency.DAILY else week_start(day)

    def current_streak(self, today: date) -> int:
        """Consecutive completed periods ending now. The current period still counts as 'in progress':
        if today isn't done yet, the streak is whatever ended yesterday (or last week)."""
        period = self._period_of(today)
        if not self._period_done(period):
            period -= self._step()
        streak = 0
        while self._period_done(period):
            streak += 1
            period -= self._step()
        return streak

    def longest_streak(self) -> int:
        periods = sorted({self._period_of(d) for d in self.check_ins if self._period_done(self._period_of(d))})
        best = run = 0
        previous = None
        for p in periods:
            run = run + 1 if previous is not None and p - previous == self._step() else 1
            best = max(best, run)
            previous = p
        return best

    def completion_rate(self, today: date, days: int = 30) -> float:
        """Share of the last `days` days (or the weeks they cover) that met the goal, ignoring time before the habit existed."""
        first = max(self.created_on, today - timedelta(days=days - 1))
        if first > today:
            return 0.0
        periods, period = [], self._period_of(first)
        while period <= today:
            periods.append(period)
            period += self._step()
        return sum(self._period_done(p) for p in periods) / len(periods)

    def done_on(self, day: date) -> bool:
        return day in self.check_ins

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "icon": self.icon, "frequency": self.frequency.value, "target": self.target,
                "created_on": self.created_on.isoformat(), "check_ins": sorted(d.isoformat() for d in self.check_ins)}

    @classmethod
    def from_dict(cls, d: dict) -> Habit:
        return cls(d["id"], d["name"], d.get("icon", "✅"), Frequency(d["frequency"]), d.get("target", 1),
                   date.fromisoformat(d["created_on"]), {date.fromisoformat(x) for x in d["check_ins"]})


class HabitTracker:
    def __init__(self, habits: list[Habit] | None = None):
        self.habits: dict[int, Habit] = {h.id: h for h in habits or []}

    def add(self, name: str, icon: str = "✅", frequency: Frequency = Frequency.DAILY, target: int = 1,
            today: date | None = None) -> Habit:
        habit = Habit(max(self.habits, default=0) + 1, name.strip(), icon or "✅", frequency, target, today or date.today())
        self.habits[habit.id] = habit
        return habit

    def get(self, habit_id: int) -> Habit:
        try:
            return self.habits[habit_id]
        except KeyError:
            raise LookupError(f"No habit #{habit_id}") from None

    def remove(self, habit_id: int) -> None:
        del self.habits[self.get(habit_id).id]

    def today_progress(self, today: date) -> tuple[int, int]:
        daily = [h for h in self.habits.values() if h.frequency is Frequency.DAILY]
        return sum(h.done_on(today) for h in daily), len(daily)


class JsonHabitStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> HabitTracker:
        if not self.path.exists():
            return HabitTracker()
        return HabitTracker([Habit.from_dict(d) for d in json.loads(self.path.read_text(encoding="utf-8"))])

    def save(self, tracker: HabitTracker) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([h.to_dict() for h in tracker.habits.values()], indent=2, ensure_ascii=False), encoding="utf-8")
