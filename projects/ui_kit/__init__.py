"""Shared helpers every project uses for its web UI and its data files.

Keeping these in one place means each project's own code stays focused on its problem.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Blueprint, Flask

REPO_ROOT = Path(__file__).resolve().parents[2]

# Templates-only blueprint: makes project_base.html, project_widgets.html and _flashes.html available to any app.
kit = Blueprint("ui_kit", __name__, template_folder="templates")


def data_dir() -> Path:
    """Where projects keep their files (JSON, SQLite). Override with the PP_DATA_DIR environment variable."""
    path = Path(os.environ.get("PP_DATA_DIR", REPO_ROOT / "instance"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_path(filename: str) -> Path:
    return data_dir() / filename


def create_standalone_app(blueprint: Blueprint, title: str) -> Flask:
    """Wrap one project's blueprint in a tiny Flask app, so the project can run on its own."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))
    app.config["PROJECT_TITLE"] = title
    app.register_blueprint(kit)
    app.register_blueprint(blueprint)
    return app


def run_standalone(blueprint: Blueprint, title: str, port: int = 5001) -> None:
    app = create_standalone_app(blueprint, title)
    print(f"{title} running on http://127.0.0.1:{port}/  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=port, debug=True)
