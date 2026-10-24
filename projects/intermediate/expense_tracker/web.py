"""Flask interface: add expenses, browse months, see a breakdown and budget progress."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from projects.ui_kit import data_path, run_standalone

from .models import Budget, Category, Expense, money, parse_amount
from .reports import monthly_report, previous_month
from .repository import SqliteExpenseRepository

bp = Blueprint("expense_tracker", __name__, template_folder="templates")


def repo() -> SqliteExpenseRepository:
    return SqliteExpenseRepository(data_path("expenses.db"))


@bp.get("/")
def index():
    r = repo()
    month = request.args.get("month") or date.today().strftime("%Y-%m")
    totals = r.monthly_totals()
    report = monthly_report(month, r.in_month(month), r.budgets(), date.today(), totals.get(previous_month(month)))
    months = sorted(set(r.months()) | {date.today().strftime("%Y-%m"), month}, reverse=True)
    return render_template("expense_tracker/index.html", report=report, expenses=r.in_month(month), month=month, months=months,
                           categories=list(Category), money=money, today=date.today(), history=list(totals.items())[-12:],
                           budgets=r.budgets())


@bp.post("/add")
def add():
    try:
        expense = Expense(parse_amount(request.form.get("amount", "")), Category[request.form.get("category", "OTHER")],
                          request.form.get("description", ""), date.fromisoformat(request.form.get("spent_on") or date.today().isoformat()))
        repo().add(expense)
        flash(f"Added {money(expense.amount_cents)} for {expense.description}", "success")
        return redirect(url_for(".index", month=expense.month))
    except (ValueError, KeyError) as error:
        flash(str(error), "error")
        return redirect(url_for(".index"))


@bp.post("/<int:expense_id>/delete")
def delete(expense_id: int):
    if not repo().delete(expense_id):
        flash("That expense was already deleted.", "error")
    return redirect(request.referrer or url_for(".index"))


@bp.post("/budgets")
def budgets():
    r = repo()
    try:
        for category in Category:
            value = request.form.get(category.name, "").strip()
            r.set_budget(Budget(category, parse_amount(value) if value and value != "0" else 0))
        flash("Budgets saved.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Expense Tracker")
