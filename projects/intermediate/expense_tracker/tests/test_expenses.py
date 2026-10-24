from datetime import date, timedelta

import pytest

from projects.intermediate.expense_tracker.models import Budget, Category, Expense, money, parse_amount
from projects.intermediate.expense_tracker.reports import days_counted, monthly_report, previous_month
from projects.intermediate.expense_tracker.repository import SqliteExpenseRepository


@pytest.fixture
def repo(tmp_path) -> SqliteExpenseRepository:
    r = SqliteExpenseRepository(tmp_path / "test.db")
    r.add(Expense(1250, Category.FOOD, "Groceries", date(2026, 3, 2)))
    r.add(Expense(4000, Category.TRANSPORT, "Train pass", date(2026, 3, 1)))
    r.add(Expense(899, Category.FOOD, "Lunch", date(2026, 3, 15)))
    r.add(Expense(3000, Category.ENTERTAINMENT, "Concert", date(2026, 2, 20)))
    return r


@pytest.mark.parametrize("text, cents", [("12.50", 1250), ("1,000", 100000), ("0.01", 1), (" 7 ", 700)])
def test_parse_amount(text, cents):
    assert parse_amount(text) == cents


@pytest.mark.parametrize("bad", ["0", "-5", "abc", "1.234", ""])
def test_parse_amount_rejects(bad):
    with pytest.raises(ValueError):
        parse_amount(bad)


def test_expense_validation():
    with pytest.raises(ValueError):
        Expense(100, Category.FOOD, "  ", date(2026, 1, 1))
    with pytest.raises(ValueError):
        Expense(100, Category.FOOD, "Time travel", date.today() + timedelta(days=1))


def test_repository_round_trip(repo):
    march = repo.in_month("2026-03")
    assert [e.description for e in march] == ["Lunch", "Groceries", "Train pass"]
    assert all(e.id for e in march)
    assert repo.months() == ["2026-03", "2026-02"]
    assert repo.monthly_totals() == {"2026-02": 3000, "2026-03": 6149}


def test_delete(repo):
    lunch = repo.in_month("2026-03")[0]
    assert repo.delete(lunch.id) and not repo.delete(lunch.id)


def test_sql_injection_is_harmless(repo):
    repo.add(Expense(100, Category.OTHER, "x'); DROP TABLE expenses; --", date(2026, 3, 3)))
    assert len(repo.in_month("2026-03")) == 4
    assert repo.in_month("2026-03' OR '1'='1") == []


def test_budgets_upsert_and_remove(repo):
    repo.set_budget(Budget(Category.FOOD, 2000))
    repo.set_budget(Budget(Category.FOOD, 2500))
    assert repo.budgets()[Category.FOOD].monthly_limit_cents == 2500
    repo.set_budget(Budget(Category.FOOD, 0))
    assert repo.budgets() == {}


def test_monthly_report(repo):
    repo.set_budget(Budget(Category.FOOD, 2000))
    report = monthly_report("2026-03", repo.in_month("2026-03"), repo.budgets(), today=date(2026, 4, 10), previous_total=3000)
    assert report.total == 6149 and report.by_category[0] == (Category.TRANSPORT, 4000)
    assert report.daily_average == 6149 // 31
    assert report.change_vs_previous == pytest.approx((6149 - 3000) / 3000)
    food = report.budgets[0]
    assert (food.spent, food.remaining, food.level) == (2149, -149, "over")


def test_month_helpers():
    assert previous_month("2026-01") == "2025-12" and previous_month("2026-10") == "2026-09"
    assert days_counted("2026-02", date(2026, 5, 1)) == 28 and days_counted("2026-05", date(2026, 5, 9)) == 9


def test_money():
    assert money(123456) == "$1,234.56"
