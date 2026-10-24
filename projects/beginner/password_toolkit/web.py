"""Flask interface: a generator form and a strength checker. Nothing is stored or logged."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from projects.ui_kit import run_standalone

from .toolkit import PasswordGenerator, PasswordPolicy, check_strength

bp = Blueprint("password_toolkit", __name__, template_folder="templates")
generator = PasswordGenerator()


@bp.route("/", methods=["GET", "POST"])
def index():
    form = request.form if request.method == "POST" else {}
    policy = PasswordPolicy(
        length=int(form.get("length", 16) or 16),
        lowercase="lowercase" in form or not form, uppercase="uppercase" in form or not form,
        digits="digits" in form or not form, symbols="symbols" in form or not form,
        exclude_ambiguous="exclude_ambiguous" in form,
    )
    words = int(form.get("words", 5) or 5)
    error, passwords, phrase = None, [], None
    try:
        passwords = [generator.password(policy) for _ in range(5)]
        phrase = generator.passphrase(words)
    except ValueError as exc:
        error = str(exc)
    # The password to check is sent with POST so it never appears in the URL or the browser history.
    report = check_strength(form["check"]) if form.get("check") else None
    return render_template("password_toolkit/index.html", policy=policy, passwords=passwords, phrase=phrase,
                           words=words, phrase_bits=generator.passphrase_entropy(words), error=error, report=report)


if __name__ == "__main__":
    run_standalone(bp, "Password Toolkit")
