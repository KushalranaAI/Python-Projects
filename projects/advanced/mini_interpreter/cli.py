"""A REPL - read, evaluate, print, loop. Type :vars, :tree on/off, or :quit."""

from __future__ import annotations

from .interpreter import Interpreter, format_result
from .lexer import LangError
from .nodes import tree_lines


def main() -> None:
    interp, show_tree = Interpreter(), False
    print("🧮 Mini interpreter - try:  x = 3   ·   def sq(n) = n^2   ·   sq(x) + sqrt(16)   ·   :tree on")
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line in {":quit", ":q", "exit"}:
            break
        if line.startswith(":tree"):
            show_tree = line.endswith("on")
            continue
        if line == ":vars":
            print(interp.variables, {k: f.source for k, f in interp.functions.items()})
            continue
        if not line:
            continue
        try:
            tree, result = interp.run(line)
            if show_tree:
                print("\n".join(tree_lines(tree)))
            print(format_result(result))
        except LangError as error:
            if error.column is not None:
                print(" " * (error.column + 4) + "^")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
