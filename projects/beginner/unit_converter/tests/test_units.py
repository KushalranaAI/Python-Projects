import pytest

from projects.beginner.unit_converter.units import (Category, IncompatibleUnitsError, Unit, UnitRegistry,
                                                    UnknownUnitError, default_registry, format_number)

reg = default_registry()


@pytest.mark.parametrize("value, src, dst, expected", [
    (1, "km", "m", 1000), (1, "mi", "km", 1.609344), (12, "in", "ft", 1), (1, "lb", "kg", 0.45359237),
    (100, "°C", "°F", 212), (32, "°F", "°C", 0), (0, "K", "°C", -273.15), (-40, "°C", "°F", -40),
    (1, "GiB", "MiB", 1024), (1, "GB", "MB", 1000), (90, "min", "h", 1.5), (36, "km/h", "m/s", 10),
])
def test_known_conversions(value, src, dst, expected):
    assert reg.convert(value, src, dst) == pytest.approx(expected)


def test_round_trip_is_identity():
    for unit in reg.units_in(Category.TEMPERATURE):
        assert reg.convert(reg.convert(37.5, "°C", unit.symbol), unit.symbol, "°C") == pytest.approx(37.5)


def test_incompatible_categories_raise():
    with pytest.raises(IncompatibleUnitsError):
        reg.convert(1, "m", "kg")


def test_unknown_unit_raises():
    with pytest.raises(UnknownUnitError):
        reg.convert(1, "parsec", "m")


def test_registry_rejects_duplicates():
    with pytest.raises(ValueError):
        UnitRegistry([Unit("m", "metre", Category.LENGTH, 1), Unit("m", "mile?", Category.LENGTH, 1609)])


def test_convert_to_all_covers_the_category():
    table = reg.convert_to_all(1, "m")
    assert set(table) == {u.symbol for u in reg.units_in(Category.LENGTH)} and table["cm"] == pytest.approx(100)


@pytest.mark.parametrize("x, text", [(1000.0, "1000"), (0.5, "0.5"), (1609.344, "1609.34"), (0, "0"), (1e-7, "1.00000e-07")])
def test_format_number(x, text):
    assert format_number(x) == text
