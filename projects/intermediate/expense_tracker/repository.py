"""Persistence. The rest of the app depends on the ExpenseRepository *protocol*, not on SQLite."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator, Protocol

from .models import Budget, Category, Expense

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount      INTEGER NOT NULL CHECK (amount > 0),
    category    TEXT    NOT NULL,
    description TEXT    NOT NULL,
    spent_on    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_expenses_spent_on ON expenses (spent_on);
CREATE TABLE IF NOT EXISTS budgets (
    category    TEXT PRIMARY KEY,
    monthly_limit INTEGER NOT NULL CHECK (monthly_limit >= 0)
);
"""


class ExpenseRepository(Protocol):
    def add(self, expense: Expense) -> Expense: ...
    def delete(self, expense_id: int) -> bool: ...
    def in_month(self, month: str) -> list[Expense]: ...
    def months(self) -> list[str]: ...
    def monthly_totals(self) -> dict[str, int]: ...
    def budgets(self) -> dict[Category, Budget]: ...
    def set_budget(self, budget: Budget) -> None: ...


class SqliteExpenseRepository:
    """SQLite implementation. Every query uses ? placeholders - never string formatting (SQL injection!)."""

    def __init__(self, path: Path | str):
        self.path = str(path)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _to_expense(row: sqlite3.Row) -> Expense:
        return Expense(row["amount"], Category[row["category"]], row["description"], date.fromisoformat(row["spent_on"]), row["id"])

    def add(self, expense: Expense) -> Expense:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO expenses (amount, category, description, spent_on) VALUES (?, ?, ?, ?)",
                (expense.amount_cents, expense.category.name, expense.description.strip(), expense.spent_on.isoformat()),
            )
        return Expense(expense.amount_cents, expense.category, expense.description.strip(), expense.spent_on, cursor.lastrowid)

    def delete(self, expense_id: int) -> bool:
        with self._connect() as conn:
            return conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,)).rowcount == 1

    def in_month(self, month: str) -> list[Expense]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM expenses WHERE substr(spent_on, 1, 7) = ? ORDER BY spent_on DESC, id DESC",
                                (month,)).fetchall()
        return [self._to_expense(r) for r in rows]

    def months(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT substr(spent_on, 1, 7) AS m FROM expenses ORDER BY m DESC").fetchall()
        return [r["m"] for r in rows]

    def monthly_totals(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute("SELECT substr(spent_on, 1, 7) AS m, SUM(amount) AS total FROM expenses GROUP BY m ORDER BY m").fetchall()
        return {r["m"]: r["total"] for r in rows}

    def budgets(self) -> dict[Category, Budget]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM budgets").fetchall()
        return {Category[r["category"]]: Budget(Category[r["category"]], r["monthly_limit"]) for r in rows}

    def set_budget(self, budget: Budget) -> None:
        with self._connect() as conn:
            if budget.monthly_limit_cents == 0:
                conn.execute("DELETE FROM budgets WHERE category = ?", (budget.category.name,))
            else:
                conn.execute("INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
                             "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
                             (budget.category.name, budget.monthly_limit_cents))
