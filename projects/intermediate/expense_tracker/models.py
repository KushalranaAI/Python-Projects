"""The domain: categories, expenses and budgets. Amounts are integer cents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum


class Category(Enum):
    FOOD = ("Food & groceries", "🍎")
    TRANSPORT = ("Transport", "🚌")
    HOUSING = ("Housing", "🏠")
    UTILITIES = ("Utilities", "💡")
    HEALTH = ("Health", "💊")
    ENTERTAINMENT = ("Entertainment", "🎬")
    SHOPPING = ("Shopping", "🛍️")
    OTHER = ("Other", "📦")

    def __init__(self, label: str, icon: str):
        self.label = label
        self.icon = icon


def parse_amount(text: str | Decimal) -> int:
    """'12.5' → 1250 cents. Rejects zero, negatives and more than two decimals."""
    try:
        value = Decimal(str(text).strip().replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"'{text}' is not an amount") from None
    if value <= 0:
        raise ValueError("Amount must be positive.")
    if value != value.quantize(Decimal("0.01")):
        raise ValueError("Use at most two decimal places.")
    return int(value * 100)


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


@dataclass(frozen=True)
class Expense:
    amount_cents: int
    category: Category
    description: str
    spent_on: date
    id: int | None = None          # None until the repository stores it

    def __post_init__(self):
        if self.amount_cents <= 0:
            raise ValueError("Amount must be positive.")
        if not self.description.strip():
            raise ValueError("Add a short description.")
        if self.spent_on > date.today():
            raise ValueError("Expenses can't be in the future.")

    @property
    def month(self) -> str:
        return self.spent_on.strftime("%Y-%m")


@dataclass(frozen=True)
class Budget:
    category: Category
    monthly_limit_cents: int
