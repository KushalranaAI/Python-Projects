---
title: Search Engine
order: 2
icon: 🔎
time: 6 hours
summary: Build a full-text search engine over this course's own pages - tokenising, stemming, an inverted index, phrase queries, exclusions, BM25 and TF-IDF ranking, and highlighted snippets.
python_skills:
  - Inverted indexes with dicts of dicts
  - Set algebra for boolean queries (∩, −)
  - math.log and ranking formulas
  - Regex-based tokenising and a hand-written stemmer
  - functools.lru_cache for one-time work
oop_concepts:
  - Strategy pattern - interchangeable Ranker classes
  - Template method - Ranker.score sums term_score
  - Value objects (Document, Query, Hit)
  - Alternative constructor Query.parse
clean_code:
  - The same text pipeline for indexing and querying
  - Explainable results (per-term score breakdown)
  - Escaping by design - snippets are data, the template escapes
  - Test invariants (breakdown sums to score; results are sorted)
features:
  - Indexes every Markdown page of this repository (guides + 20 project write-ups)
  - Queries - all words (AND), "exact phrases", -excluded words
  - BM25 (default) or TF-IDF ranking, with a 'why this score?' breakdown
  - Snippets that show the best-matching passage with highlights
architecture: |
  classDiagram
    class Document {
      <<frozen>>
      +id int
      +title str
      +text str
      +source str
    }
    class InvertedIndex {
      +documents dict
      +postings dict~term, dict~doc, positions~~
      +lengths dict
      +add(doc)
      +document_frequency(term) int
      +term_frequency(term, doc) int
      +has_phrase(doc, terms) bool
    }
    class Ranker {
      <<abstract>>
      +term_score(index, term, doc)* float
      +score(index, terms, doc) tuple
    }
    class BM25Ranker {
      +k1 float
      +b float
    }
    class TfIdfRanker
    class Query {
      +terms list
      +phrases list
      +excluded list
      +parse(text)$ Query
    }
    class SearchEngine {
      +index InvertedIndex
      +ranker Ranker
      +search(text, limit) list~Hit~
    }
    Ranker <|-- BM25Ranker
    Ranker <|-- TfIdfRanker
    SearchEngine --> InvertedIndex
    SearchEngine --> Ranker
    InvertedIndex o-- Document
    SearchEngine ..> Query
flow: |
  flowchart LR
    Q["query: #quot;unit test#quot; -pasta"] --> P[Query.parse]
    P --> T[terms: unit, test]
    T --> I["postings[unit] ∩ postings[test]"]
    I --> PH[keep docs with the phrase]
    PH --> EX["− postings[pasta]"]
    EX --> R["rank: BM25 per term, summed"]
    R --> S[snippets + highlights]
steps:
  - title: One text pipeline
    files: [text.py]
    body: |
      Lowercase → split into words → drop stop words → stem. **Indexing and querying must use the same pipeline**, or "Testing"
      in a query won't find "tests" in a document. The stemmer is a small table of suffix rules, a simplified Porter stemmer.
  - title: Build the inverted index
    files: [index.py]
    body: |
      `postings["test"] = {1: [0, 7], 3: [3, 9]}` maps each term to the documents containing it and the **positions**.
      Finding every document with a word is one dict lookup, not a scan through every file. That's why search engines are fast.
  - title: Boolean queries with sets
    files: [search.py]
    body: |
      All words must match, so intersect the document sets. Exclusions: subtract. Phrases: check that positions are
      consecutive (`has_phrase`). `Query.parse` turns `python "unit test" -java` into those three lists.
  - title: Rank with interchangeable strategies
    files: [ranking.py]
    body: |
      `Ranker` is abstract with one method, `term_score`. `score` (inherited) sums it over the query terms and keeps the
      breakdown. `TfIdfRanker` and `BM25Ranker` are drop-in replacements, chosen from a dropdown in the UI.
  - title: Understand BM25
    files: [ranking.py]
    body: |
      Like TF-IDF, rare words matter more (**idf**) and repeated words matter more (**tf**), but BM25 **saturates**: the 10th
      occurrence adds little (k1), and long documents are normalised by length (b). It's the default ranking in Lucene and Elasticsearch.
  - title: Snippets that are safe to display
    files: [search.py, templates/search_engine/index.html]
    body: |
      `make_snippet` slides a window over the document to find the passage with the most query words, then returns
      `(text, highlighted)` segments. The template wraps highlighted ones in `<mark>`, with Jinja escaping everything, so
      no HTML from documents is ever injected.
  - title: Test the invariants
    files: [tests/test_search.py]
    body: |
      Beyond examples, test **properties**: results are sorted by score, every score's breakdown sums to the score, and
      phrase order matters ("test unit" ≠ "unit test").
exercises:
  - Add **prefix search** (`clas*`) using a sorted list of terms and `bisect`.
  - Add **typo tolerance** - suggest the closest indexed term by edit distance when a word has no results.
  - Save the index to disk (JSON or `pickle`) and only re-index files whose modification time changed.
  - Add a **field boost** - matches in titles count 3×. Compare rankings before and after.
---

## Inverted index in one picture

```mermaid
flowchart LR
  subgraph Documents
    D1["1: Unit testing in Python"]
    D3["3: Test driven development"]
    D4["4: Cooking pasta"]
  end
  subgraph Index["Inverted index"]
    T1["test → {1: [1, 7], 3: [1, 9], 4: [12]}"]
    T2["unit → {1: [0, 6], 3: [10]}"]
    T3["pasta → {4: [1, 9]}"]
  end
  D1 & D3 & D4 --> Index
```

A book's index works the same way: look up a word, get the pages. Building it is slow once; every search after that is fast.
