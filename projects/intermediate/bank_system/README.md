---
title: Bank Account System
order: 4
icon: 🏦
time: 4 hours
summary: Checking and savings accounts with overdrafts, withdrawal limits, interest, fees and atomic transfers, built on encapsulation, abstract classes and the template-method pattern.
python_skills:
  - Read-only properties and private attributes (_balance)
  - Returning tuples to protect internal lists
  - itertools.count for id generation
  - getattr for dispatching by name
  - datetime and month keys
oop_concepts:
  - Encapsulation - state only changes through methods
  - Template method pattern (withdraw → _check_withdrawal hook)
  - Abstract methods for per-type behaviour (month_end)
  - Factory method (Bank.open_account)
  - Event sourcing - rebuild state by replaying transactions
clean_code:
  - Make invalid states unrepresentable (no public balance setter)
  - Fail before changing anything (validate, then mutate)
  - Compensating action to keep transfers atomic
  - Integer cents, never floats, for money
features:
  - Open checking (optional overdraft) and savings accounts
  - Deposits, withdrawals, transfers with full statements
  - Savings - no overdraft, 3 withdrawals per month, monthly interest
  - Checking - $5 monthly fee waived above $1,000
  - Month-end processing that each account type handles differently
architecture: |
  classDiagram
    class Account {
      <<abstract>>
      +number str
      +owner str
      -_balance int
      -_transactions list
      +balance int
      +transactions tuple
      +deposit(cents, at) Transaction
      +withdraw(cents, at) Transaction
      #_check_withdrawal(cents, at)*
      +month_end(at)* Transaction
      +statement(month) list
    }
    class CheckingAccount {
      +overdraft_limit int
      +available int
      #_check_withdrawal()
      +month_end() fee
    }
    class SavingsAccount {
      +annual_rate float
      +withdrawals_in(month) int
      #_check_withdrawal()
      +month_end() interest
    }
    class Transaction {
      <<frozen>>
      +kind TxKind
      +amount int
      +balance_after int
      +at datetime
      +memo str
    }
    class Bank {
      -_accounts dict
      +open_account(kind, owner) Account
      +get(number) Account
      +transfer(src, dst, cents, at)
      +run_month_end(at) list
    }
    Account <|-- CheckingAccount
    Account <|-- SavingsAccount
    Account *-- Transaction
    Bank o-- Account
flow: |
  flowchart TD
    W["withdraw(cents) - template method (fixed)"] --> V[check_amount: positive int]
    V --> H["_check_withdrawal(cents) - hook"]
    H -->|Checking| C{"cents ≤ balance + overdraft?"}
    H -->|Savings| S{"cents ≤ balance and < 3 this month?"}
    C -->|no| E[raise BankError]
    S -->|no| E
    C -->|yes| R["_record: update balance + append Transaction"]
    S -->|yes| R
steps:
  - title: Protect the balance
    files: [accounts.py]
    body: |
      `_balance` starts with an underscore ("internal") and `balance` is a **property without a setter**, so
      `account.balance = 10**9` raises `AttributeError`. `transactions` returns a *tuple copy*, so nobody can append fake
      history. Money only moves through `deposit` and `withdraw`.
  - title: One method records everything
    files: [accounts.py]
    body: |
      Both public methods end in `_record`, which updates the balance and appends an immutable `Transaction` with the
      balance after it. The statement is therefore always consistent with the balance.
  - title: Template method + hooks
    files: [accounts.py]
    body: |
      `withdraw` is the same algorithm for every account: validate the amount → check account-specific rules → record.
      Only the middle step varies, so it's an abstract **hook** `_check_withdrawal` that each subclass implements:
      overdraft for checking, no-negative and 3-per-month for savings.
  - title: Polymorphic month-end
    files: [accounts.py, bank.py]
    body: |
      `month_end` is abstract too: savings add interest (balance × rate / 12), checking charges a fee unless the balance is
      high. `Bank.run_month_end` loops over all accounts and calls the same method on each.
  - title: Atomic transfers
    files: [bank.py]
    body: |
      A transfer is two operations. We do the withdrawal first, since it's the one that can fail. If the deposit then failed,
      a **compensating** deposit puts the money back, so a transfer never half-happens. The test checks balances are
      unchanged after a failed transfer.
  - title: Store history, rebuild state
    files: [storage.py]
    body: |
      Only transactions are saved. Loading **replays** them through `_record`, which is called *event sourcing*: the log is the
      source of truth, and the balance is derived. It's how real ledgers and many databases work internally.
  - title: Test the invariants
    files: [tests/test_bank.py]
    body: |
      The tests check that the balance can't be set, invalid amounts (0, negative, float, even `True`) are rejected,
      the overdraft and withdrawal limits hold, transfers are atomic, month-end is polymorphic, and the round trip works.
exercises:
  - Add a `FixedDepositAccount` that can't be withdrawn from before its maturity date. Only `accounts.py` and `ACCOUNT_TYPES` should change.
  - Add **daily withdrawal limits** for checking. Where does that rule go?
  - Add a `Customer` class that owns several accounts and shows a net worth.
  - Write a test that replays 1,000 random valid operations and checks that every account's balance equals the sum of its transactions.
---

## Encapsulation, concretely

| Without encapsulation | With encapsulation |
|---|---|
| `account.balance -= 50` anywhere in the code | `account.withdraw(5000, now)` - one place, rules enforced |
| statement and balance can disagree | balance is updated only by `_record`, alongside the statement |
| rules copied into every caller | rules in the account class, chosen by its type |

> Python's underscore is a *convention*, not a lock: `account._balance = 5` still runs. Encapsulation in Python is about
> making the right way obvious and the wrong way look wrong.
