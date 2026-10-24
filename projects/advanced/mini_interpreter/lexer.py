"""Stage 1 - the lexer turns text into a list of tokens:  'x = 2 * (y + 1)'  →  NAME EQUALS NUMBER STAR LPAREN …"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class LangError(Exception):
    """Any error in the user's program, with the column where it happened (for a caret ^ under the input)."""

    def __init__(self, message: str, column: int | None = None):
        super().__init__(message)
        self.column = column


class T(Enum):
    NUMBER = auto()
    NAME = auto()
    DEF = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EQUALS = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: T
    text: str
    column: int


# One regex per token type, tried in order. Named groups tell us which one matched.
TOKEN_SPEC = [
    ("NUMBER", r"\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+"),
    ("NAME", r"[A-Za-z_]\w*"),
    ("PLUS", r"\+"), ("MINUS", r"-"), ("STAR", r"\*"), ("SLASH", r"/"), ("PERCENT", r"%"), ("CARET", r"\^"),
    ("LPAREN", r"\("), ("RPAREN", r"\)"), ("COMMA", r","), ("EQUALS", r"="),
    ("SPACE", r"\s+"),
    ("ERROR", r"."),
]
MASTER = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))
KEYWORDS = {"def": T.DEF}


def tokenize(source: str) -> list[Token]:
    tokens = []
    for match in MASTER.finditer(source):
        kind, text, column = match.lastgroup, match.group(), match.start()
        if kind == "SPACE":
            continue
        if kind == "ERROR":
            raise LangError(f"Unexpected character {text!r}", column)
        token_type = KEYWORDS.get(text, T.NAME) if kind == "NAME" else T[kind]
        tokens.append(Token(token_type, text, column))
    tokens.append(Token(T.EOF, "", len(source)))
    return tokens
