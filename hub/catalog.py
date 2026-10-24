"""Reads the course content from disk: project READMEs (with YAML frontmatter) and the guides."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"
GUIDES_DIR = ROOT / "guides"
LEVELS = ("beginner", "intermediate", "advanced")
SOURCE_SUFFIXES = {".py", ".html", ".json", ".css", ".js"}


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    _, meta, body = text.split("---\n", 2)
    return yaml.safe_load(meta) or {}, body


@dataclass(frozen=True)
class Step:
    title: str
    body: str
    files: tuple[str, ...] = ()


@dataclass(frozen=True)
class Project:
    slug: str
    level: str
    order: int
    title: str
    summary: str
    time: str
    icon: str
    python_skills: tuple[str, ...]
    oop_concepts: tuple[str, ...]
    clean_code: tuple[str, ...]
    features: tuple[str, ...]
    architecture: str
    flow: str
    steps: tuple[Step, ...]
    exercises: tuple[str, ...]
    body: str
    path: Path = field(repr=False)

    @property
    def package(self) -> str:
        return f"projects.{self.level}.{self.slug}"

    @property
    def number(self) -> int:
        return LEVELS.index(self.level) * 100 + self.order

    @property
    def cli_command(self) -> str:
        return f"python -m {self.package}"

    @property
    def web_command(self) -> str:
        return f"python -m {self.package}.web"

    def source_files(self) -> list[Path]:
        """Every source file of the project, domain code first, tests last."""
        files = [p for p in self.path.rglob("*") if p.is_file() and p.suffix in SOURCE_SUFFIXES and "__pycache__" not in p.parts]

        def rank(p: Path) -> tuple:
            rel = p.relative_to(self.path)
            return ("tests" in rel.parts, p.suffix == ".html", p.name in ("__init__.py", "__main__.py"),
                    p.name in ("cli.py", "web.py"), str(rel))

        return sorted(files, key=rank)


def _project(level: str, folder: Path) -> Project:
    meta, body = split_frontmatter((folder / "README.md").read_text(encoding="utf-8"))
    steps = tuple(Step(s["title"], s.get("body", ""), tuple(s.get("files", []))) for s in meta.get("steps", []))
    return Project(
        slug=folder.name, level=level, order=int(meta.get("order", 99)), title=meta.get("title", folder.name),
        summary=meta.get("summary", ""), time=meta.get("time", ""), icon=meta.get("icon", "🐍"),
        python_skills=tuple(meta.get("python_skills", [])), oop_concepts=tuple(meta.get("oop_concepts", [])),
        clean_code=tuple(meta.get("clean_code", [])), features=tuple(meta.get("features", [])),
        architecture=meta.get("architecture", ""), flow=meta.get("flow", ""), steps=steps,
        exercises=tuple(meta.get("exercises", [])), body=body, path=folder,
    )


@lru_cache(maxsize=1)
def projects() -> tuple[Project, ...]:
    found = []
    for level in LEVELS:
        for folder in sorted((PROJECTS_DIR / level).iterdir()):
            if (folder / "README.md").exists():
                found.append(_project(level, folder))
    return tuple(sorted(found, key=lambda p: p.number))


def project(slug: str) -> Project | None:
    return next((p for p in projects() if p.slug == slug), None)


def by_level() -> dict[str, list[Project]]:
    return {level: [p for p in projects() if p.level == level] for level in LEVELS}


@dataclass(frozen=True)
class Guide:
    slug: str
    order: int
    title: str
    summary: str
    icon: str
    body: str


@lru_cache(maxsize=1)
def guides() -> tuple[Guide, ...]:
    items = []
    for file in sorted(GUIDES_DIR.glob("*.md")):
        meta, body = split_frontmatter(file.read_text(encoding="utf-8"))
        items.append(Guide(file.stem, int(meta.get("order", 99)), meta.get("title", file.stem),
                           meta.get("summary", ""), meta.get("icon", "📘"), body))
    return tuple(sorted(items, key=lambda g: g.order))


def guide(slug: str) -> Guide | None:
    return next((g for g in guides() if g.slug == slug), None)
