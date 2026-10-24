"""Flask interface: paste text or pick a sample; the report is computed on every submit (nothing is stored)."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from projects.ui_kit import run_standalone

from .analyzer import SAMPLES, analyze

bp = Blueprint("text_analyzer", __name__, template_folder="templates")
MAX_CHARS = 200_000


@bp.route("/", methods=["GET", "POST"])
def index():
    sample = request.args.get("sample")
    text = request.form.get("text", "") if request.method == "POST" else SAMPLES.get(sample, next(iter(SAMPLES.values())))
    text = text[:MAX_CHARS]
    report = analyze(text) if text.strip() else None
    return render_template("text_analyzer/index.html", text=text, report=report, samples=SAMPLES)


if __name__ == "__main__":
    run_standalone(bp, "Text Analyzer")
