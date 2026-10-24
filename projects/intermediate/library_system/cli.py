"""Terminal interface: a menu over the Library's operations."""

from __future__ import annotations

from datetime import date

from projects.ui_kit import data_path

from . import storage
from .library import LibraryError

MENU = "[s]earch  [c]heckout  [r]eturn  [h]old  [o]verdue  [m]embers  [q]uit"


def main() -> None:
    path = data_path("library.json")
    lib = storage.load(path)
    today = date.today()
    print(f"📚 Library - {len(lib.items)} items, {len(lib.members)} members")
    while (choice := input(f"\n{MENU}\n> ").strip().lower()) != "q":
        try:
            if choice == "s":
                for item in lib.search(input("Search: ")):
                    status = "available" if lib.is_available(item.id) else "on loan"
                    print(f"  [{item.id}] {item.describe()} · {status if item.can_borrow else 'reference only'}")
            elif choice == "c":
                loan = lib.checkout(input("Item id: ").strip().upper(), input("Member id: ").strip().upper(), today)
                print(f"Due back on {loan.due_on:%A %d %B}.")
            elif choice == "r":
                fine = lib.return_item(input("Item id: ").strip().upper(), today)
                print(f"Returned.{f' Late fine: ${fine / 100:.2f}' if fine else ''}")
            elif choice == "h":
                print(f"Position in queue: {lib.place_hold(input('Item id: ').strip().upper(), input('Member id: ').strip().upper())}")
            elif choice == "o":
                for loan, fine in lib.overdue(today):
                    print(f"  {lib.item(loan.item_id).title} - {lib.member(loan.member_id).name}, due {loan.due_on}, fine ${fine / 100:.2f}")
            elif choice == "m":
                for m in lib.members.values():
                    print(f"  [{m.id}] {m.name}: {len(lib.loans_of(m.id))}/{m.max_loans} items, owes ${m.fines_cents / 100:.2f}")
            storage.save(lib, path)
        except LibraryError as error:
            print("  ✗", error)


if __name__ == "__main__":
    main()
