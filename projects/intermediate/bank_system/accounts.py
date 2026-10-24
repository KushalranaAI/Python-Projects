"""Bank accounts. The balance is private and only changes through deposit/withdraw, which record a transaction.

Account uses the *template method* pattern: `withdraw` is fixed (validate → check rules → record), and subclasses
customise only the rule step `_check_withdrawal` and the `month_end` behaviour.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import ClassVar


class BankError(Exception):
    pass


class InvalidAmountError(BankError):
    pass


class InsufficientFundsError(BankError):
    pass


class WithdrawalLimitError(BankError):
    pass


class TxKind(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer in"
    TRANSFER_OUT = "transfer out"
    INTEREST = "interest"
    FEE = "fee"


@dataclass(frozen=True)
class Transaction:
    kind: TxKind
    amount: int              # cents; positive = money in, negative = money out
    balance_after: int
    at: datetime
    memo: str = ""


def check_amount(cents: int) -> int:
    if not isinstance(cents, int) or isinstance(cents, bool):
        raise InvalidAmountError("Amounts are whole cents (int).")
    if cents <= 0:
        raise InvalidAmountError("Amount must be positive.")
    return cents


class Account(ABC):
    kind: ClassVar[str] = "account"

    def __init__(self, number: str, owner: str):
        if not owner.strip():
            raise ValueError("An account needs an owner.")
        self.number = number
        self.owner = owner.strip()
        self._balance = 0                                  # private: never assigned from outside
        self._transactions: list[Transaction] = []

    # --- read-only views
    @property
    def balance(self) -> int:
        return self._balance

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        return tuple(self._transactions)                   # a copy: callers can't append to our history

    # --- the only two ways money moves
    def deposit(self, cents: int, at: datetime, memo: str = "", kind: TxKind = TxKind.DEPOSIT) -> Transaction:
        return self._record(kind, check_amount(cents), at, memo)

    def withdraw(self, cents: int, at: datetime, memo: str = "", kind: TxKind = TxKind.WITHDRAWAL) -> Transaction:
        check_amount(cents)
        self._check_withdrawal(cents, at)                  # the hook subclasses customise
        return self._record(kind, -cents, at, memo)

    def _record(self, kind: TxKind, signed_cents: int, at: datetime, memo: str) -> Transaction:
        self._balance += signed_cents
        tx = Transaction(kind, signed_cents, self._balance, at, memo)
        self._transactions.append(tx)
        return tx

    # --- hooks for subclasses
    @abstractmethod
    def _check_withdrawal(self, cents: int, at: datetime) -> None:
        """Raise a BankError if this withdrawal isn't allowed."""

    @abstractmethod
    def month_end(self, at: datetime) -> Transaction | None:
        """Interest, fees… whatever this account type does at the end of a month."""

    def statement(self, month: str | None = None) -> list[Transaction]:
        return [t for t in self._transactions if month is None or t.at.strftime("%Y-%m") == month]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.number!r}, owner={self.owner!r}, balance={self._balance})"


class CheckingAccount(Account):
    kind = "checking"
    MONTHLY_FEE = 500                   # $5, waived when the balance is at least $1,000
    FEE_WAIVER_BALANCE = 100_000

    def __init__(self, number: str, owner: str, overdraft_limit: int = 0):
        super().__init__(number, owner)
        self.overdraft_limit = overdraft_limit

    @property
    def available(self) -> int:
        return self._balance + self.overdraft_limit

    def _check_withdrawal(self, cents, at):
        if cents > self.available:
            raise InsufficientFundsError(f"Only ${self.available / 100:,.2f} available (including overdraft).")

    def month_end(self, at):
        if self._balance >= self.FEE_WAIVER_BALANCE:
            return None
        return self._record(TxKind.FEE, -self.MONTHLY_FEE, at, "monthly account fee")


class SavingsAccount(Account):
    kind = "savings"
    MAX_WITHDRAWALS_PER_MONTH = 3

    def __init__(self, number: str, owner: str, annual_rate: float = 0.04):
        super().__init__(number, owner)
        if not 0 <= annual_rate <= 0.25:
            raise ValueError("Interest rate must be between 0% and 25%.")
        self.annual_rate = annual_rate

    def withdrawals_in(self, month: str) -> int:
        return sum(1 for t in self._transactions if t.amount < 0 and t.kind in (TxKind.WITHDRAWAL, TxKind.TRANSFER_OUT)
                   and t.at.strftime("%Y-%m") == month)

    def _check_withdrawal(self, cents, at):
        if cents > self._balance:
            raise InsufficientFundsError(f"Savings can't go negative (balance ${self._balance / 100:,.2f}).")
        if self.withdrawals_in(at.strftime("%Y-%m")) >= self.MAX_WITHDRAWALS_PER_MONTH:
            raise WithdrawalLimitError(f"Savings allow {self.MAX_WITHDRAWALS_PER_MONTH} withdrawals per month.")

    def month_end(self, at):
        interest = round(self._balance * self.annual_rate / 12)
        if interest <= 0:
            return None
        return self._record(TxKind.INTEREST, interest, at, f"interest at {self.annual_rate:.2%} a year")
