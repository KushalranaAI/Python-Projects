"""Flask interface: accounts overview, money movements, statements and month-end processing."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from projects.ui_kit import data_path, run_standalone

from . import storage
from .accounts import BankError

bp = Blueprint("bank_system", __name__, template_folder="templates")


def path():
    return data_path("bank.json")


def to_cents(text: str) -> int:
    try:
        return int(Decimal(text.replace(",", "")) * 100)
    except InvalidOperation:
        raise BankError(f"'{text}' is not an amount.") from None


@bp.get("/")
def index():
    bank = storage.load(path())
    selected = request.args.get("account")
    account = bank.get(selected) if selected and selected in {a.number for a in bank.accounts} else None
    return render_template("bank_system/index.html", bank=bank, account=account)


@bp.post("/do")
def do():
    bank = storage.load(path())
    action, now = request.form.get("action"), datetime.now()
    try:
        if action == "open":
            options = {}
            if request.form.get("type") == "checking" and request.form.get("overdraft"):
                options["overdraft_limit"] = to_cents(request.form["overdraft"])
            acc = bank.open_account(request.form.get("type", ""), request.form.get("owner", ""), **options)
            flash(f"Opened {acc.kind} account {acc.number} for {acc.owner}.", "success")
        elif action in ("deposit", "withdraw"):
            account = bank.get(request.form.get("number", ""))
            getattr(account, action)(to_cents(request.form.get("amount", "")), now, request.form.get("memo", ""))
            flash(f"{action.title()} done. New balance ${account.balance / 100:,.2f}.", "success")
        elif action == "transfer":
            bank.transfer(request.form.get("source", ""), request.form.get("target", ""), to_cents(request.form.get("amount", "")), now)
            flash("Transfer complete.", "success")
        elif action == "month_end":
            results = bank.run_month_end(now)
            flash(f"Month-end processed: {len(results)} interest/fee entries.", "success")
        storage.save(bank, path())
    except (BankError, ValueError) as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Bank Account System")
