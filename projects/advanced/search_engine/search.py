"""Query parsing, matching, ranking and snippets."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .index import Document, InvertedIndex
from .ranking import BM25Ranker, Ranker
from .text import TOKEN, stem, terms


@dataclass(frozen=True)
class Query:
    terms: list[str]               # stemmed words that must appear (AND)
    phrases: list[list[str]]       # each must appear as consecutive words
    excluded: list[str]            # must not appear

    @classmethod
    def parse(cls, text: str) -> Query:
        """  python "unit test" -java   →  terms [python, unit, test], phrases [[unit, test]], excluded [java]"""
        phrases = [terms(p) for p in re.findall(r'"([^"]+)"', text)]
        rest = re.sub(r'"[^"]*"', " ", text)
        excluded = [stem(w[1:].lower()) for w in rest.split() if w.startswith("-") and len(w) > 1]
        included = terms(" ".join(w for w in rest.split() if not w.startswith("-")))
        all_terms = included + [t for p in phrases for t in p]
        return cls(list(dict.fromkeys(all_terms)), [p for p in phrases if p], excluded)

    @property
    def empty(self) -> bool:
        return not self.terms


@dataclass(frozen=True)
class Hit:
    document: Document
    score: float
    breakdown: dict[str, float]
    snippet: list[tuple[str, bool]]          # (text, is_highlighted) segments - the template escapes them


def make_snippet(text: str, query_terms: set[str], width: int = 28) -> list[tuple[str, bool]]:
    """Pick the window of `width` words containing the most query terms, and mark those words."""
    words = list(TOKEN.finditer(text.lower()))
    if not words:
        return [(text[:200], False)]
    hits = [i for i, w in enumerate(words) if stem(w.group()) in query_terms]
    start = max(range(max(len(words) - width, 0) + 1), key=lambda s: sum(s <= h < s + width for h in hits)) if hits else 0
    window = words[start : start + width]
    begin, end = window[0].start(), window[-1].end()
    segments, cursor = [], begin
    for w in window:
        if stem(w.group()) in query_terms:
            segments += [(text[cursor : w.start()], False), (text[w.start() : w.end()], True)]
            cursor = w.end()
    segments.append((text[cursor:end], False))
    prefix = [("… ", False)] if begin > 0 else []
    suffix = [(" …", False)] if end < len(text) else []
    return prefix + [(re.sub(r"\s+", " ", s), h) for s, h in segments if s] + suffix


class SearchEngine:
    def __init__(self, index: InvertedIndex, ranker: Ranker | None = None):
        self.index = index
        self.ranker = ranker or BM25Ranker()

    def matching_documents(self, query: Query) -> set[int]:
        candidates = set.intersection(*(self.index.docs_with(t) for t in query.terms)) if query.terms else set()
        for phrase in query.phrases:
            candidates = {d for d in candidates if self.index.has_phrase(d, phrase)}
        for term in query.excluded:
            candidates -= self.index.docs_with(term)
        return candidates

    def search(self, text: str, limit: int = 10) -> list[Hit]:
        query = Query.parse(text)
        if query.empty:
            return []
        hits = []
        for doc_id in self.matching_documents(query):
            score, breakdown = self.ranker.score(self.index, query.terms, doc_id)
            doc = self.index.documents[doc_id]
            hits.append(Hit(doc, score, breakdown, make_snippet(doc.text, set(query.terms))))
        return sorted(hits, key=lambda h: (-h.score, h.document.title))[:limit]
