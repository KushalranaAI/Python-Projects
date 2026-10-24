---
title: Online Shop
order: 4
icon: 🛍️
time: 6-8 hours
summary: A small shop with a cart, five kinds of coupons, stock reservation and orders that move through pay → ship → deliver → return. Three classic design patterns working together - Strategy, State machine and Observer.
python_skills:
  - Callables as handlers (functions and objects with __call__)
  - collections.defaultdict(list) for subscriber lists
  - Integer cents and floor division for money
  - max(..., key=..., default=...)
  - Nested dicts as a transition table
oop_concepts:
  - Strategy pattern - Discount subclasses
  - State machine - allowed transitions as data
  - Observer pattern - EventBus with subscribers
  - Facade - Shop wires the subsystems together
  - Frozen dataclasses implementing an ABC
clean_code:
  - Rules as data (TRANSITIONS, COUPONS)
  - Loose coupling - checkout publishes events instead of calling inventory/mail directly
  - Validate before changing state (stock check before the order exists)
  - Every pattern has a focused test
features:
  - Product grid, cart with quantities, free shipping over $50
  - Coupons - percent off, percent off a category, buy 2 get 1 free, fixed amount - the best one applies
  - Orders with pay / ship / deliver / cancel / return actions, only when allowed
  - Stock reserved on order, released on cancel or refund
  - Live outbox (emails) and event log fed by subscribers
architecture: |
  classDiagram
    class Discount {
      <<abstract>>
      +code str
      +description str
      +amount(cart, products)* int
    }
    class PercentOff
    class CategoryPercentOff
    class BuyXGetYFree
    class FixedOff
    class Order {
      +status Status
      +lines list
      +total int
      +allowed_actions list
      +apply(action, at) tuple
    }
    class EventBus {
      -_handlers dict
      +subscribe(name, handler)
      +publish(event)
    }
    class Inventory {
      +stock dict
      +check(lines)
      +on_placed(event)
      +on_released(event)
    }
    class Mailer {
      +outbox list
      +__call__(event)
    }
    class AuditLog {
      +__call__(event)
    }
    class Shop {
      +products dict
      +orders dict
      +quote(cart, codes) dict
      +place_order(cart, codes, at) Order
      +act(order_id, action, at) Order
    }
    Discount <|-- PercentOff
    Discount <|-- CategoryPercentOff
    Discount <|-- BuyXGetYFree
    Discount <|-- FixedOff
    Shop --> EventBus
    Shop --> Inventory
    Shop *-- Order
    EventBus ..> Inventory : notifies
    EventBus ..> Mailer : notifies
    EventBus ..> AuditLog : notifies
flow: |
  stateDiagram-v2
    [*] --> pending : place_order
    pending --> paid : pay
    pending --> cancelled : cancel
    paid --> shipped : ship
    paid --> refunded : cancel
    shipped --> delivered : deliver
    delivered --> refunded : return
    cancelled --> [*]
    refunded --> [*]
steps:
  - title: Products and the cart
    files: [catalog.py]
    body: |
      The cart is just `{sku: quantity}`, which is small, serialisable and easy to store in a session. It computes its subtotal
      from the product table. Prices are integer cents.
  - title: Discounts as strategies
    files: [discounts.py]
    body: |
      `Discount` is an abstract class with one method, `amount(cart, products)`. Each coupon type is a frozen dataclass that
      implements it differently. `best_discount` doesn't care which types it gets: it computes all the amounts and keeps the
      best one. A new promotion is a new class, with no `if coupon_type == ...` anywhere.
  - title: The order state machine
    files: [orders.py]
    body: |
      `TRANSITIONS` lists, for each status, which actions are allowed and where they lead. `Order.apply` looks the action up
      and raises `IllegalTransition` otherwise. You can't ship an unpaid order, and you can't pay a cancelled one.
      The UI shows only `allowed_actions`.
  - title: Decouple with an event bus
    files: [events.py]
    body: |
      `EventBus.publish(Event("order.placed", ...))` calls every subscriber. `Inventory` reserves and releases stock,
      `Mailer` writes to an outbox, `AuditLog` records everything (it subscribes to `"*"`). Subscribers are any callables:
      bound methods, or objects with `__call__`.
  - title: The facade
    files: [shop.py]
    body: |
      `Shop` builds the parts and subscribes the handlers in its constructor. `place_order` checks stock **before** creating
      anything, then publishes `order.placed`. `act` applies a transition and publishes `order.<new status>`, attaching the
      lines when stock has to be released.
  - title: Test each pattern on its own
    files: [tests/test_shop.py]
    body: |
      One test per discount class, one for "best coupon wins", the full happy path, illegal transitions, stock round trips
      through cancel and refund, and the event bus's wildcard ordering.
  - title: The web UI
    files: [web.py, templates/online_shop/index.html]
    body: |
      The shop object lives in memory for the server's lifetime (restart = fresh stock). The cart and coupon codes live in
      the session. The outbox and event log panels show the subscribers working in real time.
exercises:
  - Add a `LoyaltyPoints` subscriber that gives 1 point per dollar on `order.delivered` and removes them on refund.
  - Let some coupons **stack** - add a `stackable` flag and apply all stackable discounts plus the best non-stackable one.
  - Add a `partially_shipped` state for multi-parcel orders. Only the transition table and tests should change.
  - Persist orders and stock to SQLite, publishing events *after* the transaction commits. Why does that ordering matter?
---

## Three patterns, one checkout

| Pattern | Where | What it buys you |
|---|---|---|
| **Strategy** | `Discount` subclasses | new promotions without touching checkout code |
| **State machine** | `TRANSITIONS` + `Order.apply` | impossible states can't happen; the UI knows which buttons to show |
| **Observer** | `EventBus` + subscribers | checkout doesn't know about email, stock or logs, so each can change independently |
