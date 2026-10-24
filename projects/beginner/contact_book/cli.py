"""Terminal interface: a small menu loop."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from projects.ui_kit import data_path

from .contacts import Contact, ValidationError
from .storage import JsonContactStore

MENU = "[a]dd  [s]earch  [l]ist  [d]elete  [b]irthdays  [e]xport csv  [q]uit"


def show(c: Contact) -> None:
    star = "★ " if c.favorite else ""
    print(f"  {star}{c.name}  {c.email}  {c.phone}  {c.company}  {' '.join('#' + t for t in c.tags)}  [{c.id}]")


def main() -> None:
    store = JsonContactStore(data_path("contacts.json"))
    book = store.load()
    print(f"📇 Contact Book - {len(book)} contacts")
    while (choice := input(f"\n{MENU}\n> ").strip().lower()) != "q":
        if choice == "a":
            try:
                birthday = input("Birthday (YYYY-MM-DD, optional): ").strip()
                book.add(Contact(input("Name: "), input("Email: "), input("Phone: "), input("Company: "),
                                 date.fromisoformat(birthday) if birthday else None, input("Tags (comma separated): ").split(",")))
                store.save(book)
                print("Saved.")
            except ValidationError as error:
                for field_name, message in error.errors.items():
                    print(f"  ✗ {field_name} {message}")
            except ValueError as error:
                print(f"  ✗ {error}")
        elif choice in {"s", "l"}:
            for c in book.search(input("Search: ") if choice == "s" else ""):
                show(c)
        elif choice == "d":
            try:
                print("Deleted", book.remove(input("Contact id: ").strip()).name)
                store.save(book)
            except LookupError:
                print("No contact with that id.")
        elif choice == "b":
            for c, days in book.upcoming_birthdays(date.today()):
                print(f"  {c.name}: {'today! 🎂' if days == 0 else f'in {days} days'}")
        elif choice == "e":
            path = Path("contacts.csv")
            path.write_text(book.to_csv(), encoding="utf-8")
            print(f"Wrote {path.resolve()}")


if __name__ == "__main__":
    main()
