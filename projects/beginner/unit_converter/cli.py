"""Terminal interface: "12 km to mi" style queries."""

from __future__ import annotations

import re

from .units import Category, IncompatibleUnitsError, UnknownUnitError, default_registry, format_number

QUERY = re.compile(r"^\s*(-?[\d.]+(?:e-?\d+)?)\s*(\S+)\s+(?:to|in)\s+(\S+)\s*$", re.I)


def main() -> None:
    registry = default_registry()
    print("📏 Unit Converter - type e.g. '12 km to mi', 'list', or 'quit'")
    while (line := input("> ").strip()).lower() not in {"quit", "exit", "q"}:
        if line.lower() == "list":
            for category in Category:
                print(f"  {category.value:<16} {', '.join(u.symbol for u in registry.units_in(category))}")
            continue
        match = QUERY.match(line)
        if not match:
            print("Format: <number> <unit> to <unit>")
            continue
        value, source, target = float(match[1]), match[2], match[3]
        try:
            print(f"  {format_number(value)} {source} = {format_number(registry.convert(value, source, target))} {target}")
        except (UnknownUnitError, IncompatibleUnitsError) as error:
            print(" ", error.args[0])


if __name__ == "__main__":
    main()
