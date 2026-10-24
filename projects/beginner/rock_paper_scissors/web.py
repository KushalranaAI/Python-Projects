"""Flask interface: the session stores rules, opponent and history; the Match is rebuilt for each request."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .game import Match
from .players import STRATEGIES, make_strategy
from .rules import RULESETS, Outcome

bp = Blueprint("rock_paper_scissors", __name__, template_folder="templates")
KEY = "rps"
ICONS = {"rock": "✊", "paper": "✋", "scissors": "✌️", "lizard": "🦎", "spock": "🖖"}


def load_match() -> Match:
    state = session.get(KEY, {"rules": "classic", "opponent": "frequency", "history": []})
    match = Match(make_strategy(state["opponent"], RULESETS[state["rules"]]), [tuple(h) for h in state["history"]])
    return match


def save(match: Match) -> None:
    session[KEY] = {"rules": match.opponent.rules.name, "opponent": match.opponent.name, "history": match.history}


@bp.get("/")
def index():
    match = load_match()
    rounds = match.rounds
    return render_template("rock_paper_scissors/index.html", match=match, rounds=rounds[::-1][:12], last=rounds[-1] if rounds else None,
                           score=match.score, Outcome=Outcome, strategies=STRATEGIES, rulesets=RULESETS, icons=ICONS)


@bp.post("/play")
def play():
    match = load_match()
    try:
        match.play(request.form["move"])
        save(match)
    except (KeyError, ValueError):
        pass
    return redirect(url_for(".index"))


@bp.post("/setup")
def setup():
    rules = request.form.get("rules", "classic")
    opponent = request.form.get("opponent", "frequency")
    if rules in RULESETS and opponent in STRATEGIES:
        session[KEY] = {"rules": rules, "opponent": opponent, "history": []}
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Rock Paper Scissors")
