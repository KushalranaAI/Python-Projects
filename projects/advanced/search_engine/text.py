"""Text processing shared by indexing and querying - both sides MUST use the same pipeline."""

from __future__ import annotations

import re

TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
STOP_WORDS = frozenset("""a an and are as at be but by for from has have how i if in into is it its of on or that the
their them then there these this to was what when where which who will with you your we can our not do does""".split())
# (suffix, replacement) - longest first. A tiny cousin of the Porter stemmer.
SUFFIX_RULES = [("ational", "ate"), ("ization", "ize"), ("fulness", "ful"), ("ousness", "ous"), ("iveness", "ive"),
                ("tional", "tion"), ("ments", "ment"), ("ness", ""), ("ing", ""), ("ies", "y"), ("ied", "y"),
                ("edly", ""), ("ed", ""), ("ly", ""), ("es", ""), ("s", "")]


def stem(word: str) -> str:
    """'running' → 'run', 'classes' → 'class', 'queries' → 'query'. Keeps at least 3 letters of stem."""
    if word.endswith("ss"):
        return word
    for suffix, replacement in SUFFIX_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)] + replacement
            if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "lsz":   # running → runn → run
                word = word[:-1]
            return word
    return word


def tokens_with_positions(text: str, start: int = 0) -> list[tuple[str, int]]:
    """(term, position) for every non-stop-word. Positions count only kept words, so a phrase is a run of
    consecutive positions ("unit of test" still matches "unit test" - stop words are ignored on both sides)."""
    kept = [stem(m.group()) for m in TOKEN.finditer(text.lower()) if m.group() not in STOP_WORDS]
    return [(term, start + i) for i, term in enumerate(kept)]


def terms(text: str) -> list[str]:
    return [t for t, _ in tokens_with_positions(text)]
