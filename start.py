#!/usr/bin/env python3
"""Start the learning website with one command:

    python start.py                  # installs missing packages, opens http://127.0.0.1:5050
    python start.py --port 8000 --no-browser
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = {"flask": "flask", "markdown": "markdown", "pygments": "pygments", "yaml": "pyyaml", "pytest": "pytest"}


def ensure_packages() -> None:
    missing = [pkg for module, pkg in REQUIRED.items() if importlib.util.find_spec(module) is None]
    if not missing:
        return
    print(f"Installing missing packages: {', '.join(missing)}")
    if sys.prefix == sys.base_prefix:
        print("  tip: a virtual environment keeps them separate - python -m venv .venv")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)


def open_browser_when_ready(url: str) -> None:
    for _ in range(60):
        try:
            urllib.request.urlopen(url, timeout=1)
            webbrowser.open(url)
            return
        except OSError:
            time.sleep(0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Python Projects learning website.")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        sys.exit(f"Python 3.10 or newer is required (you have {sys.version.split()[0]}).")
    ensure_packages()
    sys.path.insert(0, str(ROOT))
    from hub import create_app

    url = f"http://127.0.0.1:{args.port}"
    print(f"\n🐍 Python Projects is running at {url}  (Ctrl+C to stop)\n")
    if not args.no_browser:
        threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    # 127.0.0.1 only: the site can run each project's tests on your machine, so keep it off the network.
    create_app().run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
