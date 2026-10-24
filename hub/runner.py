"""Runs a project's test suite with pytest in a separate process and returns the output."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import os

from .catalog import ROOT, Project


def run_tests(project: Project, timeout: int = 120) -> dict:
    tests = project.path / "tests"
    if not tests.exists():
        return {"ok": False, "output": "This project has no tests folder yet."}
    with tempfile.TemporaryDirectory() as data_dir:  # tests must never touch your real data files
        env = {**os.environ, "PP_DATA_DIR": data_dir, "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", str(tests.relative_to(ROOT)), "-v", "--color=no", "-p", "no:cacheprovider"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "output": f"Tests did not finish within {timeout} seconds."}
    return {"ok": proc.returncode == 0, "output": proc.stdout + proc.stderr}
