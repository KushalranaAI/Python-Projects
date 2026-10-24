"""Stage 2's output - the abstract syntax tree (AST). One small immutable class per kind of expression."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Name:
    id: str
    column: int = 0


@dataclass(frozen=True)
class Unary:
    op: str
    operand: Node


@dataclass(frozen=True)
class Binary:
    op: str
    left: Node
    right: Node
    column: int = 0


@dataclass(frozen=True)
class Call:
    function: str
    args: tuple[Node, ...]
    column: int = 0


@dataclass(frozen=True)
class Assign:
    name: str
    value: Node


@dataclass(frozen=True)
class FunctionDef:
    name: str
    params: tuple[str, ...]
    body: Node


Node = Number | Name | Unary | Binary | Call | Assign | FunctionDef


def to_source(node: Node) -> str:
    """Turn a tree back into text, fully parenthesised - handy to *see* how precedence was applied."""
    match node:
        case Number(value):
            return f"{value:g}"
        case Name(id):
            return id
        case Unary(op, operand):
            return f"({op}{to_source(operand)})"
        case Binary(op, left, right):
            return f"({to_source(left)} {op} {to_source(right)})"
        case Call(function, args):
            return f"{function}({', '.join(map(to_source, args))})"
        case Assign(name, value):
            return f"{name} = {to_source(value)}"
        case FunctionDef(name, params, body):
            return f"def {name}({', '.join(params)}) = {to_source(body)}"
    raise TypeError(node)


def _label_children(node: Node) -> tuple[str, list[Node]]:
    """One description of each node type, shared by both tree renderers."""
    match node:
        case Number(value):
            return f"Number {value:g}", []
        case Name(id):
            return f"Name {id}", []
        case Unary(op, operand):
            return f"Unary {op}", [operand]
        case Binary(op, left, right):
            return f"Binary {op}", [left, right]
        case Call(function, args):
            return f"Call {function}", list(args)
        case Assign(name, value):
            return f"Assign {name}", [value]
        case FunctionDef(name, params, body):
            return f"FunctionDef {name}({', '.join(params)})", [body]
    raise TypeError(node)


def tree_lines(node: Node) -> list[str]:
    """ASCII tree, like the `tree` command:   Binary +  /  ├── Number 1  /  └── Number 2"""
    label, children = _label_children(node)
    lines = [label]
    for i, child in enumerate(children):
        last = i == len(children) - 1
        child_lines = tree_lines(child)
        lines.append(("└── " if last else "├── ") + child_lines[0])
        lines += [("    " if last else "│   ") + line for line in child_lines[1:]]
    return lines


def to_mermaid(node: Node) -> str:
    """The same tree as a Mermaid flowchart, for the web UI."""
    lines, counter = ["flowchart TD"], [0]

    def visit(n: Node) -> str:
        counter[0] += 1
        nid = f"n{counter[0]}"
        label, kids = _label_children(n)
        lines.append(f'    {nid}["{label.replace(chr(34), "")}"]')
        for kid in kids:
            lines.append(f"    {nid} --> {visit(kid)}")
        return nid

    visit(node)
    return "\n".join(lines)
