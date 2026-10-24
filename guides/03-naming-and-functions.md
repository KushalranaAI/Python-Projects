---
title: Naming and functions
order: 3
icon: ✍️
summary: The two habits that make the biggest difference to readability - good names and small functions that do one thing.
---

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler

## Names (PEP 8)

| Kind | Style | Examples |
|---|---|---|
| variables, functions, methods | `snake_case` | `overdue_tasks`, `days_until_birthday()` |
| classes | `PascalCase` | `TodoList`, `BudgetStatus` |
| constants | `UPPER_SNAKE` | `MAX_MISSES`, `READING_WPM` |
| "internal" | leading `_` | `_balance`, `_check_withdrawal()` |

Rules of thumb:
- Name things for **what they mean**, not their type: `prices`, not `list1`; `is_overdue`, not `flag`.
- Booleans read like questions: `is_won`, `has_cabin`, `can_borrow`.
- Functions are verbs: `parse_amount`, `allocate`, `check_strength`.
- Replace **magic numbers** with named constants: `MONTHLY_FEE = 500` explains itself; `500` doesn't.

## Small functions that do one thing
If you need "and" to describe a function, it probably does two things.

```python
# ❌ one function: parse, validate, compute, format, print
def handle(text):
    ...40 lines...

# ✅ each step has a name, a test and a single reason to change
def parse_items(text: str, bill: Bill) -> None: ...
def allocate(total_cents: int, weights: list[int]) -> list[int]: ...
def format_cents(cents: int) -> str: ...
```

## Guard clauses instead of nesting

```python
# ❌ the important line is buried four levels deep
def guess(self, number):
    if not self.is_over:
        if 1 <= number <= self.high:
            self.guesses.append(number)
            ...

# ✅ handle the exceptional cases first, then the main path reads straight down
def guess(self, number):
    if self.is_over:
        raise GameOverError("The game is over.")
    if not 1 <= number <= self.high:
        raise ValueError(f"Guess between 1 and {self.high}.")
    self.guesses.append(number)
    ...
```

## Avoid boolean "mode" parameters

```python
render(task, True)                      # ❌ what does True mean?
view(show_done=False, tag="work")       # ✅ keyword-only arguments read like sentences
```

Make parameters keyword-only with a bare `*`: `def view(self, *, show_done=True, tag=None)`.

## Comments explain *why*, code explains *what*

```python
# ❌ increment i
i += 1

# ✅ 302 instead of 301: browsers cache 301s, so later clicks would never reach us to be counted
return redirect(url, code=302)
```

## Docstrings
Public functions and classes get a one-line docstring saying what they do (and, for tricky rules, the rule itself).
The Habit Tracker's `current_streak` docstring is a good example: it records a decision ("today is still in progress").
