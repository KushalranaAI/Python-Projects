"""Terminal interface: answer a few questions, get everyone's share."""

from __future__ import annotations

from decimal import Decimal

from .bill import Bill, format_cents


def ask(prompt: str, default: str = "") -> str:
    return input(f"{prompt}{f' [{default}]' if default else ''}: ").strip() or default


def main() -> None:
    print("🧾 Bill Splitter")
    while True:
        try:
            bill = Bill(ask("Who's at the table? (names separated by spaces)").split(),
                        tax_percent=Decimal(ask("Tax %", "0")), tip_percent=Decimal(ask("Tip %", "15")))
            break
        except (ValueError, ArithmeticError) as error:
            print(error)
    print("Add items as 'name, price[, who shared it]'. Empty line to finish.")
    while line := input("item> ").strip():
        parts = [p.strip() for p in line.split(",")]
        try:
            bill.add_item(parts[0], parts[1], tuple(parts[2].split()) if len(parts) > 2 else ())
        except (ValueError, IndexError) as error:
            print("  ", error if str(error) else "Use: name, price[, names]")
    print(f"\nSubtotal {format_cents(bill.subtotal)} + tax {format_cents(bill.tax)} + tip {format_cents(bill.tip)} = {format_cents(bill.total)}")
    for share in bill.shares():
        print(f"  {share.person:<12} {format_cents(share.total):>10}")


if __name__ == "__main__":
    main()
