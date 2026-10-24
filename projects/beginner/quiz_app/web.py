"""Flask interface: the session stores question ids and answers; the bank is loaded once at import."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .quiz import QuestionBank, QuizSession

bp = Blueprint("quiz_app", __name__, template_folder="templates")
bank = QuestionBank.from_json()
KEY = "quiz_app"


def current() -> QuizSession | None:
    return QuizSession.from_dict(bank, session[KEY]) if KEY in session else None


@bp.get("/")
def index():
    quiz = current()
    last = quiz.results[-1] if quiz and quiz.choices and request.args.get("feedback") else None
    return render_template("quiz_app/index.html", quiz=quiz, bank=bank, last=last, letters="ABCD")


@bp.post("/start")
def start():
    category = request.form.get("category") or None
    session[KEY] = QuizSession.start(bank, int(request.form.get("count", 10)), category).to_dict()
    return redirect(url_for(".index"))


@bp.post("/answer")
def answer():
    quiz = current()
    if quiz and not quiz.finished:
        try:
            quiz.answer(int(request.form["choice"]))
            session[KEY] = quiz.to_dict()
        except (KeyError, ValueError):
            pass
    return redirect(url_for(".index", feedback=1))


@bp.post("/reset")
def reset():
    session.pop(KEY, None)
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Python Quiz")
