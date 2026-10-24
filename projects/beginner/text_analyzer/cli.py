"""Terminal interface: analyse a file, or paste text and finish with an empty line."""

from __future__ import annotations

import sys
from pathlib import Path

from .analyzer import analyze


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        text = Path(argv[0]).read_text(encoding="utf-8")
    else:
        print("📊 Paste text, then press Enter on an empty line:")
        lines = []
        while line := input():
            lines.append(line)
        text = "\n".join(lines)
    r = analyze(text)
    print(f"""
Words {r.words:,} (unique {r.unique_words:,}) · sentences {r.sentences} · paragraphs {r.paragraphs}
Characters {r.characters:,} ({r.characters_no_spaces:,} without spaces) · avg word {r.avg_word_length:.1f} letters
Reading time {r.reading_time} · speaking time {r.speaking_time}
Flesch reading ease {r.reading_ease} - {r.reading_ease_label}
Top words: {', '.join(f'{w} ({n})' for w, n in r.top_words)}""")


if __name__ == "__main__":
    main()
