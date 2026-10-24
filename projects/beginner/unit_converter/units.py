"""A data-driven unit converter: every unit is a row in a table, not a branch in an if/elif chain.

Every unit converts to its category's *base unit* with  base = value × factor + offset.
Converting A → B is then: to base with A, from base with B. Adding a unit means adding one line.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(Enum):
    LENGTH = "Length"
    MASS = "Mass"
    TEMPERATURE = "Temperature"
    VOLUME = "Volume"
    SPEED = "Speed"
    DATA = "Digital storage"
    TIME = "Time"


@dataclass(frozen=True)
class Unit:
    symbol: str
    name: str
    category: Category
    factor: float          # how many base units one of this unit is
    offset: float = 0.0    # only temperatures need an offset

    def to_base(self, value: float) -> float:
        return value * self.factor + self.offset

    def from_base(self, value: float) -> float:
        return (value - self.offset) / self.factor


class UnknownUnitError(KeyError):
    """Raised for a symbol the registry doesn't know."""


class IncompatibleUnitsError(ValueError):
    """Raised when converting between categories, e.g. metres to kilograms."""


class UnitRegistry:
    """Holds the units and performs conversions between them."""

    def __init__(self, units: list[Unit]):
        self._units: dict[str, Unit] = {}
        for unit in units:
            self.add(unit)

    def add(self, unit: Unit) -> None:
        if unit.symbol in self._units:
            raise ValueError(f"duplicate unit symbol {unit.symbol!r}")
        self._units[unit.symbol] = unit

    def get(self, symbol: str) -> Unit:
        try:
            return self._units[symbol]
        except KeyError:
            raise UnknownUnitError(f"unknown unit {symbol!r}") from None

    def units_in(self, category: Category) -> list[Unit]:
        return [u for u in self._units.values() if u.category is category]

    def convert(self, value: float, from_symbol: str, to_symbol: str) -> float:
        source, target = self.get(from_symbol), self.get(to_symbol)
        if source.category is not target.category:
            raise IncompatibleUnitsError(f"can't convert {source.category.value.lower()} to {target.category.value.lower()}")
        return target.from_base(source.to_base(value))

    def convert_to_all(self, value: float, from_symbol: str) -> dict[str, float]:
        """The same quantity expressed in every unit of its category - handy for a results table."""
        source = self.get(from_symbol)
        return {u.symbol: self.convert(value, from_symbol, u.symbol) for u in self.units_in(source.category)}


def format_number(x: float, significant: int = 6) -> str:
    """6 significant digits, no scientific notation for everyday sizes, and no trailing zeros."""
    if x == 0:
        return "0"
    if 1e-4 <= abs(x) < 1e12:
        text = f"{x:.{significant}g}" if abs(x) < 10**significant else f"{x:,.0f}"
        return text if "e" not in text else f"{x:.{significant}f}".rstrip("0").rstrip(".")
    return f"{x:.{significant - 1}e}"


L, M, T, V, S, D, TI = (Category.LENGTH, Category.MASS, Category.TEMPERATURE, Category.VOLUME, Category.SPEED,
                        Category.DATA, Category.TIME)
DEFAULT_UNITS = [
    Unit("mm", "millimetre", L, 0.001), Unit("cm", "centimetre", L, 0.01), Unit("m", "metre", L, 1),
    Unit("km", "kilometre", L, 1000), Unit("in", "inch", L, 0.0254), Unit("ft", "foot", L, 0.3048),
    Unit("yd", "yard", L, 0.9144), Unit("mi", "mile", L, 1609.344),
    Unit("mg", "milligram", M, 1e-6), Unit("g", "gram", M, 0.001), Unit("kg", "kilogram", M, 1),
    Unit("t", "tonne", M, 1000), Unit("oz", "ounce", M, 0.028349523125), Unit("lb", "pound", M, 0.45359237),
    Unit("°C", "Celsius", T, 1), Unit("K", "Kelvin", T, 1, -273.15), Unit("°F", "Fahrenheit", T, 5 / 9, -160 / 9),
    Unit("ml", "millilitre", V, 0.001), Unit("l", "litre", V, 1), Unit("m³", "cubic metre", V, 1000),
    Unit("cup", "US cup", V, 0.2365882365), Unit("gal", "US gallon", V, 3.785411784),
    Unit("m/s", "metres per second", S, 1), Unit("km/h", "kilometres per hour", S, 1 / 3.6),
    Unit("mph", "miles per hour", S, 0.44704), Unit("kn", "knot", S, 1852 / 3600),
    Unit("B", "byte", D, 1), Unit("KB", "kilobyte", D, 1e3), Unit("MB", "megabyte", D, 1e6), Unit("GB", "gigabyte", D, 1e9),
    Unit("KiB", "kibibyte", D, 1024), Unit("MiB", "mebibyte", D, 1024**2), Unit("GiB", "gibibyte", D, 1024**3),
    Unit("s", "second", TI, 1), Unit("min", "minute", TI, 60), Unit("h", "hour", TI, 3600),
    Unit("day", "day", TI, 86400), Unit("week", "week", TI, 604800),
]


def default_registry() -> UnitRegistry:
    return UnitRegistry(DEFAULT_UNITS)
