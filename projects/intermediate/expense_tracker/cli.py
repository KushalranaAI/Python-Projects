"""Terminal interface:  add | list | report | budget"""

from __future__ import annotations

import argparse
from datetime import date

from projects.ui_kit import data_path

from .models import Budget, Category, Expense, money, parse_amount
from .reports import monthly_report, previous_month
from .repository import SqliteExpenseRepository


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="expenses")
    sub = parser.add_subparsers(dest="command")
    add = sub.add_parser("add")
    add.add_argument("amount")
    add.add_argument("category", choices=[c.name.lower() for c in Category])
    add.add_argument("description")
    add.add_argument("--date", type=date.fromisoformat, default=date.today())
    for name in ("list", "report"):
        sub.add_parser(name).add_argument("--month", default=date.today().strftime("%Y-%m"))
    budget = sub.add_parser("budget")
    budget.add_argument("category", choices=[c.name.lower() for c in Category])
    budget.add_argument("limit")
    args = parser.parse_args(argv)
    repo = SqliteExpenseRepository(data_path("expenses.db"))

    try:
        if args.command == "add":
            e = repo.add(Expense(parse_amount(args.amount), Category[args.category.upper()], args.description, args.date))
            print(f"Added #{e.id}: {money(e.amount_cents)} {e.category.icon} {e.description}")
        elif args.command == "budget":
            repo.set_budget(Budget(Category[args.category.upper()], parse_amount(args.limit) if args.limit != "0" else 0))
            print("Budget saved.")
        elif args.command == "report":
            totals = repo.monthly_totals()
            r = monthly_report(args.month, repo.in_month(args.month), repo.budgets(), date.today(), totals.get(previous_month(args.month)))
            print(f"{args.month}: {money(r.total)} (≈ {money(r.daily_average)}/day)")
            for cat, cents in r.by_category:
                print(f"  {cat.icon} {cat.label:<18} {money(cents):>12}")
            for s in r.budgets:
                print(f"  budget {s.category.label:<14} {s.ratio:6.0%} of {money(s.limit)}  [{s.level}]")
        else:
            month = getattr(args, "month", date.today().strftime("%Y-%m"))
            for e in repo.in_month(month):
                print(f"  #{e.id:<4} {e.spent_on}  {money(e.amount_cents):>10}  {e.category.icon} {e.description}")
    except ValueError as error:
        raise SystemExit(f"error: {error}")


if __name__ == "__main__":
    main()
