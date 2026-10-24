---
title: Bill Splitter
order: 6
icon: 🧾
time: 2 hours
summary: Split a restaurant bill with shared items, tax and tip, so the shares add up exactly to the cent. You'll learn why floats are wrong for money and how to fix it.
python_skills:
  - decimal.Decimal and why floats can't represent money
  - Integer cents arithmetic
  - Parsing multi-line text input
  - zip, dict.fromkeys, enumerate(start=1)
oop_concepts:
  - Dataclasses with computed properties (subtotal, tax, total)
  - Small immutable records (Item, Share)
  - Validation in __post_init__
  - Pure helper functions next to the class
clean_code:
  - Choose the right representation for the domain (cents as int)
  - An algorithm with a name and a docstring (largest remainder)
  - Error messages that point to the exact input line
  - Tests that assert invariants ("shares always sum to the total")
features:
  - Items shared by everyone or by a named subset
  - Tax and tip split in proportion to what each person ordered
  - Exact rounding - the shares always equal the total
  - A "settle up" list - who owes the person who paid
architecture: |
  classDiagram
    class Bill {
      +people list~str~
      +items list~Item~
      +tax_percent Decimal
      +tip_percent Decimal
      +add_item(name, price, shared_by) Item
      +subtotal int
      +tax int
      +tip int
      +total int
      +shares() list~Share~
      +settle(payer) list
    }
    class Item {
      <<frozen>>
      +name str
      +price_cents int
      +shared_by tuple
    }
    class Share {
      <<frozen>>
      +person str
      +subtotal int
      +tax int
      +tip int
      +total int
    }
    Bill "1" *-- "*" Item
    Bill ..> Share : computes
    Bill ..> allocate : uses
flow: |
  flowchart LR
    I[items] -->|"allocate price among sharers"| S[subtotal per person]
    S -->|"weights"| T["allocate(tax)"]
    S -->|"weights"| P["allocate(tip)"]
    S & T & P --> R["shares: sum == bill.total ✔"]
steps:
  - title: See the float problem for yourself
    body: |
      In a Python shell: `0.1 + 0.2` → `0.30000000000000004`, and `100 / 3 * 3` happens to give back `100.0`, but rounding each
      third to 2 decimals gives 33.33 × 3 = 99.99. A cent has gone missing. Binary floats can't store 0.1 exactly. Money needs
      exact arithmetic: **Decimal** for input, **integer cents** for calculation.
  - title: Write `allocate`, the heart of the project
    files: [bill.py, tests/test_bill.py]
    body: |
      Splitting 100 cents three ways: give everyone ⌊33.3⌋ = 33, so 1 cent is left over. Give it to whoever has the largest
      remainder. This **largest-remainder method** is also used to share seats in parliaments. Test it with a parametrised
      table and assert that `sum(parts) == total`, always.
  - title: Model items, shares and the bill
    files: [bill.py]
    body: |
      `Item` and `Share` are frozen records. `Bill` validates its people (non-empty, unique names) in `__post_init__`,
      and `subtotal`, `tax`, `tip` and `total` are properties. There's nothing to keep in sync.
  - title: Compute fair shares
    files: [bill.py]
    body: |
      `shares()` first splits each item among the people who shared it, then splits tax and tip **in proportion** to each
      subtotal (whoever ordered more pays more tip), using `allocate` both times. The invariant test proves the shares
      always add up.
  - title: Parse friendly input, report precise errors
    files: [bill.py]
    body: |
      `parse_items` reads lines like `Wine, 30, Ana Chloe`. When something's wrong it raises
      `ValueError("Line 3: Zoe isn't at the table.")`, an error message the user can act on.
  - title: A stateless web form
    files: [web.py, templates/bill_splitter/index.html]
    body: |
      No session, no storage: every submit rebuilds the `Bill` from the form. The template calls `money()`
      (`format_cents`) so formatting rules live in Python. Pre-filled example data shows how the input works.
exercises:
  - Support **percent discounts** on single items ("Pizza, 24.50, , -10%").
  - Let several people **each pay part** of the bill, then compute the minimum set of transfers to settle everyone.
  - Add **currencies** with a `Money(cents, currency)` value object that refuses to add USD to EUR.
  - 'Write a **property-based test** with `hypothesis`: for any random weights and total, `allocate` sums to the total.'
---

## Floats vs. Decimal vs. cents

| Representation | `0.10 + 0.20` | Good for money? |
|---|---|---|
| `float` | 0.30000000000000004 | ❌ rounding errors accumulate |
| `Decimal("0.10")` | 0.30 | ✅ exact decimal arithmetic |
| `int` cents | 10 + 20 = 30 | ✅ exact and fast; format only for display |

Banks, payment APIs (Stripe uses integer cents) and accounting software all use one of the last two.
