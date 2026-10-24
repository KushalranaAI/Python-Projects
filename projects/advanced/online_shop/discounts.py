"""Discounts as interchangeable strategy objects. Each one inspects the cart and returns how much it takes off."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .catalog import Cart, Product


class Discount(ABC):
    code: str
    description: str

    @abstractmethod
    def amount(self, cart: Cart, products: dict[str, Product]) -> int:
        """Cents off (0 if the conditions aren't met)."""

    def applies(self, cart: Cart, products: dict[str, Product]) -> bool:
        return self.amount(cart, products) > 0


@dataclass(frozen=True)
class PercentOff(Discount):
    code: str
    percent: int
    min_subtotal: int = 0

    @property
    def description(self) -> str:
        minimum = f" on orders over ${self.min_subtotal / 100:.0f}" if self.min_subtotal else ""
        return f"{self.percent}% off{minimum}"

    def amount(self, cart, products):
        subtotal = cart.subtotal(products)
        return subtotal * self.percent // 100 if subtotal >= self.min_subtotal else 0


@dataclass(frozen=True)
class CategoryPercentOff(Discount):
    code: str
    category: str
    percent: int

    @property
    def description(self) -> str:
        return f"{self.percent}% off {self.category}"

    def amount(self, cart, products):
        return sum(p.price * q for p, q in cart.items(products) if p.category == self.category) * self.percent // 100


@dataclass(frozen=True)
class BuyXGetYFree(Discount):
    code: str
    sku: str
    buy: int
    free: int

    @property
    def description(self) -> str:
        return f"buy {self.buy} {self.sku.lower()}, get {self.free} free"

    def amount(self, cart, products):
        quantity = cart.lines.get(self.sku, 0)
        groups = quantity // (self.buy + self.free)
        return groups * self.free * products[self.sku].price if self.sku in products else 0


@dataclass(frozen=True)
class FixedOff(Discount):
    code: str
    cents: int
    min_subtotal: int

    @property
    def description(self) -> str:
        return f"${self.cents / 100:.0f} off orders over ${self.min_subtotal / 100:.0f}"

    def amount(self, cart, products):
        subtotal = cart.subtotal(products)
        return min(self.cents, subtotal) if subtotal >= self.min_subtotal else 0


COUPONS: dict[str, Discount] = {d.code: d for d in [
    PercentOff("WELCOME10", 10), PercentOff("BIG20", 20, min_subtotal=10_000), CategoryPercentOff("READ25", "books", 25),
    BuyXGetYFree("MUG3FOR2", "MUG", 2, 1), FixedOff("TAKE15", 1500, min_subtotal=6000),
]}


def best_discount(cart: Cart, products: dict[str, Product], codes: list[str]) -> tuple[Discount | None, int]:
    """Coupons don't stack: pick the single best one for the customer among the codes they entered."""
    candidates = [(COUPONS[c], COUPONS[c].amount(cart, products)) for c in codes if c in COUPONS]
    best = max(candidates, key=lambda pair: pair[1], default=(None, 0))
    return best if best[1] > 0 else (None, 0)
