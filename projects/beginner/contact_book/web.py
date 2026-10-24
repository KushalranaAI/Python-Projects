"""Flask interface with add/edit forms, search, CSV export and import."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from projects.ui_kit import data_path, run_standalone

from .contacts import Contact, ContactNotFoundError, ValidationError
from .storage import JsonContactStore

bp = Blueprint("contact_book", __name__, template_folder="templates")


def store() -> JsonContactStore:
    return JsonContactStore(data_path("contacts.json"))


def form_fields(form) -> dict:
    birthday = form.get("birthday", "").strip()
    return {"name": form.get("name", ""), "email": form.get("email", ""), "phone": form.get("phone", ""),
            "company": form.get("company", ""), "birthday": date.fromisoformat(birthday) if birthday else None,
            "tags": form.get("tags", "").split(","), "favorite": "favorite" in form}


@bp.get("/")
def index():
    book = store().load()
    query, tag = request.args.get("q", ""), request.args.get("tag") or None
    editing = None
    if request.args.get("edit"):
        try:
            editing = book.get(request.args["edit"])
        except ContactNotFoundError:
            pass
    return render_template("contact_book/index.html", contacts=book.search(query, tag), total=len(book), query=query,
                           tag=tag, tags=book.tags(), birthdays=book.upcoming_birthdays(date.today()), editing=editing,
                           errors={}, form={})


@bp.post("/save")
def save():
    s = store()
    book = s.load()
    contact_id = request.form.get("id")
    try:
        fields = form_fields(request.form)
        if contact_id:
            book.update(contact_id, **fields)
        else:
            book.add(Contact(**fields))
        s.save(book)
        flash(f"Saved {fields['name'].strip()}", "success")
        return redirect(url_for(".index"))
    except ValidationError as error:
        errors = error.errors
    except ValueError:
        errors = {"birthday": "use the date picker (YYYY-MM-DD)"}
    return render_template("contact_book/index.html", contacts=book.search(), total=len(book), query="", tag=None,
                           tags=book.tags(), birthdays=[], editing=book.get(contact_id) if contact_id else None,
                           errors=errors, form=request.form), 400


@bp.post("/<contact_id>/delete")
def delete(contact_id: str):
    s = store()
    book = s.load()
    try:
        flash(f"Deleted {book.remove(contact_id).name}", "success")
        s.save(book)
    except ContactNotFoundError:
        flash("That contact no longer exists.", "error")
    return redirect(url_for(".index"))


@bp.get("/export.csv")
def export_csv():
    return Response(store().load().to_csv(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=contacts.csv"})


@bp.post("/import")
def import_csv():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("Choose a CSV file first.", "error")
        return redirect(url_for(".index"))
    s = store()
    book = s.load()
    added, problems = book.import_csv(upload.read().decode("utf-8-sig"))
    s.save(book)
    flash(f"Imported {added} contact(s).", "success")
    for problem in problems[:10]:
        flash(problem, "error")
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Contact Book")
