from datetime import date, timedelta

import pytest

from projects.intermediate.library_system import storage
from projects.intermediate.library_system.items import DVD, Book, LibraryItem, Magazine, ReferenceBook, isbn13_is_valid, item_from_dict
from projects.intermediate.library_system.library import (Library, LoanLimitError, Member, NotBorrowableError, UnavailableError,
                                                           UnpaidFinesError)

DAY0 = date(2026, 3, 1)


@pytest.fixture
def lib() -> Library:
    return storage.sample_library()


def test_isbn_checksum():
    assert isbn13_is_valid("978-0-13-235088-4") and not isbn13_is_valid("9780132350885")
    with pytest.raises(ValueError):
        Book("X", "Bad", 2000, "Someone", "1234567890123")


def test_abstract_base_cannot_be_created():
    with pytest.raises(TypeError):
        LibraryItem("X", "Thing", 2000)


def test_subclasses_override_rules():
    book, dvd, mag = Book("1", "b", 2000, "a"), DVD("2", "d", 2000, "x", 90), Magazine("3", "m", 2026, "May")
    assert (book.loan_days, dvd.loan_days, mag.loan_days) == (14, 7, 7)
    assert ReferenceBook("4", "r", 2000, "p").can_borrow is False and book.can_borrow
    assert isinstance(ReferenceBook("4", "r", 2000, "p"), Book)
    assert "dir. x" in dvd.describe()


def test_checkout_uses_each_items_loan_period(lib):
    assert lib.checkout("B1", "U1", DAY0).due_on == DAY0 + timedelta(days=14)
    assert lib.checkout("D1", "U1", DAY0).due_on == DAY0 + timedelta(days=7)


def test_rules(lib):
    lib.checkout("B1", "U1", DAY0)
    with pytest.raises(UnavailableError):
        lib.checkout("B1", "U2", DAY0)
    with pytest.raises(NotBorrowableError):
        lib.checkout("R1", "U2", DAY0)
    lib.checkout("B2", "U1", DAY0)
    lib.checkout("B3", "U1", DAY0)
    with pytest.raises(LoanLimitError):
        lib.checkout("B4", "U1", DAY0)


def test_late_return_charges_fine_and_blocks_borrowing(lib):
    lib.checkout("D1", "U3", DAY0)                       # DVD: 7 days, $1/day
    fine = lib.return_item("D1", DAY0 + timedelta(days=13))
    assert fine == 600 and lib.member("U3").fines_cents == 600
    with pytest.raises(UnpaidFinesError):
        lib.checkout("B1", "U3", DAY0)
    lib.pay_fine("U3", 600)
    lib.checkout("B1", "U3", DAY0)


def test_overdue_report(lib):
    lib.checkout("B1", "U1", DAY0)
    lib.checkout("M1", "U2", DAY0)
    report = lib.overdue(DAY0 + timedelta(days=10))
    assert [(loan.item_id, fine) for loan, fine in report] == [("M1", 30)]


def test_holds_reserve_the_item_for_the_first_in_line(lib):
    lib.checkout("B1", "U1", DAY0)
    assert lib.place_hold("B1", "U2") == 1
    lib.return_item("B1", DAY0)
    with pytest.raises(UnavailableError):
        lib.checkout("B1", "U3", DAY0)
    lib.checkout("B1", "U2", DAY0)
    assert lib.next_in_line("B1") is None


def test_search(lib):
    assert [i.id for i in lib.search("python")] == ["B1", "B3", "M1"]          # sorted by title
    assert [i.id for i in lib.search(kind="dvd")] == ["D2", "D1"]
    lib.checkout("D1", "U1", DAY0)
    assert [i.id for i in lib.search(kind="dvd", available_only=True)] == ["D2"]


def test_polymorphic_round_trip(tmp_path, lib):
    lib.checkout("B1", "U1", DAY0)
    lib.place_hold("B1", "U2")
    storage.save(lib, tmp_path / "lib.json")
    again = storage.load(tmp_path / "lib.json")
    assert {type(i) for i in again.items.values()} == {Book, ReferenceBook, DVD, Magazine}
    assert again.items == lib.items and again.loans == lib.loans and list(again.holds["B1"]) == ["U2"]


def test_item_from_dict_picks_the_class():
    assert isinstance(item_from_dict({"type": "dvd", "id": "D", "title": "t", "year": 2000, "director": "d", "minutes": 1}), DVD)
