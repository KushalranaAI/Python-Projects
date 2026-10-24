"""Flask interface: the same GuessingGame, stored in the browser session between requests."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .game import Difficulty, GameOverError, GuessingGame, optimal_attempts

bp = Blueprint("number_guessing", __name__, template_folder="templates")
SESSION_KEY = "number_guessing"


def current_game() -> GuessingGame | None:
    data = session.get(SESSION_KEY)
    return GuessingGame.from_dict(data) if data else None


def save(game: GuessingGame) -> None:
    session[SESSION_KEY] = game.to_dict()


@bp.get("/")
def index():
    game = current_game()
    return render_template("number_guessing/index.html", game=game, difficulties=list(Difficulty),
                           optimal=optimal_attempts(game.high) if game else None)


@bp.post("/new")
def new_game():
    difficulty = Difficulty[request.form.get("difficulty", "EASY")]
    save(GuessingGame.new(difficulty))
    return redirect(url_for(".index"))


@bp.post("/guess")
def guess():
    game = current_game()
    if game is None:
        return redirect(url_for(".index"))
    try:
        feedback = game.guess(int(request.form["number"]))
        flash(f"{request.form['number']}: {feedback.value}", "success" if game.is_won else "info")
    except (ValueError, KeyError):
        flash(f"Enter a whole number between 1 and {game.high}.", "error")
    except GameOverError as error:
        flash(str(error), "error")
    save(game)
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Number Guessing Game")
