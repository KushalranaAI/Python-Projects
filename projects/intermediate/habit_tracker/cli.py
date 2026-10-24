"""Terminal interface: today's checklist plus streaks."""

from __future__ import annotations

import argparse
from datetime import date

from projects.ui_kit import data_path

from .habits import Frequency, JsonHabitStore


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="habits")
    sub = parser.add_subparsers(dest="command")
    add = sub.add_parser("add")
    add.add_argument("name")
    add.add_argument("--weekly", type=int, metavar="TIMES", help="weekly habit with this many days per week")
    sub.add_parser("done").add_argument("id", type=int)
    args = parser.parse_args(argv)
    store = JsonHabitStore(data_path("habits.json"))
    tracker, today = store.load(), date.today()
    try:
        if args.command == "add":
            freq = Frequency.WEEKLY if args.weekly else Frequency.DAILY
            h = tracker.add(args.name, frequency=freq, target=args.weekly or 1)
            print(f"Added #{h.id} {h.name}")
        elif args.command == "done":
            h = tracker.get(args.id)
            print(f"{h.name}: {'checked ✔' if h.toggle(today, today) else 'unchecked'}")
        store.save(tracker)
    except (ValueError, LookupError) as error:
        raise SystemExit(f"error: {error}")
    done, total = tracker.today_progress(today)
    print(f"\nToday {done}/{total} daily habits")
    for h in tracker.habits.values():
        mark = "✔" if h.done_on(today) else "○"
        print(f"  {mark} #{h.id} {h.icon} {h.name:<24} 🔥 {h.current_streak(today)}  best {h.longest_streak()}  "
              f"{h.completion_rate(today):.0%} (30d)")


if __name__ == "__main__":
    main()
