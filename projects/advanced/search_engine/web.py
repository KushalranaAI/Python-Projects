"""Flask interface: search this repository's guides and project write-ups."""

from __future__ import annotations

from functools import lru_cache

from flask import Blueprint, render_template, request

from projects.ui_kit import REPO_ROOT, run_standalone

from .index import InvertedIndex, load_folder
from .ranking import RANKERS
from .search import Query, SearchEngine

bp = Blueprint("search_engine", __name__, template_folder="templates")


@lru_cache(maxsize=1)
def course_index() -> InvertedIndex:
    """Index the course's Markdown once per server start."""
    return load_folder(REPO_ROOT, ("*.md",))


@bp.get("/")
def index():
    q = request.args.get("q", "").strip()[:200]
    ranker_name = request.args.get("ranker", "bm25")
    idx = course_index()
    engine = SearchEngine(idx, RANKERS.get(ranker_name, RANKERS["bm25"]))
    hits = engine.search(q) if q else []
    return render_template("search_engine/index.html", q=q, hits=hits, idx=idx, ranker=ranker_name, rankers=list(RANKERS),
                           parsed=Query.parse(q) if q else None,
                           examples=["inheritance polymorphism", '"pure function" test', "sqlite -expense", "dataclass frozen", "streak"])


if __name__ == "__main__":
    run_standalone(bp, "Search Engine")
