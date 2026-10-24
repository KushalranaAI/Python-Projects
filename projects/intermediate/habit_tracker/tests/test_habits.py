from datetime import date, timedelta

import pytest

from projects.intermediate.habit_tracker.habits import Frequency, Habit, HabitTracker, JsonHabitStore, week_start

TODAY = date(2026, 3, 18)          # a Wednesday


def days_ago(*ns: int) -> set[date]:
    return {TODAY - timedelta(days=n) for n in ns}


def habit(check_ins=(), **kw) -> Habit:
    return Habit(1, "Read", check_ins=set(check_ins), created_on=date(2026, 1, 1), **kw)


def test_current_streak_counts_today_and_back():
    assert habit(days_ago(0, 1, 2, 4)).current_streak(TODAY) == 3


def test_today_not_done_yet_keeps_yesterdays_streak():
    assert habit(days_ago(1, 2)).current_streak(TODAY) == 2
    assert habit(days_ago(2, 3)).current_streak(TODAY) == 0


def test_longest_streak():
    assert habit(days_ago(0, 1, 5, 6, 7, 8, 20)).longest_streak() == 4
    assert habit().longest_streak() == 0


def test_weekly_habit_streak():
    monday = week_start(TODAY)
    this_week = {monday, monday + timedelta(days=1)}
    last_week = {monday - timedelta(days=7 - i) for i in (0, 2, 4)}
    two_weeks_ago = {monday - timedelta(days=14)}
    h = habit(this_week | last_week | two_weeks_ago, frequency=Frequency.WEEKLY, target=3)
    assert h.current_streak(TODAY) == 1           # this week (2/3) is in progress; last week met the target
    assert h.longest_streak() == 1


def test_completion_rate_respects_creation_date():
    h = Habit(1, "New", created_on=TODAY - timedelta(days=3), check_ins=days_ago(0, 1))
    assert h.completion_rate(TODAY) == pytest.approx(2 / 4)


def test_toggle_and_future_days():
    h = habit()
    assert h.toggle(TODAY, TODAY) and not h.toggle(TODAY, TODAY)
    with pytest.raises(ValueError):
        h.toggle(TODAY + timedelta(days=1), TODAY)


def test_validation():
    with pytest.raises(ValueError):
        Habit(1, " ")
    with pytest.raises(ValueError):
        Habit(1, "x", frequency=Frequency.WEEKLY, target=9)


def test_tracker_and_store(tmp_path):
    t = HabitTracker()
    a = t.add("Run", "🏃", today=TODAY)
    t.add("Gym", "🏋️", Frequency.WEEKLY, 3, today=TODAY)
    a.toggle(TODAY, TODAY)
    assert t.today_progress(TODAY) == (1, 1)
    store = JsonHabitStore(tmp_path / "h.json")
    store.save(t)
    loaded = store.load()
    assert [h.to_dict() for h in loaded.habits.values()] == [h.to_dict() for h in t.habits.values()]
    loaded.remove(1)
    with pytest.raises(LookupError):
        loaded.get(1)
