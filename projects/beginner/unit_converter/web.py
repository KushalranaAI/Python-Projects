"""Flask interface: choose a category, a value and a unit; see it in every unit of that category."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from projects.ui_kit import run_standalone

from .units import Category, UnknownUnitError, default_registry, format_number

bp = Blueprint("unit_converter", __name__, template_folder="templates")
registry = default_registry()


@bp.get("/")
def index():
    category = Category[request.args.get("category", "LENGTH")]
    units = registry.units_in(category)
    unit = request.args.get("unit", units[0].symbol)
    error, results = None, {}
    try:
        value = float(request.args.get("value", "1"))
        results = registry.convert_to_all(value, unit)
    except ValueError:
        value, error = 1.0, "Please enter a number."
    except UnknownUnitError:
        unit = units[0].symbol
        results = registry.convert_to_all(value, unit)
    return render_template("unit_converter/index.html", categories=list(Category), category=category, units=units,
                           unit=unit, value=value, results=results, error=error, fmt=format_number,
                           names={u.symbol: u.name for u in units})


if __name__ == "__main__":
    run_standalone(bp, "Unit Converter")
