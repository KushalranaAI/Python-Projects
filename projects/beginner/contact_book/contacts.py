"""Contacts with validation, a searchable book, and CSV import/export."""

from __future__ import annotations

import csv
import io
import re
import uuid
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import date

EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PHONE_ALLOWED = re.compile(r"^\+?[\d\s().-]{7,20}$")


class ValidationError(ValueError):
    """Carries one message per invalid field, so a form can show them next to the inputs."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


def normalize_phone(phone: str) -> str:
    """Keep a leading + and the digits: '+44 (0)20 7946-0958' → '+440207946 0958' style noise removed."""
    phone = phone.strip()
    return ("+" if phone.startswith("+") else "") + re.sub(r"\D", "", phone)


@dataclass
class Contact:
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    birthday: date | None = None
    tags: list[str] = field(default_factory=list)
    favorite: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self):
        self.name = " ".join(self.name.split())
        self.email = self.email.strip().lower()
        self.tags = sorted({t.strip().lower() for t in self.tags if t.strip()})
        errors = self.validate()
        if errors:
            raise ValidationError(errors)
        self.phone = normalize_phone(self.phone) if self.phone else ""

    def validate(self) -> dict[str, str]:
        errors = {}
        if not self.name:
            errors["name"] = "is required"
        if self.email and not EMAIL.match(self.email):
            errors["email"] = "doesn't look like an email address"
        if self.phone and not PHONE_ALLOWED.match(self.phone.strip()):
            errors["phone"] = "use digits, spaces, + ( ) - only (7-20 characters)"
        if self.birthday and self.birthday > date.today():
            errors["birthday"] = "can't be in the future"
        return errors

    @property
    def initials(self) -> str:
        return "".join(part[0] for part in self.name.split()[:2]).upper()

    def matches(self, query: str) -> bool:
        q = query.lower().strip()
        haystack = " ".join([self.name, self.email, self.phone, self.company, *self.tags]).lower()
        return all(word in haystack for word in q.split())

    def days_until_birthday(self, today: date) -> int | None:
        if not self.birthday:
            return None
        def on_year(year: int) -> date:
            try:
                return self.birthday.replace(year=year)
            except ValueError:                      # 29 February in a non-leap year
                return date(year, 3, 1)
        upcoming = on_year(today.year)
        if upcoming < today:
            upcoming = on_year(today.year + 1)
        return (upcoming - today).days

    def to_dict(self) -> dict:
        data = asdict(self)
        data["birthday"] = self.birthday.isoformat() if self.birthday else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Contact:
        data = dict(data)
        data["birthday"] = date.fromisoformat(data["birthday"]) if data.get("birthday") else None
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})


class ContactNotFoundError(LookupError):
    pass


class ContactBook:
    def __init__(self, contacts: list[Contact] | None = None):
        self._contacts: dict[str, Contact] = {c.id: c for c in contacts or []}

    def __len__(self) -> int:
        return len(self._contacts)

    def __iter__(self):
        return iter(sorted(self._contacts.values(), key=lambda c: (not c.favorite, c.name.lower())))

    def add(self, contact: Contact) -> Contact:
        duplicate = self.find_duplicate(contact)
        if duplicate:
            raise ValidationError({"email" if contact.email and duplicate.email == contact.email else "phone":
                                   f"already belongs to {duplicate.name}"})
        self._contacts[contact.id] = contact
        return contact

    def find_duplicate(self, contact: Contact) -> Contact | None:
        for other in self._contacts.values():
            if other.id != contact.id and ((contact.email and other.email == contact.email) or
                                           (contact.phone and other.phone == contact.phone)):
                return other
        return None

    def get(self, contact_id: str) -> Contact:
        try:
            return self._contacts[contact_id]
        except KeyError:
            raise ContactNotFoundError(contact_id) from None

    def update(self, contact_id: str, **changes) -> Contact:
        updated = replace(self.get(contact_id), **changes)   # replace() re-runs __post_init__, so it re-validates
        duplicate = self.find_duplicate(updated)
        if duplicate:
            raise ValidationError({"email": f"already belongs to {duplicate.name}"})
        self._contacts[contact_id] = updated
        return updated

    def remove(self, contact_id: str) -> Contact:
        return self._contacts.pop(self.get(contact_id).id)

    def search(self, query: str = "", tag: str | None = None) -> list[Contact]:
        return [c for c in self if c.matches(query) and (tag is None or tag in c.tags)]

    def tags(self) -> list[str]:
        return sorted({t for c in self._contacts.values() for t in c.tags})

    def upcoming_birthdays(self, today: date, within_days: int = 30) -> list[tuple[Contact, int]]:
        soon = [(c, d) for c in self._contacts.values() if (d := c.days_until_birthday(today)) is not None and d <= within_days]
        return sorted(soon, key=lambda pair: pair[1])

    # --- CSV, the format every spreadsheet and phone understands
    CSV_FIELDS = ["name", "email", "phone", "company", "birthday", "tags", "favorite"]

    def to_csv(self) -> str:
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=self.CSV_FIELDS)
        writer.writeheader()
        for c in self:
            writer.writerow({"name": c.name, "email": c.email, "phone": c.phone, "company": c.company,
                             "birthday": c.birthday.isoformat() if c.birthday else "", "tags": ";".join(c.tags),
                             "favorite": "yes" if c.favorite else ""})
        return out.getvalue()

    def import_csv(self, text: str) -> tuple[int, list[str]]:
        """Add every valid row; collect a readable error for each bad one instead of stopping at the first."""
        added, problems = 0, []
        for line_no, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
            try:
                self.add(Contact(name=row.get("name", ""), email=row.get("email", ""), phone=row.get("phone", ""),
                                 company=row.get("company", ""),
                                 birthday=date.fromisoformat(row["birthday"]) if row.get("birthday") else None,
                                 tags=(row.get("tags") or "").split(";"), favorite=(row.get("favorite") or "").lower() in {"yes", "true", "1"}))
                added += 1
            except ValueError as error:
                problems.append(f"line {line_no}: {error}")
        return added, problems
