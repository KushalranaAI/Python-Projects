"""Markdown → HTML with syntax highlighting (Pygments) and Mermaid diagrams."""

from __future__ import annotations

import html
import re
from pathlib import Path

import markdown
from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

MERMAID_BLOCK = re.compile(r"^```mermaid\n(.*?)^```", re.S | re.M)


def render_markdown(text: str) -> Markup:
    # Mermaid source must reach the browser untouched, so pull those blocks out before Markdown sees them.
    diagrams: list[str] = []

    def stash(match: re.Match) -> str:
        diagrams.append(match.group(1))
        return f"\n\nMERMAIDPLACEHOLDER{len(diagrams) - 1}\n\n"

    text = MERMAID_BLOCK.sub(stash, text)
    out = markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "tables", "toc", "sane_lists"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "highlight"}},
    )
    for i, src in enumerate(diagrams):
        out = out.replace(f"<p>MERMAIDPLACEHOLDER{i}</p>", mermaid(src))
    return Markup(out)


def mermaid(source: str) -> Markup:
    return Markup(f'<pre class="mermaid">{html.escape(source.strip())}</pre>') if source else Markup("")


def highlight_file(path: Path) -> Markup:
    try:
        lexer = get_lexer_for_filename(path.name)
    except ClassNotFound:
        lexer = get_lexer_for_filename("x.txt")
    formatter = HtmlFormatter(cssclass="highlight", linenos="table")
    return Markup(highlight(path.read_text(encoding="utf-8"), lexer, formatter))


def pygments_css() -> str:
    light = HtmlFormatter(style="friendly").get_style_defs(".highlight")
    dark = HtmlFormatter(style="github-dark").get_style_defs(".highlight")
    return f"{light}\n@media (prefers-color-scheme: dark) {{\n{dark}\n}}\n"
