import math

import pytest

from projects.advanced.mini_interpreter.interpreter import Interpreter, format_result
from projects.advanced.mini_interpreter.lexer import LangError, T, tokenize
from projects.advanced.mini_interpreter.nodes import Binary, Number, to_source, tree_lines
from projects.advanced.mini_interpreter.parser import parse


def test_tokenizer():
    assert [t.type for t in tokenize("x = 2.5e3 * (y + 1)")] == [T.NAME, T.EQUALS, T.NUMBER, T.STAR, T.LPAREN, T.NAME, T.PLUS, T.NUMBER, T.RPAREN, T.EOF]
    assert tokenize("def f")[0].type is T.DEF


def test_tokenizer_reports_column():
    with pytest.raises(LangError) as info:
        tokenize("1 + $")
    assert info.value.column == 4


@pytest.mark.parametrize("source, shape", [
    ("1 + 2 * 3", "(1 + (2 * 3))"), ("(1 + 2) * 3", "((1 + 2) * 3)"), ("10 - 4 - 3", "((10 - 4) - 3)"),
    ("2 ^ 3 ^ 2", "(2 ^ (3 ^ 2))"), ("-2 ^ 2", "(-(2 ^ 2))"), ("f(1, 2 + x)", "f(1, (2 + x))"),
])
def test_precedence_and_associativity(source, shape):
    assert to_source(parse(source)) == shape


@pytest.mark.parametrize("source, value", [
    ("1 + 2 * 3", 7), ("(1 + 2) * 3", 9), ("2 ^ 3 ^ 2", 512), ("-2 ^ 2", -4), ("7 % 4", 3), ("10 / 4", 2.5),
    ("sqrt(16) + abs(-3)", 7), ("max(1, 9, 3)", 9), ("round(2.6)", 3), ("pi", math.pi), ("hypot(3, 4)", 5),
])
def test_evaluation(source, value):
    assert Interpreter().run(source)[1] == pytest.approx(value)


def test_variables_and_functions():
    i = Interpreter()
    i.run("r = 2")
    i.run("def area(r) = pi * r^2")
    i.run("def double(x) = 2 * x")
    assert i.run("area(3)")[1] == pytest.approx(math.pi * 9)            # the parameter shadows the global r
    assert i.run("double(area(r))")[1] == pytest.approx(8 * math.pi)


def test_recursion_is_bounded():
    i = Interpreter()
    i.run("def loop(n) = loop(n + 1)")
    with pytest.raises(LangError, match="recursion"):
        i.run("loop(1)")


@pytest.mark.parametrize("source, message", [
    ("1 / 0", "Division by zero"), ("y + 1", "Unknown name"), ("nope(1)", "Unknown function"), ("sqrt(1, 2)", "takes 1"),
    ("2 +* 3", "Expected a number"), ("(1 + 2", r"Expected '\)'"), ("pi = 3", "built in"), ("sqrt(-1)", "sqrt()"), ("", "Type"),
    ("def f(a, a) = a", "different"), ("(-8) ^ (1/3)", "real number"), ("10 ^ 400", "too large"),
])
def test_errors(source, message):
    with pytest.raises(LangError, match=message):
        Interpreter().run(source)


def test_tree_rendering():
    tree = parse("1 + 2")
    assert tree == Binary("+", Number(1), Number(2), 2)
    assert tree_lines(tree) == ["Binary +", "├── Number 1", "└── Number 2"]
    assert tree_lines(parse("-(1 + 2)")) == ["Unary -", "└── Binary +", "    ├── Number 1", "    └── Number 2"]


def test_format_result():
    assert format_result(0.1 + 0.2) == "0.3" and format_result(2.0) == "2"
