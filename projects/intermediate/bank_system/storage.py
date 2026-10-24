"""Persist a Bank as JSON by saving each account's transactions and *replaying* them on load.

Replaying history to rebuild state is called event sourcing: the transaction log is the truth, balances are derived.
"""

from __future__ import annotations

import itertools
import json
from datetime import datetime
from pathlib import Path

from .accounts import TxKind
from .bank import ACCOUNT_TYPES, Bank


def save(bank: Bank, path: Path) -> None:
    data = []
    for a in bank.accounts:
        options = {"overdraft_limit": a.overdraft_limit} if a.kind == "checking" else {"annual_rate": a.annual_rate}
        data.append({"type": a.kind, "number": a.number, "owner": a.owner, "options": options,
                     "transactions": [{"kind": t.kind.name, "amount": t.amount, "at": t.at.isoformat(), "memo": t.memo}
                                      for t in a.transactions]})
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load(path: Path) -> Bank:
    bank = Bank()
    if not Path(path).exists():
        return bank
    highest = 1000
    for item in json.loads(Path(path).read_text(encoding="utf-8")):
        account = ACCOUNT_TYPES[item["type"]](item["number"], item["owner"], **item["options"])
        for t in item["transactions"]:
            account._record(TxKind[t["kind"]], t["amount"], datetime.fromisoformat(t["at"]), t["memo"])   # replay, bypassing rules
        bank._accounts[account.number] = account
        highest = max(highest, int(account.number.split("-")[1]))
    bank._numbers = itertools.count(highest + 1)
    return bank
