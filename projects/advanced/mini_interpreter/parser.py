"""Stage 2 - a recursive-descent parser. Each grammar rule is one method; precedence comes from which rule calls which.

    statement := "def" NAME "(" [NAME ("," NAME)*] ")" "=" expr
               | NAME "=" expr
               | expr
    expr      := term (("+" | "-") term)*            lowest precedence, left-associative
    term      := unary (("*" | "/" | "%") unary)*
    unary     := "-" unary | power
    power     := call ["^" unary]                    right-associative: 2^3^2 = 2^(3^2)
    call      := primary ["(" [expr ("," expr)*] ")"]
    primary   := NUMBER | NAME | "(" expr ")"
"""

from __future__ import annotations

from .lexer import LangError, T, Token, tokenize
from .nodes import Assign, Binary, Call, FunctionDef, Name, Node, Number, Unary


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # --- helpers
    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def advance(self) -> Token:
        token = self.current
        self.pos += 1
        return token

    def expect(self, kind: T, what: str) -> Token:
        if self.current.type is not kind:
            found = repr(self.current.text) if self.current.text else "end of input"
            raise LangError(f"Expected {what} but found {found}", self.current.column)
        return self.advance()

    # --- grammar rules
    def statement(self) -> Node:
        if self.current.type is T.DEF:
            self.advance()
            name = self.expect(T.NAME, "a function name").text
            self.expect(T.LPAREN, "'('")
            params = []
            if self.current.type is not T.RPAREN:
                params.append(self.expect(T.NAME, "a parameter name").text)
                while self.current.type is T.COMMA:
                    self.advance()
                    params.append(self.expect(T.NAME, "a parameter name").text)
            self.expect(T.RPAREN, "')'")
            self.expect(T.EQUALS, "'='")
            node = FunctionDef(name, tuple(params), self.expr())
        elif self.current.type is T.NAME and self.peek().type is T.EQUALS:
            name = self.advance().text
            self.advance()
            node = Assign(name, self.expr())
        else:
            node = self.expr()
        self.expect(T.EOF, "end of input")
        return node

    def expr(self) -> Node:
        node = self.term()
        while self.current.type in (T.PLUS, T.MINUS):
            op = self.advance()
            node = Binary(op.text, node, self.term(), op.column)
        return node

    def term(self) -> Node:
        node = self.unary()
        while self.current.type in (T.STAR, T.SLASH, T.PERCENT):
            op = self.advance()
            node = Binary(op.text, node, self.unary(), op.column)
        return node

    def unary(self) -> Node:
        if self.current.type is T.MINUS:
            self.advance()
            return Unary("-", self.unary())
        return self.power()

    def power(self) -> Node:
        base = self.call()
        if self.current.type is T.CARET:
            op = self.advance()
            return Binary("^", base, self.unary(), op.column)    # recursion on the right = right-associative
        return base

    def call(self) -> Node:
        node = self.primary()
        if self.current.type is T.LPAREN and isinstance(node, Name):
            self.advance()
            args = []
            if self.current.type is not T.RPAREN:
                args.append(self.expr())
                while self.current.type is T.COMMA:
                    self.advance()
                    args.append(self.expr())
            self.expect(T.RPAREN, "')'")
            return Call(node.id, tuple(args), node.column)
        return node

    def primary(self) -> Node:
        token = self.current
        if token.type is T.NUMBER:
            self.advance()
            return Number(float(token.text))
        if token.type is T.NAME:
            self.advance()
            return Name(token.text, token.column)
        if token.type is T.LPAREN:
            self.advance()
            node = self.expr()
            self.expect(T.RPAREN, "')'")
            return node
        found = repr(token.text) if token.text else "end of input"
        raise LangError(f"Expected a number, a name or '(' but found {found}", token.column)


def parse(source: str) -> Node:
    if not source.strip():
        raise LangError("Type an expression.", 0)
    return Parser(tokenize(source)).statement()
