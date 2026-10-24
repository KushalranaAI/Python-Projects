"""Flask interface: a terminal-style transcript; the game state lives in the session as a plain dict."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .engine import Game, GameState, World, mermaid_map

bp = Blueprint("text_adventure", __name__, template_folder="templates")
world = World.load()


def load() -> tuple[Game, list[tuple[str, str]]]:
    data = session.get("adventure")
    if not data:
        game = Game(world)
        return game, [("system", world.data["intro"]), ("game", game.describe_room())]
    return Game(world, GameState.from_dict(data["state"])), [tuple(x) for x in data["log"]]


@bp.get("/")
def index():
    game, log = load()
    return render_template("text_adventure/index.html", game=game, log=log[-40:], title=world.data["title"], map=mermaid_map(game))


@bp.post("/")
def act():
    game, log = load()
    command = request.form.get("command", "").strip()[:100]
    if command:
        log += [("player", command), ("game", game.handle(command))]
    session["adventure"] = {"state": game.state.to_dict(), "log": log[-60:]}
    return redirect(url_for(".index") + "#bottom")


@bp.post("/restart")
def restart():
    session.pop("adventure", None)
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Text Adventure")
