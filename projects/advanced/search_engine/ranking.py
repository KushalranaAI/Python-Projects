"""Ranking functions. Each ranker is a class with score(index, query_terms, doc_id) → (score, per-term breakdown)."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from .index import InvertedIndex


class Ranker(ABC):
    name = "ranker"

    @abstractmethod
    def term_score(self, index: InvertedIndex, term: str, doc_id: int) -> float:
        """How much one query term contributes to one document's score."""

    def score(self, index: InvertedIndex, query_terms: list[str], doc_id: int) -> tuple[float, dict[str, float]]:
        parts = {t: self.term_score(index, t, doc_id) for t in dict.fromkeys(query_terms)}
        return sum(parts.values()), parts


class TfIdfRanker(Ranker):
    """tf-idf = (1 + log tf) × log(N / df), normalised by document length so long documents don't win by size alone."""

    name = "tf-idf"

    def term_score(self, index, term, doc_id):
        tf, df = index.term_frequency(term, doc_id), index.document_frequency(term)
        if not tf or not df:
            return 0.0
        idf = math.log(len(index) / df) + 1e-9
        return (1 + math.log(tf)) * idf / math.sqrt(index.lengths[doc_id])


class BM25Ranker(Ranker):
    """Okapi BM25 - the default in Lucene/Elasticsearch.

        idf · tf·(k1 + 1) / (tf + k1·(1 − b + b·|d|/avgdl))
    k1 controls how quickly repeated words stop adding score (saturation); b how much long documents are penalised.
    """

    name = "bm25"

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1, self.b = k1, b

    def term_score(self, index, term, doc_id):
        tf, df, n = index.term_frequency(term, doc_id), index.document_frequency(term), len(index)
        if not tf:
            return 0.0
        idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
        norm = 1 - self.b + self.b * index.lengths[doc_id] / index.average_length
        return idf * tf * (self.k1 + 1) / (tf + self.k1 * norm)


RANKERS = {r.name: r for r in (BM25Ranker(), TfIdfRanker())}
