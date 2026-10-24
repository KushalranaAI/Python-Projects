"""Documents and the inverted index: term → {doc_id: [positions]}. Looking up a word is one dict access."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .text import tokens_with_positions


@dataclass(frozen=True)
class Document:
    id: int
    title: str
    text: str
    source: str = ""


@dataclass
class InvertedIndex:
    documents: dict[int, Document] = field(default_factory=dict)
    postings: dict[str, dict[int, list[int]]] = field(default_factory=lambda: defaultdict(dict))
    lengths: dict[int, int] = field(default_factory=dict)

    def add(self, doc: Document) -> None:
        if doc.id in self.documents:
            raise ValueError(f"Document {doc.id} is already indexed.")
        self.documents[doc.id] = doc
        # The title is indexed twice (a cheap boost). Big position gaps stop a "phrase" from spanning title and body.
        tokens = (tokens_with_positions(doc.title) + tokens_with_positions(doc.title, start=10_000)
                  + tokens_with_positions(doc.text, start=20_000))
        self.lengths[doc.id] = len(tokens)
        for term, position in tokens:
            self.postings[term].setdefault(doc.id, []).append(position)

    def __len__(self) -> int:
        return len(self.documents)

    @property
    def average_length(self) -> float:
        return sum(self.lengths.values()) / len(self.lengths) if self.lengths else 0.0

    def document_frequency(self, term: str) -> int:
        return len(self.postings.get(term, {}))

    def term_frequency(self, term: str, doc_id: int) -> int:
        return len(self.postings.get(term, {}).get(doc_id, ()))

    def docs_with(self, term: str) -> set[int]:
        return set(self.postings.get(term, {}))

    def has_phrase(self, doc_id: int, phrase_terms: list[str]) -> bool:
        """True if the terms appear at consecutive positions: term k at position start + k."""
        if not phrase_terms:
            return True
        position_sets = [set(self.postings.get(term, {}).get(doc_id, ())) for term in phrase_terms]
        return any(all(start + k in positions for k, positions in enumerate(position_sets)) for start in position_sets[0])

    @property
    def vocabulary_size(self) -> int:
        return len(self.postings)


def markdown_title(text: str, fallback: str) -> str:
    front = re.search(r"^title:\s*(.+)$", text, re.M)
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    return (front or heading).group(1).strip().strip('"') if (front or heading) else fallback


MERMAID = re.compile(r"```mermaid.*?```", re.S)


def readable_text(raw: str) -> str:
    """The prose of a Markdown file: frontmatter text fields + body, without diagram source code."""
    body, parts = raw, []
    if raw.startswith("---\n") and raw.count("---\n") >= 2:
        _, front, body = raw.split("---\n", 2)
        try:
            import yaml

            meta = yaml.safe_load(front) or {}
        except Exception:                                   # not YAML after all - index it as plain text
            meta, body = {}, raw
        for key in ("summary", "problem"):
            parts.append(str(meta.get(key, "")))
        for key in ("features", "exercises"):
            parts += [str(x) for x in meta.get(key, []) or []]
        for step in meta.get("steps", []) or []:
            parts += [str(step.get("title", "")), str(step.get("body", ""))]
    parts.append(MERMAID.sub(" ", body))
    return "\n".join(p for p in parts if p)


def load_folder(folder: Path, patterns: tuple[str, ...] = ("*.md", "*.txt")) -> InvertedIndex:
    index = InvertedIndex()
    files = sorted({p for pattern in patterns for p in Path(folder).rglob(pattern) if ".git" not in p.parts})
    for i, path in enumerate(files, start=1):
        raw = path.read_text(encoding="utf-8", errors="replace")
        index.add(Document(i, markdown_title(raw, path.stem), readable_text(raw), str(path.relative_to(folder))))
    return index
