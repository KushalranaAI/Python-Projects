---
title: Clean code checklist
order: 12
icon: ✅
summary: A review checklist to run over any project before you call it done, plus the tools that automate half of it.
---

Use this list on your own projects, or open any project in this course and check it against the list.

## Structure
- [ ] Domain logic is in its own module, with no `input()`, `print()`, Flask or SQL
- [ ] Interfaces (CLI, web) are thin: parse → call the domain → display
- [ ] Storage is behind a small class (repository)
- [ ] Imports point towards the domain, never away from it

## Names and functions
- [ ] Names say what things *mean* (`overdue_tasks`, not `lst`)
- [ ] Functions do one thing and fit on a screen
- [ ] No magic numbers. Constants have names
- [ ] Guard clauses instead of deep nesting
- [ ] Keyword arguments for anything that isn't obvious

## Data and objects
- [ ] Fixed sets of values are `Enum`s
- [ ] Records are dataclasses, frozen when they shouldn't change
- [ ] Derived values are properties, not stored copies
- [ ] Money is `int` cents or `Decimal`, never `float`

## Errors
- [ ] Input is validated where it enters, with messages that say how to fix it
- [ ] Custom exceptions for domain failures. No bare `except:`
- [ ] Invalid states are impossible (no public setters for things like balances)

## Testing
- [ ] Every rule has a test; bugs get a test before the fix
- [ ] Time, randomness and storage are injectable
- [ ] Edge cases: empty input, zero, the maximum, duplicates, leap days

## Tools that do the boring part

```bash
pip install ruff mypy
ruff check .            # lint: unused imports, undefined names, bad patterns
ruff format .           # consistent formatting (like black)
mypy projects           # type checking from your hints
python -m pytest        # everything still works?
```

| Tool | Catches |
|---|---|
| `ruff check` | unused variables, shadowed names, mutable defaults, wildcard imports |
| `ruff format` | spacing, quotes, line length, so reviews talk about logic, not style |
| `mypy` | `None` where a value was expected, wrong argument types, missing returns |
| `pytest` | behaviour regressions |

> Clean code isn't about perfection. It's about leaving the code a little easier to change than you found it.
