"""Terminal interface:  python -m projects.advanced.search_engine "query" [--dir FOLDER] [--ranker bm25|tf-idf]"""

from __future__ import annotations

import argparse
from pathlib import Path

from projects.ui_kit import REPO_ROOT

from .index import load_folder
from .ranking import RANKERS
from .search import SearchEngine


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="search")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--dir", type=Path, default=REPO_ROOT, help="folder of .md/.txt files to index")
    parser.add_argument("--ranker", choices=list(RANKERS), default="bm25")
    args = parser.parse_args(argv)
    index = load_folder(args.dir)
    engine = SearchEngine(index, RANKERS[args.ranker])
    print(f"🔎 Indexed {len(index)} documents, {index.vocabulary_size:,} distinct terms")
    queries = [args.query] if args.query else iter(lambda: input("query> ").strip(), "")
    for q in queries:
        for hit in engine.search(q):
            snippet = "".join(f"[{t}]" if marked else t for t, marked in hit.snippet)
            print(f"\n{hit.score:6.2f}  {hit.document.title}  ({hit.document.source})\n        {snippet[:180]}")


if __name__ == "__main__":
    main()
