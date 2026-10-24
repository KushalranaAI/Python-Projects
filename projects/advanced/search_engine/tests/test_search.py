import pytest

from projects.advanced.search_engine.index import Document, InvertedIndex, markdown_title, readable_text
from projects.advanced.search_engine.ranking import BM25Ranker, TfIdfRanker
from projects.advanced.search_engine.search import Query, SearchEngine, make_snippet
from projects.advanced.search_engine.text import stem, terms

DOCS = [
    Document(1, "Unit testing in Python", "Write a unit test for every function. Testing pure functions is easy."),
    Document(2, "Classes and objects", "A class bundles data and behaviour. Objects are instances of classes."),
    Document(3, "Test driven development", "Write the test first, then the code. Unit tests guide the design of classes."),
    Document(4, "Cooking pasta", "Boil water, add salt, cook the pasta for ten minutes. Testing doneness by tasting."),
]


@pytest.fixture
def engine() -> SearchEngine:
    index = InvertedIndex()
    for d in DOCS:
        index.add(d)
    return SearchEngine(index)


@pytest.mark.parametrize("word, root", [("testing", "test"), ("tests", "test"), ("classes", "class"), ("running", "run"),
                                        ("queries", "query"), ("class", "class"), ("is", "is"), ("organizational", "organizate")])
def test_stemmer(word, root):
    assert stem(word) == root


def test_terms_drop_stop_words_and_stem():
    assert terms("The Tests of the classes") == ["test", "class"]


def test_query_parsing():
    q = Query.parse('python "unit test" -java')
    assert q.terms == ["python", "unit", "test"] and q.phrases == [["unit", "test"]] and q.excluded == ["java"]


def test_and_semantics_and_exclusion(engine):
    assert {h.document.id for h in engine.search("test")} == {1, 3, 4}
    assert {h.document.id for h in engine.search("test class")} == {3}
    assert {h.document.id for h in engine.search("test -pasta")} == {1, 3}


def test_phrase_search(engine):
    assert {h.document.id for h in engine.search('"unit test"')} == {1, 3}
    assert engine.search('"test unit"') == []
    assert {h.document.id for h in engine.search('"unit of test"')} == {1, 3}       # stop words are ignored


def test_bm25_prefers_focused_documents(engine):
    hits = engine.search("test")
    assert hits[0].document.id in {1, 3} and hits[-1].document.id == 4
    assert all(h.score > 0 for h in hits) and hits == sorted(hits, key=lambda h: -h.score)


def test_breakdown_sums_to_score(engine):
    for ranker in (BM25Ranker(), TfIdfRanker()):
        engine.ranker = ranker
        for hit in engine.search("unit test"):
            assert sum(hit.breakdown.values()) == pytest.approx(hit.score)


def test_snippet_highlights_query_words():
    segments = make_snippet("Boil water. Then testing begins with tests.", {"test"})
    assert [t for t, marked in segments if marked] == ["testing", "tests"]


def test_duplicate_documents_rejected(engine):
    with pytest.raises(ValueError):
        engine.index.add(DOCS[0])


def test_markdown_title():
    assert markdown_title("---\ntitle: Hello\n---\n# Other", "x") == "Hello"
    assert markdown_title("# Heading here", "x") == "Heading here" and markdown_title("plain", "fallback") == "fallback"


def test_readable_text_drops_diagrams_and_keeps_prose():
    raw = "---\ntitle: T\nsummary: Short summary\narchitecture: |\n  classDiagram\n---\nBody text\n```mermaid\nflowchart LR\n```\n"
    text = readable_text(raw)
    assert "Short summary" in text and "Body text" in text and "flowchart" not in text and "classDiagram" not in text
