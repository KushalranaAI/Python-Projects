---
title: Files, JSON, CSV and SQLite
order: 11
icon: 💾
summary: Reading and writing data safely - pathlib, context managers, atomic writes, JSON and CSV round trips, and SQLite with transactions and placeholders.
---

## pathlib and `with`

```python
from pathlib import Path

path = Path("instance") / "todo.json"
text = path.read_text(encoding="utf-8")          # opens, reads and closes for you

with open(path, "w", encoding="utf-8") as f:     # 'with' closes the file even if an exception happens
    f.write(text)
```

Always pass `encoding="utf-8"`. The default differs between operating systems.

## JSON: dicts and lists ↔ text
JSON knows strings, numbers, booleans, null, lists and objects, but not dates, sets, enums or your classes. So objects get
`to_dict()` / `from_dict()`:

```python
def to_dict(self) -> dict:
    return {"id": self.id, "due": self.due.isoformat() if self.due else None, "priority": self.priority.name}
```

Test the round trip: `Task.from_dict(task.to_dict()) == task`.

## Atomic writes
Writing a file in place can leave it half-written if the program crashes. Write a temporary file, then rename it.
A rename is atomic:

```python
tmp = path.with_suffix(".tmp")
tmp.write_text(json.dumps(data))
tmp.replace(path)
```

## CSV
Use the `csv` module (it handles commas inside quotes for you) with `DictReader`/`DictWriter`. `io.StringIO` gives you
an in-memory "file", which is handy for building a download or testing.

## SQLite: a real database in one file

```python
import sqlite3

with sqlite3.connect("expenses.db") as conn:       # commits on success, rolls back on exception
    conn.execute("INSERT INTO expenses (amount, description) VALUES (?, ?)", (1250, user_text))
```

| Do | Don't |
|---|---|
| `?` placeholders | f-strings: `f"... WHERE code = '{code}'"` → SQL injection |
| constraints in the schema (`NOT NULL`, `CHECK`, `UNIQUE`) | rely only on Python checks |
| one transaction for changes that belong together | commit halfway through |
| `row_factory = sqlite3.Row` to access columns by name | `row[3]` |

The Expense Tracker's tests include an injection attempt that is safely stored as text. Read it to see why placeholders matter.
