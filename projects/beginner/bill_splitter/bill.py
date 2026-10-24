"""Split a restaurant bill fairly: shared items, tax and tip, exact to the cent.

Money is never a float: 0.1 + 0.2 == 0.30000000000000004. We use Decimal for input and whole cents (int) for
arithmetic, and hand out leftover cents with the largest-remainder method, so the shares always add up exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def to_cents(amount: Decimal | str | int) -> int:
    try:
        value = Decimal(str(amount))
    except InvalidOperation:
        raise ValueError(f"{amount!r} is not an amount of money") from None
    if value < 0:
        raise ValueError("Amounts can't be negative.")
    return int((value / CENT).to_integral_value())


def format_cents(cents: int, currency: str = "$") -> str:
    return f"{currency}{Decimal(cents) * CENT:,.2f}"


def allocate(total_cents: int, weights: list[float | int]) -> list[int]:
    """Split `total_cents` in proportion to `weights` so that the parts are whole cents and sum exactly to the total.

    Largest remainder: give everyone the floor of their exact share, then hand the leftover cents one by one to
    whoever lost the most in rounding.
    """
    if not weights:
        return []
    weight_sum = sum(weights)
    if weight_sum == 0:
        weights, weight_sum = [1] * len(weights), len(weights)
    exact = [total_cents * w / weight_sum for w in weights]
    parts = [int(x) for x in exact]
    leftover = total_cents - sum(parts)
    by_remainder = sorted(range(len(weights)), key=lambda i: exact[i] - parts[i], reverse=True)
    for i in by_remainder[:leftover]:
        parts[i] += 1
    return parts


@dataclass(frozen=True)
class Item:
    name: str
    price_cents: int
    shared_by: tuple[str, ...] = ()        # empty = shared by everyone


@dataclass(frozen=True)
class Share:
    person: str
    subtotal: int
    tax: int
    tip: int

    @property
    def total(self) -> int:
        return self.subtotal + self.tax + self.tip


@dataclass
class Bill:
    people: list[str]
    items: list[Item] = field(default_factory=list)
    tax_percent: Decimal = Decimal("0")
    tip_percent: Decimal = Decimal("0")

    def __post_init__(self):
        names = [p.strip() for p in self.people if p.strip()]
        if not names:
            raise ValueError("Add at least one person.")
        if len({n.lower() for n in names}) != len(names):
            raise ValueError("People's names must be different.")
        self.people = names

    def add_item(self, name: str, price: Decimal | str, shared_by: tuple[str, ...] = ()) -> Item:
        unknown = [p for p in shared_by if p not in self.people]
        if unknown:
            raise ValueError(f"{', '.join(unknown)} isn't at the table.")
        item = Item(name.strip() or "item", to_cents(price), tuple(shared_by))
        self.items.append(item)
        return item

    @property
    def subtotal(self) -> int:
        return sum(i.price_cents for i in self.items)

    @property
    def tax(self) -> int:
        return round(self.subtotal * self.tax_percent / 100)

    @property
    def tip(self) -> int:
        return round(self.subtotal * self.tip_percent / 100)   # tip on the pre-tax amount, as is customary

    @property
    def total(self) -> int:
        return self.subtotal + self.tax + self.tip

    def shares(self) -> list[Share]:
        subtotals = dict.fromkeys(self.people, 0)
        for item in self.items:
            eaters = list(item.shared_by or self.people)
            for person, cents in zip(eaters, allocate(item.price_cents, [1] * len(eaters))):
                subtotals[person] += cents
        weights = [subtotals[p] for p in self.people]
        taxes, tips = allocate(self.tax, weights), allocate(self.tip, weights)
        return [Share(p, subtotals[p], t, tp) for p, t, tp in zip(self.people, taxes, tips)]

    def settle(self, payer: str) -> list[tuple[str, str, int]]:
        """Everyone pays back the person who paid the whole bill: (from, to, cents)."""
        if payer not in self.people:
            raise ValueError(f"{payer} isn't at the table.")
        return [(s.person, payer, s.total) for s in self.shares() if s.person != payer and s.total]


def parse_items(text: str, bill: Bill) -> None:
    """Lines like  'Pizza, 24.50'  or  'Wine, 30, Ana Ben'  (the last part lists who shared it)."""
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            raise ValueError(f"Line {number}: write 'name, price' (and optionally ', who shared it').")
        sharers = tuple(parts[2].split()) if len(parts) > 2 and parts[2] else ()
        try:
            bill.add_item(parts[0], parts[1], sharers)
        except ValueError as error:
            raise ValueError(f"Line {number}: {error}") from None
