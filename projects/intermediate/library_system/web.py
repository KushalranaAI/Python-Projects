"""Flask interface with a 'time machine' to try the fine rules without waiting two weeks."""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from projects.ui_kit import data_path, run_standalone

from . import storage
from .items import ITEM_TYPES
from .library import LibraryError

bp = Blueprint("library_system", __name__, template_folder="templates")


def path():
    return data_path("library.json")


def today() -> date:
    return date.today() + timedelta(days=session.get("library_days_ahead", 0))


@bp.get("/")
def index():
    lib = storage.load(path())
    query, kind = request.args.get("q", ""), request.args.get("kind") or None
    return render_template("library_system/index.html", lib=lib, items=lib.search(query, kind), query=query, kind=kind,
                           kinds=list(ITEM_TYPES), today=today(), days_ahead=session.get("library_days_ahead", 0),
                           overdue=lib.overdue(today()))


@bp.post("/action")
def action():
    lib = storage.load(path())
    item_id, member_id, verb = request.form.get("item_id", ""), request.form.get("member_id", ""), request.form.get("verb")
    try:
        if verb == "checkout":
            loan = lib.checkout(item_id, member_id, today())
            flash(f"{lib.member(member_id).name} borrowed “{lib.item(item_id).title}”, due {loan.due_on:%d %b}.", "success")
        elif verb == "return":
            fine = lib.return_item(item_id, today())
            flash(f"Returned “{lib.item(item_id).title}”." + (f" Late fine ${fine / 100:.2f}." if fine else ""), "success")
        elif verb == "hold":
            flash(f"{lib.member(member_id).name} is #{lib.place_hold(item_id, member_id)} in the queue.", "success")
        elif verb == "pay":
            member = lib.member(member_id)
            lib.pay_fine(member_id, member.fines_cents)
            flash(f"{member.name} paid ${member.fines_cents / 100:.2f}.", "success")
        storage.save(lib, path())
    except LibraryError as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for(".index"))


@bp.post("/time-machine")
def time_machine():
    session["library_days_ahead"] = max(0, min(365, int(request.form.get("days", 0) or 0)))
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Library Management System")
