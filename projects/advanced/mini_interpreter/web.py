"""Flask interface: a notebook-style REPL that shows the tokens, the tree and the result of each line."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .interpreter import Interpreter, format_result
from .lexer import LangError, tokenize
from .nodes import to_mermaid, to_source, tree_lines

bp = Blueprint("mini_interpreter", __name__, template_folder="templates")
KEY = "mini_interpreter"
EXAMPLES = ["1 + 2 * 3", "(1 + 2) * 3", "2 ^ 3 ^ 2", "-2 ^ 2", "r = 5", "area = pi * r^2", "def hyp(a, b) = sqrt(a^2 + b^2)",
            "hyp(3, 4)", "def fact(n) = n * fact(n - 1)", "max(1, 7, 3) % 4", "1 / 0", "2 +* 3"]


def restore() -> Interpreter:
    """Rebuild the interpreter by re-running the successful lines - the session only stores text."""
    interp = Interpreter()
    for entry in session.get(KEY, []):
        if entry["ok"]:
            try:
                interp.run(entry["source"])
            except LangError:
                pass
    return interp


@bp.get("/")
def index():
    entries = session.get(KEY, [])
    interp = restore()
    return render_template("mini_interpreter/index.html", entries=entries[::-1], examples=EXAMPLES,
                           variables=interp.variables, functions={k: f.source for k, f in interp.functions.items()})


@bp.post("/run")
def run():
    source = request.form.get("source", "")[:300]
    interp = restore()
    entry = {"source": source}
    try:
        entry["tokens"] = [(t.type.name, t.text) for t in tokenize(source)][:-1]
        tree, result = interp.run(source)
        entry.update(ok=True, result=format_result(result), tree="\n".join(tree_lines(tree)), mermaid=to_mermaid(tree),
                     parenthesised=to_source(tree))
    except LangError as error:
        entry.update(ok=False, error=str(error), column=error.column)
    session[KEY] = (session.get(KEY, []) + [entry])[-12:]
    return redirect(url_for(".index"))


@bp.post("/clear")
def clear():
    session.pop(KEY, None)
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Mini Interpreter")
