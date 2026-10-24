"""A tiny publish/subscribe event bus (the Observer pattern) and the subscribers that react to order events.

The checkout code just announces "an order was placed". It doesn't know - or care - that this updates stock,
sends an email and writes an audit log. New reactions are added by subscribing, without touching checkout.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .catalog import ShopError


@dataclass(frozen=True)
class Event:
    name: str                 # "order.placed", "order.paid", …
    order_id: int
    at: datetime
    data: dict


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, name: str, handler: Handler) -> None:
        """name may be an exact event or "*" for everything."""
        self._handlers[name].append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers[event.name] + self._handlers["*"]:
            handler(event)


class Inventory:
    """Reserves stock when an order is placed and puts it back when the order is cancelled or refunded."""

    def __init__(self, stock: dict[str, int]):
        self.stock = dict(stock)

    def available(self, sku: str) -> int:
        return self.stock.get(sku, 0)

    def check(self, lines: dict[str, int]) -> None:
        short = [sku for sku, qty in lines.items() if qty > self.available(sku)]
        if short:
            raise ShopError(f"Not enough stock for: {', '.join(short)}.")

    def on_placed(self, event: Event) -> None:
        for sku, qty in event.data["lines"].items():
            self.stock[sku] -= qty

    def on_released(self, event: Event) -> None:
        for sku, qty in event.data["lines"].items():
            self.stock[sku] += qty


class Mailer:
    """Pretend email: messages land in an outbox list you can inspect (and test)."""

    TEMPLATES = {"order.placed": "Thanks! We received order #{id}.", "order.paid": "Payment received for order #{id}.",
                 "order.shipped": "Order #{id} is on its way 🚚", "order.delivered": "Order #{id} was delivered. Enjoy!",
                 "order.cancelled": "Order #{id} was cancelled.", "order.refunded": "Order #{id} has been refunded."}

    def __init__(self):
        self.outbox: list[str] = []

    def __call__(self, event: Event) -> None:
        template = self.TEMPLATES.get(event.name)
        if template:
            self.outbox.append(template.format(id=event.order_id))


class AuditLog:
    def __init__(self):
        self.entries: list[str] = []

    def __call__(self, event: Event) -> None:
        self.entries.append(f"{event.at:%H:%M:%S} {event.name} #{event.order_id}")
