"""Flask interface with an on-screen keyboard and an SVG gallows."""

from __future__ import annotations

import string

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .game import GameOverError, GuessResult, HangmanGame
from .words import CATEGORIES

bp = Blueprint("hangman", __name__, template_folder="templates")
KEY = "hangman"


def current() -> HangmanGame | None:
    return HangmanGame.from_dict(session[KEY]) if KEY in session else None


@bp.get("/")
def index():
    return render_template("hangman/index.html", game=current(), categories=list(CATEGORIES), alphabet=string.ascii_lowercase)


@bp.post("/new")
def new():
    session[KEY] = HangmanGame.random(request.form.get("category") or None).to_dict()
    return redirect(url_for(".index"))


@bp.post("/guess")
def guess():
    game = current()
    if game:
        try:
            if request.form.get("word"):
                if not game.guess_word(request.form["word"]):
                    flash("That's not the word - it cost you a life.", "error")
            else:
                if game.guess(request.form.get("letter", "")) is GuessResult.REPEAT:
                    flash("You already tried that letter.", "info")
        except (ValueError, GameOverError) as error:
            flash(str(error), "error")
        session[KEY] = game.to_dict()
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Hangman")
