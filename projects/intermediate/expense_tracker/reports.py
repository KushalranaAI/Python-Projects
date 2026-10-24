"""Reports are pure functions of a list of expenses - no database needed, so they're trivial to test."""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from .models import Budget, Category, Expense


@dataclass(frozen=True)
class BudgetStatus:
    category: Category
    spent: int
    limit: int

    @property
    def ratio(self) -> float:
        return self.spent / self.limit if self.limit else 0.0

    @property
    def remaining(self) -> int:
        return self.limit - self.spent

    @property
    def level(self) -> str:
        return "over" if self.ratio > 1 else "warning" if self.ratio >= 0.8 else "ok"


@dataclass(frozen=True)
class MonthlyReport:
    month: str
    total: int
    by_category: list[tuple[Category, int]]
    biggest: list[Expense]
    daily_average: int
    previous_total: int | None
    budgets: list[BudgetStatus]

    @property
    def change_vs_previous(self) -> float | None:
        if not self.previous_total:
            return None
        return (self.total - self.previous_total) / self.previous_total


def previous_month(month: str) -> str:
    year, mon = map(int, month.split("-"))
    return f"{year - 1}-12" if mon == 1 else f"{year}-{mon - 1:02d}"


def days_counted(month: str, today: date) -> int:
    """Average over the days that have passed: the whole month if it's over, up to today if it's the current one."""
    year, mon = map(int, month.split("-"))
    days_in_month = calendar.monthrange(year, mon)[1]
    if (year, mon) == (today.year, today.month):
        return today.day
    return days_in_month


def monthly_report(month: str, expenses: list[Expense], budgets: dict[Category, Budget], today: date,
                   previous_total: int | None = None) -> MonthlyReport:
    totals: dict[Category, int] = defaultdict(int)
    for e in expenses:
        totals[e.category] += e.amount_cents
    total = sum(totals.values())
    statuses = [BudgetStatus(cat, totals.get(cat, 0), b.monthly_limit_cents) for cat, b in budgets.items()]
    return MonthlyReport(
        month=month,
        total=total,
        by_category=sorted(totals.items(), key=lambda kv: kv[1], reverse=True),
        biggest=sorted(expenses, key=lambda e: e.amount_cents, reverse=True)[:5],
        daily_average=total // max(days_counted(month, today), 1),
        previous_total=previous_total,
        budgets=sorted(statuses, key=lambda s: s.ratio, reverse=True),
    )
