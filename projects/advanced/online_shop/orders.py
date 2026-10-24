"""Orders follow a state machine: only the transitions in TRANSITIONS are allowed, everything else raises."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .catalog import ShopError


class Status(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


TRANSITIONS: dict[Status, dict[str, Status]] = {
    Status.PENDING: {"pay": Status.PAID, "cancel": Status.CANCELLED},
    Status.PAID: {"ship": Status.SHIPPED, "cancel": Status.REFUNDED},
    Status.SHIPPED: {"deliver": Status.DELIVERED},
    Status.DELIVERED: {"return": Status.REFUNDED},
    Status.CANCELLED: {},
    Status.REFUNDED: {},
}


class IllegalTransition(ShopError):
    pass


@dataclass(frozen=True)
class OrderLine:
    sku: str
    name: str
    unit_price: int
    quantity: int

    @property
    def total(self) -> int:
        return self.unit_price * self.quantity


@dataclass
class Order:
    id: int
    lines: list[OrderLine]
    subtotal: int
    discount: int
    shipping: int
    coupon: str | None
    status: Status = Status.PENDING
    history: list[tuple[Status, datetime]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.subtotal - self.discount + self.shipping

    @property
    def allowed_actions(self) -> list[str]:
        return list(TRANSITIONS[self.status])

    def apply(self, action: str, at: datetime) -> tuple[Status, Status]:
        """Move to the next state. Returns (old, new) so callers can publish an event."""
        try:
            new = TRANSITIONS[self.status][action]
        except KeyError:
            raise IllegalTransition(f"Can't {action} an order that is {self.status.value}.") from None
        old, self.status = self.status, new
        self.history.append((new, at))
        return old, new
