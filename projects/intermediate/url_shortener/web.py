"""Flask interface. /go/<code> is the actual redirect a short link points to."""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from projects.ui_kit import data_path, run_standalone

from .shortener import LinkNotFoundError, Shortener

bp = Blueprint("url_shortener", __name__, template_folder="templates")


def service() -> Shortener:
    return Shortener(data_path("links.db"))


@bp.get("/")
def index():
    return render_template("url_shortener/index.html", links=service().all_links(), latest=request.args.get("new"))


@bp.post("/shorten")
def shorten():
    try:
        link = service().shorten(request.form.get("url", ""), request.form.get("alias") or None)
        return redirect(url_for(".index", new=link.code))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for(".index"))


@bp.get("/go/<code>")
def go(code: str):
    try:
        return redirect(service().resolve(code, request.referrer), code=302)   # 302: browsers ask us every time, so we count every click
    except LinkNotFoundError:
        abort(404)


@bp.get("/stats/<code>")
def stats(code: str):
    try:
        return render_template("url_shortener/stats.html", stats=service().stats(code))
    except LinkNotFoundError:
        abort(404)


@bp.post("/delete/<code>")
def delete(code: str):
    try:
        service().delete(code)
    except LinkNotFoundError:
        pass
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "URL Shortener")
