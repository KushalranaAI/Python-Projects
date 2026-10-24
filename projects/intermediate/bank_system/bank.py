"""The Bank: opens accounts, finds them, moves money between them atomically, runs month-end."""

from __future__ import annotations

import itertools
from datetime import datetime

from .accounts import Account, BankError, CheckingAccount, SavingsAccount, Transaction, TxKind

ACCOUNT_TYPES: dict[str, type[Account]] = {"checking": CheckingAccount, "savings": SavingsAccount}


class AccountNotFoundError(BankError):
    pass


class Bank:
    def __init__(self, name: str = "PyBank"):
        self.name = name
        self._accounts: dict[str, Account] = {}
        self._numbers = itertools.count(1001)

    def open_account(self, kind: str, owner: str, **options) -> Account:
        """Factory: the caller names a type, the bank picks the class and the account number."""
        try:
            cls = ACCOUNT_TYPES[kind]
        except KeyError:
            raise BankError(f"Unknown account type {kind!r}.") from None
        account = cls(f"{kind[:3].upper()}-{next(self._numbers)}", owner, **options)
        self._accounts[account.number] = account
        return account

    def get(self, number: str) -> Account:
        try:
            return self._accounts[number]
        except KeyError:
            raise AccountNotFoundError(f"No account {number}.") from None

    @property
    def accounts(self) -> list[Account]:
        return list(self._accounts.values())

    def accounts_of(self, owner: str) -> list[Account]:
        return [a for a in self._accounts.values() if a.owner.lower() == owner.lower()]

    @property
    def total_deposits(self) -> int:
        return sum(a.balance for a in self._accounts.values())

    def transfer(self, source: str, target: str, cents: int, at: datetime, memo: str = "") -> tuple[Transaction, Transaction]:
        """Both legs succeed or neither does. The withdrawal runs first because it's the one that can fail."""
        if source == target:
            raise BankError("Choose two different accounts.")
        src, dst = self.get(source), self.get(target)
        out = src.withdraw(cents, at, memo or f"to {dst.number}", kind=TxKind.TRANSFER_OUT)
        try:
            inn = dst.deposit(cents, at, memo or f"from {src.number}", kind=TxKind.TRANSFER_IN)
        except BankError:
            src.deposit(cents, at, "transfer reversed")    # compensate so no money disappears
            raise
        return out, inn

    def run_month_end(self, at: datetime) -> list[tuple[Account, Transaction]]:
        """Polymorphism: each account decides what month-end means for it."""
        results = []
        for account in self._accounts.values():
            tx = account.month_end(at)
            if tx:
                results.append((account, tx))
        return results
