"""The facade that wires everything together: catalog, inventory, coupons, orders and the event bus."""

from __future__ import annotations

from datetime import datetime

from .catalog import CATALOG, Cart, Product, ShopError
from .discounts import best_discount
from .events import AuditLog, Event, EventBus, Inventory, Mailer
from .orders import Order, OrderLine, Status

FREE_SHIPPING_FROM = 5000
SHIPPING_FEE = 499
RELEASES_STOCK = {Status.CANCELLED, Status.REFUNDED}


class Shop:
    def __init__(self, products: list[Product] | None = None, stock: dict[str, int] | None = None):
        self.products = {p.sku: p for p in products or CATALOG}
        self.inventory = Inventory(stock or {sku: 10 for sku in self.products})
        self.orders: dict[int, Order] = {}
        self.bus, self.mailer, self.audit = EventBus(), Mailer(), AuditLog()
        self.bus.subscribe("order.placed", self.inventory.on_placed)
        for name in ("order.cancelled", "order.refunded"):
            self.bus.subscribe(name, self.inventory.on_released)
        self.bus.subscribe("*", self.mailer)
        self.bus.subscribe("*", self.audit)

    def quote(self, cart: Cart, codes: list[str]) -> dict:
        subtotal = cart.subtotal(self.products)
        discount_obj, discount = best_discount(cart, self.products, codes)
        shipping = 0 if cart.is_empty or subtotal - discount >= FREE_SHIPPING_FROM else SHIPPING_FEE
        return {"subtotal": subtotal, "discount": discount, "coupon": discount_obj, "shipping": shipping,
                "total": subtotal - discount + shipping, "free_shipping_gap": max(FREE_SHIPPING_FROM - (subtotal - discount), 0)}

    def place_order(self, cart: Cart, codes: list[str], at: datetime) -> Order:
        if cart.is_empty:
            raise ShopError("Your cart is empty.")
        self.inventory.check(cart.lines)
        q = self.quote(cart, codes)
        order = Order(id=len(self.orders) + 1,
                      lines=[OrderLine(p.sku, p.name, p.price, qty) for p, qty in cart.items(self.products)],
                      subtotal=q["subtotal"], discount=q["discount"], shipping=q["shipping"],
                      coupon=q["coupon"].code if q["coupon"] else None, history=[(Status.PENDING, at)])
        self.orders[order.id] = order
        self.bus.publish(Event("order.placed", order.id, at, {"lines": dict(cart.lines)}))
        return order

    def act(self, order_id: int, action: str, at: datetime) -> Order:
        order = self.orders.get(order_id)
        if order is None:
            raise ShopError(f"No order #{order_id}.")
        old, new = order.apply(action, at)
        data = {"lines": {line.sku: line.quantity for line in order.lines}} if new in RELEASES_STOCK else {}
        self.bus.publish(Event(f"order.{new.value}", order_id, at, data))
        return order
