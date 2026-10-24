from datetime import datetime

import pytest

from projects.intermediate.bank_system import storage
from projects.intermediate.bank_system.accounts import (Account, CheckingAccount, InsufficientFundsError, InvalidAmountError,
                                                        SavingsAccount, TxKind, WithdrawalLimitError)
from projects.intermediate.bank_system.bank import AccountNotFoundError, Bank

T = datetime(2026, 3, 10, 12, 0)


@pytest.fixture
def bank() -> Bank:
    b = Bank()
    chk = b.open_account("checking", "Ada", overdraft_limit=5000)
    sav = b.open_account("savings", "Ada", annual_rate=0.06)
    chk.deposit(20000, T)
    sav.deposit(100000, T)
    return b


def test_account_is_abstract():
    with pytest.raises(TypeError):
        Account("X", "Y")


def test_balance_is_read_only(bank):
    acc = bank.get("CHE-1001")
    with pytest.raises(AttributeError):
        acc.balance = 10**9
    assert len(acc.transactions) == 1
    with pytest.raises(AttributeError):
        acc.transactions.append("hack")


@pytest.mark.parametrize("amount", [0, -5, 1.5, True])
def test_invalid_amounts(bank, amount):
    with pytest.raises(InvalidAmountError):
        bank.get("CHE-1001").deposit(amount, T)


def test_checking_overdraft(bank):
    chk = bank.get("CHE-1001")
    chk.withdraw(24000, T)
    assert chk.balance == -4000 and chk.available == 1000
    with pytest.raises(InsufficientFundsError):
        chk.withdraw(1001, T)


def test_savings_rules(bank):
    sav = bank.get("SAV-1002")
    with pytest.raises(InsufficientFundsError):
        sav.withdraw(100001, T)
    for _ in range(3):
        sav.withdraw(100, T)
    with pytest.raises(WithdrawalLimitError):
        sav.withdraw(100, T)
    sav.withdraw(100, datetime(2026, 4, 1))          # new month, new allowance


def test_transfer_is_atomic(bank):
    out, inn = bank.transfer("SAV-1002", "CHE-1001", 5000, T)
    assert out.kind is TxKind.TRANSFER_OUT and inn.amount == 5000
    before = (bank.get("CHE-1001").balance, bank.get("SAV-1002").balance)
    with pytest.raises(InsufficientFundsError):
        bank.transfer("CHE-1001", "SAV-1002", 10**8, T)
    assert (bank.get("CHE-1001").balance, bank.get("SAV-1002").balance) == before
    with pytest.raises(AccountNotFoundError):
        bank.transfer("CHE-1001", "NOPE", 1, T)


def test_month_end_is_polymorphic(bank):
    results = {acc.number: tx for acc, tx in bank.run_month_end(T)}
    assert results["SAV-1002"].amount == 500                         # 1,000 × 6% / 12
    assert results["CHE-1001"].amount == -CheckingAccount.MONTHLY_FEE   # balance under $1,000
    bank.get("CHE-1001").deposit(200000, T)
    assert "CHE-1001" not in {acc.number for acc, _ in bank.run_month_end(T)}


def test_statement_filters_by_month(bank):
    chk = bank.get("CHE-1001")
    chk.deposit(100, datetime(2026, 4, 2))
    assert len(chk.statement("2026-04")) == 1 and len(chk.statement()) == 2


def test_event_sourced_round_trip(tmp_path, bank):
    bank.transfer("SAV-1002", "CHE-1001", 2500, T)
    storage.save(bank, tmp_path / "bank.json")
    again = storage.load(tmp_path / "bank.json")
    assert [(a.number, a.balance, type(a)) for a in again.accounts] == [(a.number, a.balance, type(a)) for a in bank.accounts]
    assert again.open_account("savings", "Bob").number == "SAV-1003"


def test_unknown_type():
    with pytest.raises(Exception):
        Bank().open_account("crypto", "Eve")


def test_savings_rate_validation():
    with pytest.raises(ValueError):
        SavingsAccount("S", "X", annual_rate=2)
