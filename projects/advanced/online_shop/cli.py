"""Terminal demo: place an order with a coupon, then walk it through its life cycle."""

from __future__ import annotations

from datetime import datetime

from .catalog import Cart
from .discounts import COUPONS
from .shop import Shop


def money(c: int) -> str:
    return f"${c / 100:,.2f}"


def main() -> None:
    shop = Shop()
    cart = Cart()
    print("🛒 Products:")
    for p in shop.products.values():
        print(f"  {p.sku:<9} {p.icon} {p.name:<22} {money(p.price):>9}  stock {shop.inventory.available(p.sku)}")
    while (line := input("Add 'SKU qty' (empty to check out): ").strip()):
        try:
            sku, qty = (line.split() + ["1"])[:2]
            cart.add(shop.products[sku.upper()], int(qty))
        except (KeyError, ValueError) as error:
            print("  ✗", error)
    print("Coupons:", ", ".join(f"{c} ({d.description})" for c, d in COUPONS.items()))
    codes = input("Coupon codes (space separated): ").upper().split()
    q = shop.quote(cart, codes)
    print(f"Subtotal {money(q['subtotal'])} - discount {money(q['discount'])} + shipping {money(q['shipping'])} = {money(q['total'])}")
    order = shop.place_order(cart, codes, datetime.now())
    while order.allowed_actions:
        action = input(f"Order #{order.id} is {order.status.value}. Next ({'/'.join(order.allowed_actions)}, or q): ").strip()
        if action == "q":
            break
        try:
            shop.act(order.id, action, datetime.now())
        except Exception as error:
            print("  ✗", error)
    print("\nEmails sent:", *shop.mailer.outbox, sep="\n  ")


if __name__ == "__main__":
    main()
