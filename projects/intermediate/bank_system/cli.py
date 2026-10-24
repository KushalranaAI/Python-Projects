"""Terminal interface: an ATM-style menu."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from projects.ui_kit import data_path

from . import storage
from .accounts import BankError

MENU = "[o]pen  [d]eposit  [w]ithdraw  [t]ransfer  [s]tatement  [l]ist  [m]onth-end  [q]uit"


def cents(text: str) -> int:
    return int(Decimal(text) * 100)


def main() -> None:
    path = data_path("bank.json")
    bank = storage.load(path)
    print(f"🏦 {bank.name}")
    while (choice := input(f"\n{MENU}\n> ").strip().lower()) != "q":
        now = datetime.now()
        try:
            if choice == "o":
                acc = bank.open_account(input("Type (checking/savings): ").strip(), input("Owner: "))
                print(f"Opened {acc.number}")
            elif choice == "d":
                print(bank.get(input("Account: ").strip()).deposit(cents(input("Amount: ")), now))
            elif choice == "w":
                print(bank.get(input("Account: ").strip()).withdraw(cents(input("Amount: ")), now))
            elif choice == "t":
                bank.transfer(input("From: ").strip(), input("To: ").strip(), cents(input("Amount: ")), now)
                print("Done.")
            elif choice == "s":
                for t in bank.get(input("Account: ").strip()).statement():
                    print(f"  {t.at:%Y-%m-%d} {t.kind.value:<13} {t.amount / 100:>10,.2f}  → {t.balance_after / 100:>10,.2f}  {t.memo}")
            elif choice == "l":
                for a in bank.accounts:
                    print(f"  {a.number}  {a.kind:<9} {a.owner:<15} ${a.balance / 100:,.2f}")
            elif choice == "m":
                for acc, tx in bank.run_month_end(now):
                    print(f"  {acc.number}: {tx.kind.value} {tx.amount / 100:+,.2f}")
            storage.save(bank, path)
        except (BankError, ValueError, ArithmeticError) as error:
            print("  ✗", error)


if __name__ == "__main__":
    main()
