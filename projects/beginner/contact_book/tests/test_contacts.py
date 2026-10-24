from datetime import date

import pytest

from projects.beginner.contact_book.contacts import Contact, ContactBook, ValidationError, normalize_phone
from projects.beginner.contact_book.storage import JsonContactStore


@pytest.fixture
def book() -> ContactBook:
    return ContactBook([
        Contact("Ada Lovelace", "ada@example.com", "+44 20 7946 0958", "Analytical Engines", date(1815, 12, 10), ["math", "vip"], True),
        Contact("alan turing", "ALAN@example.com", company="Bletchley", tags=["Math"]),
        Contact("Grace Hopper", phone="(555) 123-4567", birthday=date(1906, 12, 9)),
    ])


def test_fields_are_normalised(book):
    alan = book.search("turing")[0]
    assert alan.email == "alan@example.com" and alan.tags == ["math"] and alan.initials == "AT"
    assert normalize_phone("(555) 123-4567") == "5551234567" and normalize_phone("+44 20") == "+4420"


@pytest.mark.parametrize("kwargs, field", [({"name": " "}, "name"), ({"name": "X", "email": "nope"}, "email"),
                                            ({"name": "X", "phone": "abc"}, "phone"),
                                            ({"name": "X", "birthday": date(2999, 1, 1)}, "birthday")])
def test_validation_reports_each_field(kwargs, field):
    with pytest.raises(ValidationError) as info:
        Contact(**kwargs)
    assert field in info.value.errors


def test_iteration_puts_favourites_first(book):
    assert [c.name for c in book] == ["Ada Lovelace", "alan turing", "Grace Hopper"]


def test_search_matches_all_words_across_fields(book):
    assert [c.name for c in book.search("math vip")] == ["Ada Lovelace"]
    assert [c.name for c in book.search(tag="math")] == ["Ada Lovelace", "alan turing"]
    assert book.search("nobody") == []


def test_duplicates_are_rejected(book):
    with pytest.raises(ValidationError):
        book.add(Contact("Someone", "ada@example.com"))


def test_update_and_remove(book):
    ada = book.search("ada")[0]
    book.update(ada.id, company="Babbage & Co")
    assert book.get(ada.id).company == "Babbage & Co"
    book.remove(ada.id)
    assert len(book) == 2


def test_birthdays(book):
    upcoming = book.upcoming_birthdays(date(2026, 12, 1), within_days=10)
    assert [(c.name, d) for c, d in upcoming] == [("Grace Hopper", 8), ("Ada Lovelace", 9)]
    leap = Contact("Leap", birthday=date(2000, 2, 29))
    assert leap.days_until_birthday(date(2027, 2, 28)) == 1


def test_csv_round_trip_with_errors(book):
    text = book.to_csv() + "Bad Row,not-an-email,,,,,\n"
    fresh = ContactBook()
    added, problems = fresh.import_csv(text)
    assert added == 3 and len(problems) == 1 and "line 5" in problems[0]
    assert {c.name for c in fresh} == {c.name for c in book}


def test_json_store_round_trip(tmp_path, book):
    store = JsonContactStore(tmp_path / "c.json")
    store.save(book)
    assert [c.to_dict() for c in store.load()] == [c.to_dict() for c in book]
