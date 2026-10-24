from datetime import datetime

import pytest

from projects.advanced.online_shop.catalog import Cart, ShopError
from projects.advanced.online_shop.discounts import COUPONS, BuyXGetYFree, CategoryPercentOff, FixedOff, PercentOff, best_discount
from projects.advanced.online_shop.events import Event, EventBus
from projects.advanced.online_shop.orders import IllegalTransition, Status
from projects.advanced.online_shop.shop import SHIPPING_FEE, Shop

NOW = datetime(2026, 5, 1, 12, 0)


@pytest.fixture
def shop() -> Shop:
    return Shop()


def cart_with(shop, **qty) -> Cart:
    c = Cart()
    for sku, n in qty.items():
        c.add(shop.products[sku.upper()], n)
    return c


def test_discount_strategies(shop):
    c = cart_with(shop, mug=3, book=1)                        # 3 × 12 + 35 = 71
    p = shop.products
    assert PercentOff("X", 10).amount(c, p) == 710
    assert PercentOff("X", 20, min_subtotal=10_000).amount(c, p) == 0
    assert CategoryPercentOff("X", "books", 25).amount(c, p) == 875
    assert BuyXGetYFree("X", "MUG", 2, 1).amount(c, p) == 1200
    assert FixedOff("X", 1500, 6000).amount(c, p) == 1500


def test_best_coupon_wins_and_unknown_codes_are_ignored(shop):
    c = cart_with(shop, mug=3, book=1)
    discount, amount = best_discount(c, shop.products, ["WELCOME10", "TAKE15", "MUG3FOR2", "NOPE"])
    assert discount.code == "TAKE15" and amount == 1500


def test_quote_and_free_shipping(shop):
    small = shop.quote(cart_with(shop, stickers=1), [])
    assert small["shipping"] == SHIPPING_FEE and small["free_shipping_gap"] == 4500
    big = shop.quote(cart_with(shop, keyboard=1), ["WELCOME10"])
    assert big["shipping"] == 0 and big["total"] == 8900 - 890


def test_place_order_reserves_stock_and_sends_mail(shop):
    order = shop.place_order(cart_with(shop, hoodie=2), [], NOW)
    assert order.status is Status.PENDING and shop.inventory.available("HOODIE") == 8
    assert shop.mailer.outbox == ["Thanks! We received order #1."]


def test_out_of_stock_and_empty_cart(shop):
    with pytest.raises(ShopError, match="stock"):
        shop.place_order(cart_with(shop, mug=11), [], NOW)
    with pytest.raises(ShopError, match="empty"):
        shop.place_order(Cart(), [], NOW)


def test_state_machine_happy_path(shop):
    order = shop.place_order(cart_with(shop, mug=1), [], NOW)
    for action in ("pay", "ship", "deliver"):
        shop.act(order.id, action, NOW)
    assert order.status is Status.DELIVERED and [s for s, _ in order.history][-1] is Status.DELIVERED
    assert order.allowed_actions == ["return"]


def test_illegal_transitions_raise(shop):
    order = shop.place_order(cart_with(shop, mug=1), [], NOW)
    with pytest.raises(IllegalTransition):
        shop.act(order.id, "ship", NOW)                       # can't ship before paying
    shop.act(order.id, "cancel", NOW)
    with pytest.raises(IllegalTransition):
        shop.act(order.id, "pay", NOW)


def test_cancel_and_refund_release_stock(shop):
    a = shop.place_order(cart_with(shop, tshirt=3), [], NOW)
    b = shop.place_order(cart_with(shop, tshirt=2), [], NOW)
    shop.act(a.id, "cancel", NOW)
    shop.act(b.id, "pay", NOW)
    shop.act(b.id, "cancel", NOW)                                # paid → refunded
    assert b.status is Status.REFUNDED and shop.inventory.available("TSHIRT") == 10


def test_event_bus_wildcard_and_order():
    bus, seen = EventBus(), []
    bus.subscribe("a", lambda e: seen.append(("a", e.name)))
    bus.subscribe("*", lambda e: seen.append(("*", e.name)))
    bus.publish(Event("a", 1, NOW, {}))
    bus.publish(Event("b", 1, NOW, {}))
    assert seen == [("a", "a"), ("*", "a"), ("*", "b")]


def test_all_coupons_have_descriptions():
    assert all(d.description for d in COUPONS.values())
