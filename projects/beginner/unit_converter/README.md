---
title: Unit Converter
order: 2
icon: 📏
time: 1-2 hours
summary: Convert between 37 units in 7 categories. You'll learn to replace long if/elif chains with a table of data plus one general rule.
python_skills:
  - Floats and rounding, f-string number formatting
  - Dictionaries as lookup tables
  - Regular expressions for parsing "12 km to mi"
  - List comprehensions and dict comprehensions
oop_concepts:
  - Frozen (immutable) dataclasses
  - A registry class that owns a collection
  - Custom exception hierarchy (KeyError / ValueError subclasses)
  - Encapsulation (the `_units` dict is private)
clean_code:
  - Data-driven design instead of branching
  - One formula for every unit (factor + offset)
  - "`raise ... from None` for clean error messages"
  - Parametrized tests as a table of known answers
features:
  - Length, mass, temperature, volume, speed, digital storage and time
  - Converts one value into every unit of its category at once
  - Terminal mode understands queries like `100 °F to °C`
  - Adding a new unit is one line
architecture: |
  classDiagram
    class Category {
      <<enum>>
      LENGTH
      MASS
      TEMPERATURE
      ...
    }
    class Unit {
      <<frozen dataclass>>
      +symbol str
      +name str
      +category Category
      +factor float
      +offset float
      +to_base(value) float
      +from_base(value) float
    }
    class UnitRegistry {
      -_units dict~str, Unit~
      +add(unit)
      +get(symbol) Unit
      +units_in(category) list~Unit~
      +convert(value, from, to) float
      +convert_to_all(value, from) dict
    }
    class UnknownUnitError
    class IncompatibleUnitsError
    UnitRegistry "1" o-- "*" Unit
    Unit --> Category
    UnitRegistry ..> UnknownUnitError
    UnitRegistry ..> IncompatibleUnitsError
flow: |
  flowchart LR
    A["100 °F"] -->|"to_base: v·5/9 − 160/9"| B["37.78 (base = °C)"]
    B -->|"from_base: (v − offset)/factor"| C["310.93 K"]
steps:
  - title: Spot the pattern before coding
    body: |
      The naive version is a giant `if from == "km" and to == "m": ... elif ...`, with **n²** branches for *n* units.
      Notice instead that every unit is just a multiple of a *base unit* (metres, kilograms, litres…). So we need
      only **two** conversions per unit: to the base and back. That's *n* rows of data and one rule.
  - title: Describe a unit with a frozen dataclass
    files: [units.py]
    body: |
      `@dataclass(frozen=True)` makes `Unit` immutable and hashable: a unit's definition should never change at run time.
      Temperatures aren't pure multiples (0 °C ≠ 0 °F), so we add an `offset`: `base = value × factor + offset`.
      For °F: factor 5/9, offset −160/9, because °C = (°F − 32) × 5/9.
  - title: Build the registry
    files: [units.py]
    body: |
      `UnitRegistry` owns a private `_units` dict keyed by symbol. Its public methods (`get`, `units_in`,
      `convert`) are the only way in, which is **encapsulation**. `add` refuses duplicates so a typo can't silently replace a unit.
  - title: Design errors as part of the API
    files: [units.py]
    body: |
      Two custom exceptions say exactly what went wrong. `UnknownUnitError` subclasses `KeyError` and
      `IncompatibleUnitsError` subclasses `ValueError`, so callers can catch them specifically *or* generally.
      `raise ... from None` hides the internal `KeyError` traceback the user doesn't care about.
  - title: Test with a table of known answers
    files: [tests/test_units.py]
    body: |
      `@pytest.mark.parametrize` turns a list of `(value, from, to, expected)` rows into a dozen tests. Use
      `pytest.approx` for floats, since `0.1 + 0.2 != 0.3`. Include tricky cases: −40 °C = −40 °F, 0 K, GiB vs GB.
  - title: Parse free text in the CLI with a regex
    files: [cli.py]
    body: |
      `QUERY` matches `<number> <unit> to|in <unit>`. The walrus loop `while (line := input(...)) not in {...}`
      reads, checks and loops in one line. The CLI catches the domain's exceptions and prints their message,
      without re-implementing any validation.
  - title: A GET form in Flask
    files: [web.py, templates/unit_converter/index.html]
    body: |
      Conversions don't change anything, so the form uses **GET**: the result URL is bookmarkable and refreshing is
      harmless. The template receives `format_number` as `fmt`, so formatting rules live in Python, not in the template.
exercises:
  - Add **area** (m², hectare, acre) and **pressure** (Pa, bar, psi, atm) categories. You only add data, no code.
  - Load the unit table from a JSON file instead of a Python list. Validate the file when it is loaded.
  - Support compound input like `5 ft 11 in to cm` in the CLI.
  - Add a "precision" option (significant digits) to the web form and to `format_number`.
---

## Why this design matters

With 37 units, an if/elif design needs **37 × 36 = 1,332** branches. The table design needs 37 rows and a 2-line
formula. Every time you write a long chain of `if/elif` that differs only in numbers or strings, ask:
*can this be a table?*

| Approach | Units | Branches / rows | Adding a unit |
|---|---|---|---|
| if/elif per pair | n | n·(n−1) | touch n places |
| base unit + table | n | n | one line |
