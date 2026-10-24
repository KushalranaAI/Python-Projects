from decimal import Decimal

import pytest

from projects.beginner.bill_splitter.bill import Bill, allocate, format_cents, parse_items, to_cents


@pytest.mark.parametrize("total, weights, expected", [
    (100, [1, 1, 1], [34, 33, 33]), (10, [1, 1, 1, 1], [3, 3, 2, 2]), (0, [1, 2], [0, 0]),
    (1001, [1, 0], [1001, 0]), (5, [0, 0], [3, 2]),
])
def test_allocate_sums_exactly(total, weights, expected):
    parts = allocate(total, weights)
    assert parts == expected and sum(parts) == total


def test_allocate_with_nobody_returns_nothing():
    assert allocate(7, []) == []


def test_money_parsing():
    assert to_cents("24.50") == 2450 and to_cents(Decimal("0.1")) + to_cents("0.2") == 30
    with pytest.raises(ValueError):
        to_cents("abc")
    with pytest.raises(ValueError):
        to_cents("-1")
    assert format_cents(123456) == "$1,234.56"


def make_bill() -> Bill:
    bill = Bill(["Ana", "Ben", "Chloe"], tax_percent=Decimal("10"), tip_percent=Decimal("20"))
    bill.add_item("Pizza", "30")                  # everyone: 10 each
    bill.add_item("Wine", "20", ("Ana", "Chloe"))  # 10 each
    return bill


def test_shared_items_and_proportional_tax_tip():
    bill = make_bill()
    shares = {s.person: s for s in bill.shares()}
    assert shares["Ana"].subtotal == 2000 and shares["Ben"].subtotal == 1000
    assert bill.tax == 500 and bill.tip == 1000
    assert shares["Ana"].tax == 200 and shares["Ben"].tip == 200
    assert sum(s.total for s in shares.values()) == bill.total == 6500


def test_shares_always_add_up_even_with_awkward_cents():
    bill = Bill(["A", "B", "C"], tax_percent=Decimal("7.25"), tip_percent=Decimal("18"))
    bill.add_item("x", "10.01")
    bill.add_item("y", "3.33", ("A", "B"))
    assert sum(s.total for s in bill.shares()) == bill.total


def test_validation():
    with pytest.raises(ValueError):
        Bill([])
    with pytest.raises(ValueError):
        Bill(["Ana", "ana"])
    with pytest.raises(ValueError):
        make_bill().add_item("Cake", "5", ("Zoe",))


def test_settle_up():
    assert make_bill().settle("Ana") == [("Ben", "Ana", 1300), ("Chloe", "Ana", 2600)]


def test_parse_items_reports_line_numbers():
    bill = Bill(["Ana", "Ben"])
    parse_items("Soup, 5\n\nBread, 2, Ben", bill)
    assert [i.name for i in bill.items] == ["Soup", "Bread"]
    with pytest.raises(ValueError, match="Line 2"):
        parse_items("ok, 1\nbroken", Bill(["Ana"]))
