---
title: Contact Book
order: 8
icon: 📇
time: 3 hours
summary: A contact manager with field-by-field validation, duplicate detection, multi-word search, birthday reminders and CSV import/export.
python_skills:
  - Regular expressions for validation and cleaning
  - The csv module (DictReader / DictWriter) and io.StringIO
  - uuid for identifiers
  - Date arithmetic (including 29 February!)
  - File uploads and downloads in Flask
oop_concepts:
  - An exception class that carries data (errors per field)
  - __len__ and __iter__ to make a collection feel built-in
  - Normalising data in __post_init__
  - Class constants (CSV_FIELDS)
clean_code:
  - Validate once, at the edge of the model, and report every problem at once
  - Normalise input (case, spaces, phone formatting) so comparisons work
  - Import keeps going on bad rows and reports them all
  - Form error messages next to the field that caused them
features:
  - Add / edit / delete contacts with favourites and tags
  - Search across all fields, filter by tag
  - Upcoming-birthday reminders
  - Duplicate email / phone detection
  - Export to CSV and import from CSV with per-line error reports
architecture: |
  classDiagram
    class Contact {
      +id str
      +name str
      +email str
      +phone str
      +company str
      +birthday date
      +tags list
      +favorite bool
      +validate() dict
      +matches(query) bool
      +days_until_birthday(today) int
      +initials str
    }
    class ContactBook {
      -_contacts dict
      +__len__() int
      +__iter__() Iterator
      +add(contact)
      +update(id, **changes)
      +remove(id)
      +search(query, tag) list
      +upcoming_birthdays(today) list
      +to_csv() str
      +import_csv(text) tuple
    }
    class ValidationError {
      +errors dict~str,str~
    }
    class JsonContactStore {
      +load() ContactBook
      +save(book)
    }
    ValueError <|-- ValidationError
    ContactBook "1" *-- "*" Contact
    Contact ..> ValidationError : raises
    JsonContactStore ..> ContactBook
flow: |
  flowchart LR
    F[form submit] --> C["Contact(**fields)<br/>__post_init__: normalise + validate"]
    C -->|ValidationError| E["re-render form<br/>errors next to fields"]
    C -->|ok| D{duplicate email/phone?}
    D -->|yes| E
    D -->|no| S[book.add → store.save → redirect]
steps:
  - title: Design the Contact and its validation rules
    files: [contacts.py]
    body: |
      `__post_init__` first **normalises** (collapse spaces in names, lowercase emails and tags), then **validates** and
      collects *all* problems into a dict like `{"email": "doesn't look like an email address"}`. One error per field
      makes great form feedback.
  - title: An exception that carries data
    files: [contacts.py]
    body: |
      `ValidationError(ValueError)` stores `errors` as an attribute. Code that only cares that *something* is wrong can
      catch `ValueError`; the web form reads `error.errors` to show each message in the right place.
  - title: Make ContactBook behave like a built-in collection
    files: [contacts.py]
    body: |
      With `__len__` and `__iter__`, you can write `len(book)` and `for c in book`, and iteration already sorts
      favourites first. Python's *data model* lets your classes plug into the language.
  - title: Search, duplicates and birthdays
    files: [contacts.py]
    body: |
      `matches` requires every query word to appear in some field. `find_duplicate` compares the *normalised* email and phone.
      `days_until_birthday(today)` takes today as a parameter (testable!) and handles 29 February in non-leap years.
  - title: CSV in and out
    files: [contacts.py]
    body: |
      `csv.DictWriter` writes rows from dicts into an `io.StringIO` buffer, which is a file in memory. `import_csv` keeps going
      when a row is bad and returns `(added, problems)`, so the user learns about **every** broken line at once.
  - title: Persist and test
    files: [storage.py, tests/test_contacts.py]
    body: |
      The JSON store mirrors Project 3's. Tests cover normalisation, each validation rule (parametrised), search,
      duplicates, birthdays (including the leap-year case) and both round trips.
  - title: A real form with inline errors, uploads and downloads
    files: [web.py, templates/contact_book/index.html]
    body: |
      A Jinja **macro** renders each labelled input plus its error. On a validation error the route re-renders the form
      with the user's input and status **400**, without redirecting. Export returns a `Response` with a
      `Content-Disposition` header; import reads `request.files`.
exercises:
  - Add **groups** (Family, Work…) as their own class, where a contact can belong to several. Where should the relationship live?
  - Export and import **vCard (.vcf)** files, the format phones use.
  - 'Add **merge duplicates**: combine two contacts, keeping the non-empty fields.'
  - Validate phone numbers per country with the `phonenumbers` library, behind the same `validate()` method.
---

## Validation strategy

| Where | What | Why |
|---|---|---|
| HTML form (`type=email`, `required`) | quick hints | convenience only, since anyone can bypass it |
| `Contact.__post_init__` | normalise and validate every field | the **single source of truth**: CLI, web and CSV import all go through it |
| `ContactBook.add/update` | rules that need *other* contacts (duplicates) | a single contact can't know about the others |
