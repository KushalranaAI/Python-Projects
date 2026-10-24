"""The learning hub: a Flask app that serves the guides, the project pages and every project's live UI."""

from __future__ import annotations

import importlib
import os
import re
import secrets

from flask import Blueprint, Flask, abort, jsonify, render_template, request

from projects.ui_kit import kit

from . import catalog
from .rendering import highlight_file, mermaid, pygments_css, render_markdown
from .runner import run_tests

LOCAL_HOST = re.compile(r"^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")
LEVEL_INFO = {
    "beginner": ("🌱", "Beginner", "Functions, loops, collections, files and your first classes."),
    "intermediate": ("🌿", "Intermediate", "Databases, inheritance, custom exceptions and layered design."),
    "advanced": ("🌳", "Advanced", "Parsers, design patterns, state machines, search and REST APIs."),
}

site = Blueprint("site", __name__)


@site.app_context_processor
def inject_globals():
    blueprint_project = catalog.project(request.blueprint) if request.blueprint else None
    return {"catalog": catalog, "LEVEL_INFO": LEVEL_INFO, "current_project": blueprint_project}


@site.app_template_filter("markdown")
def markdown_filter(text: str):
    return render_markdown(text or "")


@site.app_template_filter("mermaid")
def mermaid_filter(text: str):
    return mermaid(text or "")


@site.route("/")
def home():
    return render_template("index.html", levels=catalog.by_level(), guides=catalog.guides())


@site.route("/guides/")
def guides():
    return render_template("guides.html", guides=catalog.guides())


@site.route("/guides/<slug>")
def guide(slug: str):
    item = catalog.guide(slug) or abort(404)
    items = list(catalog.guides())
    i = items.index(item)
    return render_template("guide.html", guide=item, prev=items[i - 1] if i else None,
                           next=items[i + 1] if i + 1 < len(items) else None)


@site.route("/projects/<slug>")
def project(slug: str):
    item = catalog.project(slug) or abort(404)
    files = [(f.relative_to(item.path).as_posix(), highlight_file(f)) for f in item.source_files()]
    all_projects = list(catalog.projects())
    i = all_projects.index(item)
    return render_template("project.html", project=item, files=files,
                           prev=all_projects[i - 1] if i else None,
                           next=all_projects[i + 1] if i + 1 < len(all_projects) else None)


@site.route("/api/projects/<slug>/tests", methods=["POST"])
def project_tests(slug: str):
    # Only this machine's browser may run code: check the Host and Origin headers and require JSON.
    origin = request.headers.get("Origin", "")
    origin_host = re.sub(r"^https?://", "", origin) if origin else None
    if not LOCAL_HOST.match(request.host) or (origin_host is not None and not LOCAL_HOST.match(origin_host)) \
            or not request.is_json:
        abort(403)
    item = catalog.project(slug) or abort(404)
    return jsonify(run_tests(item))


@site.route("/assets/pygments.css")
def pygments_stylesheet():
    return pygments_css(), 200, {"Content-Type": "text/css; charset=utf-8"}


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))
    app.register_blueprint(site)
    app.register_blueprint(kit)  # after the hub, so hub/templates/project_base.html wins over the standalone one
    for item in catalog.projects():
        module = importlib.import_module(f"{item.package}.web")
        app.register_blueprint(module.bp, url_prefix=f"/play/{item.slug}")

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404

    return app
