---
title: Type hints, dataclasses and enums
order: 4
icon: 🏷️
summary: Three tools that make Python code self-documenting and catch whole classes of bugs - and which every project in this course uses.
---

## Type hints
Hints document what goes in and out, and editors and `mypy` use them to find mistakes before you run anything.

```python
def allocate(total_cents: int, weights: list[int]) -> list[int]: ...
def find_item(self, noun: str, places: list[str]) -> str | None: ...
```

`from __future__ import annotations` (at the top of most files here) lets you use modern syntax like `str | None`
and refer to a class inside its own body.

## Dataclasses
`@dataclass` writes `__init__`, `__repr__` and `__eq__` from the annotations:

```python
from dataclasses import dataclass, field

@dataclass
class TodoList:
    tasks: dict[int, Task] = field(default_factory=dict)   # never use a mutable default directly!
```

| Option | Effect | Used for |
|---|---|---|
| `frozen=True` | instances can't be modified (and are hashable) | values: `Task`, `Unit`, `Transaction` |
| `field(default_factory=list)` | a fresh list per instance | collections inside objects |
| `__post_init__` | runs after `__init__` | validation and normalisation (`Contact`) |
| `dataclasses.replace(obj, x=1)` | a modified copy | updating frozen objects |

## Enums
Use an `Enum` whenever a value comes from a fixed set:

```python
class Priority(IntEnum):        # IntEnum: members compare like numbers, so they sort
    LOW = 1
    MEDIUM = 2
    HIGH = 3

Priority["HIGH"]     # by name - handy for forms
Priority(3)          # by value - handy for JSON
```

Enums prevent typos (`"hgih"` silently breaks a string comparison; `Priority.HGIH` is an error) and give editors autocompletion.
Members can even carry data: `Category.FOOD.icon` in the Expense Tracker.

## Protocols: interfaces by shape
`typing.Protocol` describes what methods something must have, without inheritance:

```python
class ExpenseRepository(Protocol):
    def add(self, expense: Expense) -> Expense: ...
    def in_month(self, month: str) -> list[Expense]: ...
```

Any class with those methods fits. This is static **duck typing**, checked by `mypy`.
