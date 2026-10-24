"""Stage 3 - walk the tree and compute. Structural pattern matching (match/case) picks the code for each node type."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .lexer import LangError
from .nodes import Assign, Binary, Call, FunctionDef, Name, Node, Number, Unary
from .parser import parse

BUILTINS = {
    "sqrt": (math.sqrt, 1), "sin": (math.sin, 1), "cos": (math.cos, 1), "tan": (math.tan, 1), "ln": (math.log, 1),
    "log": (math.log10, 1), "exp": (math.exp, 1), "abs": (abs, 1), "floor": (math.floor, 1), "ceil": (math.ceil, 1),
    "round": (round, 1), "min": (min, None), "max": (max, None), "hypot": (math.hypot, None),
}
CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}
MAX_DEPTH = 200


@dataclass
class UserFunction:
    params: tuple[str, ...]
    body: Node
    source: str


@dataclass
class Interpreter:
    variables: dict[str, float] = field(default_factory=dict)
    functions: dict[str, UserFunction] = field(default_factory=dict)

    def run(self, source: str) -> tuple[Node, float | str]:
        tree = parse(source)
        match tree:
            case Assign(name, value):
                if name in CONSTANTS or name in BUILTINS:
                    raise LangError(f"'{name}' is built in and can't be reassigned.")
                result = self.evaluate(value, {})
                self.variables[name] = result
                return tree, result
            case FunctionDef(name, params, body):
                if name in BUILTINS:
                    raise LangError(f"'{name}' is a built-in function.")
                if len(set(params)) != len(params):
                    raise LangError("Parameter names must be different.")
                self.functions[name] = UserFunction(params, body, source.strip())
                return tree, f"defined {name}({', '.join(params)})"
            case _:
                return tree, self.evaluate(tree, {})

    def evaluate(self, node: Node, local: dict[str, float], depth: int = 0) -> float:
        if depth > MAX_DEPTH:
            raise LangError("Too much recursion.")
        ev = lambda n: self.evaluate(n, local, depth)                     # noqa: E731 - tiny local shorthand
        match node:
            case Number(value):
                return value
            case Name(id, column):
                for scope in (local, self.variables, CONSTANTS):          # innermost scope first
                    if id in scope:
                        return scope[id]
                raise LangError(f"Unknown name '{id}'", column)
            case Unary("-", operand):
                return -ev(operand)
            case Binary(op, left, right, column):
                return self._binary(op, ev(left), ev(right), column)
            case Call(name, args, column):
                values = [ev(a) for a in args]
                if name in BUILTINS:
                    fn, arity = BUILTINS[name]
                    if arity is not None and len(values) != arity:
                        raise LangError(f"{name}() takes {arity} argument(s), got {len(values)}", column)
                    if not values:
                        raise LangError(f"{name}() needs arguments", column)
                    try:
                        return float(fn(*values))
                    except (ValueError, OverflowError) as error:
                        raise LangError(f"{name}(): {error}", column) from None
                if name in self.functions:
                    fn = self.functions[name]
                    if len(values) != len(fn.params):
                        raise LangError(f"{name}() takes {len(fn.params)} argument(s), got {len(values)}", column)
                    return self.evaluate(fn.body, dict(zip(fn.params, values)), depth + 1)   # a fresh local scope
                raise LangError(f"Unknown function '{name}'", column)
        raise LangError(f"Can't evaluate {type(node).__name__}")

    @staticmethod
    def _binary(op: str, a: float, b: float, column: int) -> float:
        try:
            match op:
                case "+":
                    return a + b
                case "-":
                    return a - b
                case "*":
                    return a * b
                case "/":
                    return a / b
                case "%":
                    return a % b
                case "^":
                    result = a ** b
                    if isinstance(result, complex):          # e.g. (-8) ^ (1/3) - Python returns a complex number
                        raise LangError("The result isn't a real number", column)
                    return float(result)
        except ZeroDivisionError:
            raise LangError("Division by zero", column) from None
        except OverflowError:
            raise LangError("Number too large", column) from None
        raise LangError(f"Unknown operator {op}", column)


def format_result(value: float | str) -> str:
    if isinstance(value, str):
        return value
    return f"{value:.12g}"
