---
title: Expense Tracker
order: 1
icon: 💸
time: 4 hours
summary: Track spending in an SQLite database, set monthly budgets per category, and get reports with breakdowns, trends and warnings. Your first project with a real database.
python_skills:
  - sqlite3 - schemas, parameterised queries, transactions
  - Context managers (with) and contextlib.contextmanager
  - Decimal parsing to integer cents
  - collections.defaultdict, calendar.monthrange
  - SQL GROUP BY and aggregate functions
oop_concepts:
  - The Repository pattern
  - typing.Protocol - an interface by structure
  - Enum members with extra attributes (label, icon)
  - Frozen dataclasses for domain records and report objects
clean_code:
  - Never build SQL with f-strings (SQL injection)
  - Reports as pure functions - test without a database
  - Business rules in the model, constraints in the schema (CHECK)
  - One connection per unit of work, closed in finally
features:
  - Add and delete expenses in 8 categories
  - Monthly view with per-category bars and a 12-month history chart
  - Budgets with green / amber / red warnings
  - Daily average and comparison with the previous month
  - CLI - expenses add 12.50 food "Lunch" / report / budget
architecture: |
  classDiagram
    class Category {
      <<enum>>
      FOOD
      TRANSPORT
      ...
      +label str
      +icon str
    }
    class Expense {
      <<frozen>>
      +amount_cents int
      +category Category
      +description str
      +spent_on date
      +id int
      +month str
    }
    class ExpenseRepository {
      <<Protocol>>
      +add(expense) Expense
      +delete(id) bool
      +in_month(month) list
      +monthly_totals() dict
      +budgets() dict
      +set_budget(budget)
    }
    class SqliteExpenseRepository {
      -path str
      -_connect() Connection
    }
    class MonthlyReport {
      +total int
      +by_category list
      +daily_average int
      +budgets list~BudgetStatus~
      +change_vs_previous float
    }
    class BudgetStatus {
      +spent int
      +limit int
      +ratio float
      +level str
    }
    ExpenseRepository <|.. SqliteExpenseRepository : implements
    SqliteExpenseRepository ..> Expense
    MonthlyReport *-- BudgetStatus
    monthly_report ..> MonthlyReport : builds
flow: |
  sequenceDiagram
    participant W as web.py
    participant R as SqliteExpenseRepository
    participant DB as SQLite
    participant P as reports.monthly_report
    W->>R: in_month("2026-03")
    R->>DB: SELECT ... WHERE substr(spent_on,1,7) = ?
    DB-->>R: rows
    R-->>W: list[Expense]
    W->>R: budgets(), monthly_totals()
    W->>P: monthly_report(month, expenses, budgets, today)
    P-->>W: MonthlyReport (pure computation)
    W-->>W: render template
steps:
  - title: Model the domain first
    files: [models.py]
    body: |
      `Category` is an Enum whose members carry a label and an icon (an Enum `__init__` receives the tuple value).
      `Expense` validates itself: positive amount, a description, not in the future. `parse_amount` turns user text into
      integer cents and rejects "1.234".
  - title: Design the schema with constraints
    files: [repository.py]
    body: |
      `CHECK (amount > 0)` means even a buggy program can't store a negative expense. The database is your last line of
      defence. An index on `spent_on` keeps month queries fast as the table grows.
  - title: A repository behind a Protocol
    files: [repository.py]
    body: |
      `ExpenseRepository(Protocol)` lists the methods the app needs. `SqliteExpenseRepository` provides them without
      inheriting anything; a `Protocol` is satisfied **by structure** ("if it has these methods, it fits"). Tests could
      use an in-memory fake that fits the same shape.
  - title: Connections, transactions and placeholders
    files: [repository.py]
    body: |
      `_connect()` is a generator-based context manager: open, `yield`, **commit** on success, **rollback** on error,
      always **close**. Every query passes values as a tuple to `?` placeholders. Run the injection test and look: the
      "DROP TABLE" description is stored as harmless text.
  - title: Reports as pure functions
    files: [reports.py]
    body: |
      `monthly_report(month, expenses, budgets, today)` takes plain data and returns a frozen `MonthlyReport`. No database,
      no clock: `today` is a parameter. `BudgetStatus.level` turns the spent/limit ratio into ok/warning/over.
  - title: Test every layer
    files: [tests/test_expenses.py]
    body: |
      Parsing and validation are parametrised. The repository gets a fresh SQLite file in `tmp_path` per test. Reports are
      tested with fixed dates. There's even a test that proves SQL injection doesn't work.
  - title: CLI and web on the same repository
    files: [cli.py, web.py, templates/expense_tracker/index.html]
    body: |
      Charts are plain HTML: bar widths are percentages computed in the template from report numbers. The budget form posts
      one field per category; empty means "no budget", which the repository turns into a DELETE.
exercises:
  - Add **recurring expenses** (rent on the 1st of each month). Generate missing entries when the app starts.
  - Import a **bank statement CSV** and auto-categorise rows by keywords in the description.
  - Add an `InMemoryExpenseRepository` that satisfies the Protocol and use it in some tests. Run `mypy` to check it fits.
  - Add **multiple currencies** with a fixed exchange-rate table, keeping totals in a base currency.
---

## Why the Repository pattern?

```mermaid
flowchart LR
  WEB[web.py] --> P{{ExpenseRepository Protocol}}
  CLI[cli.py] --> P
  P -.implemented by.-> S[SqliteExpenseRepository]
  P -.could be.-> M[InMemoryExpenseRepository]
  P -.could be.-> PG[PostgresExpenseRepository]
```

The web and CLI code only call `add`, `in_month`, `budgets`… They don't know SQL exists. Moving to PostgreSQL means
writing one new class, and the reports, templates and tests of the reports don't change.
