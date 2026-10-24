---
title: Library Management System
order: 2
icon: 📚
time: 4-5 hours
summary: Books, reference books, DVDs and magazines; members, loans, holds and late fines. The project where inheritance, abstract classes and polymorphism earn their keep.
python_skills:
  - "@abstractmethod, ClassVar and super()"
  - collections.deque as a queue
  - datetime.timedelta arithmetic
  - "**kwargs unpacking when loading objects"
  - Exception hierarchies
oop_concepts:
  - Abstract base class with shared behaviour
  - Inheritance (Book → ReferenceBook) and method overriding
  - Polymorphism - item.loan_days / can_borrow / creator() differ per class
  - Class attributes as per-type configuration
  - __eq__ and __hash__, __repr__
  - Polymorphic serialisation with a type registry
clean_code:
  - Each class answers its own questions ("can I be borrowed?") instead of `if type == ...`
  - One exception base class + specific subclasses
  - Rules in one place (`Library.checkout`) with a clear message per rule
  - Inject 'today' - and a time machine to demo it
features:
  - Catalogue of books, reference books, DVDs and magazines with search and filters
  - Lend, return, and place holds (a waiting queue per item)
  - Per-type loan periods and daily fines; members blocked above $5 owed
  - Overdue report and fine payments
  - A time machine to jump ahead and watch fines grow
architecture: |
  classDiagram
    class LibraryItem {
      <<abstract>>
      +kind ClassVar
      +loan_days ClassVar = 14
      +daily_fine_cents ClassVar = 25
      +id str
      +title str
      +year int
      +can_borrow bool
      +creator()* str
      +describe() str
      +to_dict() dict
    }
    class Book {
      +author str
      +isbn str
      +creator() str
    }
    class ReferenceBook {
      +can_borrow = False
    }
    class DVD {
      +loan_days = 7
      +daily_fine_cents = 100
      +director str
      +minutes int
    }
    class Magazine {
      +loan_days = 7
      +issue str
    }
    class Library {
      +items dict
      +members dict
      +loans list~Loan~
      +holds dict~str, deque~
      +checkout(item, member, today) Loan
      +return_item(item, today) int
      +place_hold(item, member) int
      +overdue(today) list
    }
    class Member {
      +id str
      +name str
      +max_loans int
      +fines_cents int
    }
    class Loan {
      +borrowed_on date
      +due_on date
      +returned_on date
      +days_overdue(today) int
    }
    LibraryItem <|-- Book
    Book <|-- ReferenceBook
    LibraryItem <|-- DVD
    LibraryItem <|-- Magazine
    Library o-- LibraryItem
    Library o-- Member
    Library *-- Loan
flow: |
  flowchart TD
    C["checkout(item, member, today)"] --> A{"item.can_borrow?<br/>(polymorphic)"}
    A -->|no| E1[NotBorrowableError]
    A -->|yes| B{already on loan?}
    B -->|yes| E2[UnavailableError]
    B -->|no| H{on hold for someone else?}
    H -->|yes| E2
    H -->|no| L{member at max_loans?}
    L -->|yes| E3[LoanLimitError]
    L -->|no| F{fines > $5?}
    F -->|yes| E4[UnpaidFinesError]
    F -->|no| OK["Loan(due = today + item.loan_days)"]
steps:
  - title: Find what all items share
    files: [items.py]
    body: |
      Every item has an id, a title and a year, can be described and searched, and has a loan period and a fine rate.
      That goes in `LibraryItem`. What *differs*, such as who made it, is declared with `@abstractmethod creator()`, which
      every subclass must provide.
  - title: Subclasses override only what's different
    files: [items.py]
    body: |
      `Book.__init__` calls `super().__init__(...)` for the shared attributes, then adds author and ISBN (with a real
      checksum check). `DVD` overrides the **class attributes** `loan_days = 7` and `daily_fine_cents = 100`.
      `ReferenceBook(Book)` overrides one property: `can_borrow → False`.
  - title: Polymorphism replaces type checks
    files: [library.py]
    body: |
      `checkout` never asks `if isinstance(item, DVD)`. It asks the item: `item.can_borrow`, `item.loan_days`,
      `item.daily_fine_cents`. Add an `AudioBook` class tomorrow and `checkout` works unchanged. That's the
      **open/closed principle**: open for extension, closed for modification.
  - title: Model loans and members as immutable records
    files: [library.py]
    body: |
      Returning a book creates a new `Loan` with `returned_on` set (`dataclasses.replace`). A fine creates an updated `Member`.
      Immutable records make history easy to reason about.
  - title: An exception hierarchy
    files: [library.py]
    body: |
      `LibraryError` is the base; `UnavailableError`, `LoanLimitError`, `UnpaidFinesError`… say exactly which rule failed.
      The interfaces catch `LibraryError` once and show the message.
  - title: Holds with a queue
    files: [library.py]
    body: |
      `collections.deque` gives O(1) `append` and `popleft`, the right structure for a first-come-first-served queue.
      When an item with a queue comes back, only the first person in line may borrow it.
  - title: Save polymorphic objects
    files: [items.py, storage.py]
    body: |
      Each class's `to_dict` extends its parent's (`{**super().to_dict(), "author": ...}`) and includes a `"type"` key.
      `ITEM_TYPES` maps that key back to the class when loading. The round-trip test checks every subclass survives.
  - title: Test the rules, then add a time machine
    files: [tests/test_library.py, web.py]
    body: |
      Because `today` is a parameter, tests jump 13 days in one line. The web UI turns the same idea into a feature: a
      session setting that shifts "today", so you can see fines without waiting.
exercises:
  - Add an `AudioBook` subclass (narrator, hours, 21-day loans). How many lines outside `items.py` did you change?
  - Add **renewals** (once, only if nobody is waiting).
  - Add member tiers with a `StudentMember` subclass (lower fines). Is inheritance or a `tier` field the better design? Argue both.
  - Move persistence to SQLite with tables per item type, or one table with a `type` column. Compare the two designs.
---

## Inheritance vs. composition here

Inheritance fits the items: a DVD **is a** library item, and the subclasses only *specialise* behaviour.
The `Library`, though, **has** items, members and loans. That's **composition**, and it's why `Library` isn't a
subclass of `dict` or `list`. Rule of thumb: inherit for *is-a* relationships with shared behaviour, compose for *has-a*.
