"""Members, loans and the Library that enforces the lending rules."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from .items import LibraryItem


# --- errors: one base class so callers can catch "any library problem" or a specific one
class LibraryError(Exception):
    pass


class NotFoundError(LibraryError):
    pass


class NotBorrowableError(LibraryError):
    pass


class UnavailableError(LibraryError):
    pass


class LoanLimitError(LibraryError):
    pass


class UnpaidFinesError(LibraryError):
    pass


@dataclass(frozen=True)
class Member:
    id: str
    name: str
    max_loans: int = 3
    fines_cents: int = 0

    FINE_BLOCK_CENTS = 500   # members owing more than $5 can't borrow


@dataclass(frozen=True)
class Loan:
    item_id: str
    member_id: str
    borrowed_on: date
    due_on: date
    returned_on: date | None = None

    @property
    def is_open(self) -> bool:
        return self.returned_on is None

    def days_overdue(self, today: date) -> int:
        end = self.returned_on or today
        return max((end - self.due_on).days, 0)


@dataclass
class Library:
    items: dict[str, LibraryItem] = field(default_factory=dict)
    members: dict[str, Member] = field(default_factory=dict)
    loans: list[Loan] = field(default_factory=list)
    holds: dict[str, deque[str]] = field(default_factory=dict)       # item_id -> queue of member ids

    # --- catalogue and members
    def add_item(self, item: LibraryItem) -> None:
        if item.id in self.items:
            raise LibraryError(f"Item id {item.id} is already used.")
        self.items[item.id] = item

    def add_member(self, member: Member) -> None:
        if member.id in self.members:
            raise LibraryError(f"Member id {member.id} is already used.")
        self.members[member.id] = member

    def item(self, item_id: str) -> LibraryItem:
        try:
            return self.items[item_id]
        except KeyError:
            raise NotFoundError(f"No item {item_id}.") from None

    def member(self, member_id: str) -> Member:
        try:
            return self.members[member_id]
        except KeyError:
            raise NotFoundError(f"No member {member_id}.") from None

    # --- queries
    def open_loan(self, item_id: str) -> Loan | None:
        return next((l for l in self.loans if l.item_id == item_id and l.is_open), None)

    def loans_of(self, member_id: str) -> list[Loan]:
        return [l for l in self.loans if l.member_id == member_id and l.is_open]

    def is_available(self, item_id: str) -> bool:
        return self.open_loan(item_id) is None

    def next_in_line(self, item_id: str) -> str | None:
        queue = self.holds.get(item_id)
        return queue[0] if queue else None

    def search(self, query: str = "", kind: str | None = None, available_only: bool = False) -> list[LibraryItem]:
        found = [i for i in self.items.values() if i.matches(query) and (kind in (None, i.kind))
                 and (not available_only or (i.can_borrow and self.is_available(i.id)))]
        return sorted(found, key=lambda i: i.title.lower())

    def overdue(self, today: date) -> list[tuple[Loan, int]]:
        """(loan, fine so far) for every open loan past its due date."""
        result = []
        for loan in self.loans:
            if loan.is_open and loan.days_overdue(today):
                result.append((loan, loan.days_overdue(today) * self.item(loan.item_id).daily_fine_cents))
        return sorted(result, key=lambda pair: pair[0].due_on)

    # --- the rules
    def checkout(self, item_id: str, member_id: str, today: date) -> Loan:
        item, member = self.item(item_id), self.member(member_id)
        if not item.can_borrow:                                           # polymorphism: each class answers for itself
            raise NotBorrowableError(f"“{item.title}” is for use in the library only.")
        if not self.is_available(item_id):
            raise UnavailableError(f"“{item.title}” is already on loan.")
        waiting = self.next_in_line(item_id)
        if waiting and waiting != member_id:
            raise UnavailableError(f"“{item.title}” is on hold for {self.member(waiting).name}.")
        if len(self.loans_of(member_id)) >= member.max_loans:
            raise LoanLimitError(f"{member.name} already has {member.max_loans} items.")
        if member.fines_cents > Member.FINE_BLOCK_CENTS:
            raise UnpaidFinesError(f"{member.name} owes ${member.fines_cents / 100:.2f} - please pay first.")
        if waiting == member_id:
            self.holds[item_id].popleft()
        loan = Loan(item_id, member_id, today, today + timedelta(days=item.loan_days))   # each class has its own loan_days
        self.loans.append(loan)
        return loan

    def return_item(self, item_id: str, today: date) -> int:
        """Close the loan and return the fine in cents (also added to the member's balance)."""
        loan = self.open_loan(item_id)
        if loan is None:
            raise LibraryError(f"{item_id} isn't on loan.")
        closed = replace(loan, returned_on=today)
        self.loans[self.loans.index(loan)] = closed
        fine = closed.days_overdue(today) * self.item(item_id).daily_fine_cents
        if fine:
            member = self.members[loan.member_id]
            self.members[member.id] = replace(member, fines_cents=member.fines_cents + fine)
        return fine

    def place_hold(self, item_id: str, member_id: str) -> int:
        item, member = self.item(item_id), self.member(member_id)
        if not item.can_borrow:
            raise NotBorrowableError(f"“{item.title}” can't be borrowed.")
        queue = self.holds.setdefault(item_id, deque())
        if member_id in queue:
            raise LibraryError(f"{member.name} is already in the queue.")
        queue.append(member_id)
        return len(queue)

    def pay_fine(self, member_id: str, cents: int) -> Member:
        member = self.member(member_id)
        if not 0 < cents <= member.fines_cents:
            raise LibraryError("Pay between $0.01 and the amount owed.")
        updated = replace(member, fines_cents=member.fines_cents - cents)
        self.members[member_id] = updated
        return updated
