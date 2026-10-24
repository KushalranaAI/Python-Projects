"""Flask interface: a single stateless form; the bill is rebuilt from the form on every submit."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request

from projects.ui_kit import run_standalone

from .bill import Bill, format_cents, parse_items

bp = Blueprint("bill_splitter", __name__, template_folder="templates")
EXAMPLE = {"people": "Ana Ben Chloe", "items": "Pizza, 24.50\nPasta, 16, Ben\nWine, 30, Ana Chloe\nDessert, 9.90, Ana Ben",
           "tax": "8", "tip": "15", "payer": "Ana"}


@bp.route("/", methods=["GET", "POST"])
def index():
    form = request.form if request.method == "POST" else EXAMPLE
    error, bill, shares, settle = None, None, [], []
    try:
        bill = Bill(form.get("people", "").split(), tax_percent=Decimal(form.get("tax") or "0"),
                    tip_percent=Decimal(form.get("tip") or "0"))
        parse_items(form.get("items", ""), bill)
        shares = bill.shares()
        if form.get("payer"):
            settle = bill.settle(form["payer"].strip())
    except (ValueError, InvalidOperation) as exc:
        error = str(exc) or "Please check the numbers."
    return render_template("bill_splitter/index.html", form=form, bill=bill, shares=shares, settle=settle,
                           error=error, money=format_cents)


if __name__ == "__main__":
    run_standalone(bp, "Bill Splitter")
