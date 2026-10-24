---
title: Mini Interpreter
order: 1
icon: 🧮
time: 6-8 hours
summary: Build a small programming language - numbers, operators with correct precedence, variables, built-in and user-defined (even recursive) functions - with a lexer, a recursive-descent parser, an AST and a tree-walking interpreter.
python_skills:
  - Regex with named groups and finditer
  - Structural pattern matching (match / case) on dataclasses
  - Recursion, and limiting it safely
  - Type unions (Node = Number | Name | …)
  - The math module
oop_concepts:
  - Frozen dataclasses as AST nodes
  - A parser class with one method per grammar rule
  - The interpreter as an object holding environment state
  - An exception with extra data (error column)
clean_code:
  - Split a hard problem into stages (lex → parse → evaluate)
  - Write the grammar down first; let the code mirror it
  - Error messages that point at the exact column
  - Precedence tests that assert the *shape* of the tree
features:
  - "+ - * / % ^, unary minus, parentheses - with correct precedence and associativity"
  - Variables (r = 5) and constants (pi, e, tau)
  - 14 built-ins (sqrt, sin, log, max, hypot…)
  - User functions, including recursion - def hyp(a, b) = sqrt(a^2 + b^2)
  - Web notebook that shows tokens, the syntax tree (ASCII + diagram) and the result
architecture: |
  classDiagram
    class Lexer {
      <<module>>
      +tokenize(source) list~Token~
    }
    class Token {
      +type T
      +text str
      +column int
    }
    class Parser {
      -tokens list
      -pos int
      +statement() Node
      +expr() Node
      +term() Node
      +unary() Node
      +power() Node
      +call() Node
      +primary() Node
    }
    class Node {
      <<union>>
      Number | Name | Unary | Binary
      Call | Assign | FunctionDef
    }
    class Interpreter {
      +variables dict
      +functions dict
      +run(source) tuple
      +evaluate(node, local) float
    }
    class LangError {
      +column int
    }
    Lexer ..> Token
    Parser ..> Node : builds
    Interpreter ..> Parser : parse()
    Interpreter ..> Node : walks
flow: |
  flowchart LR
    S["'2 * (x + 1)'"] -->|tokenize| TK["NUMBER STAR LPAREN NAME PLUS NUMBER RPAREN"]
    TK -->|parse: expr → term → unary → power → call → primary| AST["Binary * ( Number 2, Binary + (Name x, Number 1) )"]
    AST -->|evaluate: match/case, bottom-up| R["8 (if x = 3)"]
steps:
  - title: Write the grammar first
    files: [parser.py]
    body: |
      The docstring at the top of `parser.py` *is* the design. Each rule refers to the next-tighter one: `expr` handles
      `+ -`, which are made of `term`s (`* / %`), which are made of `unary`s… **Lower in the chain = binds tighter.**
  - title: The lexer - one regex to rule them all
    files: [lexer.py]
    body: |
      Each token type is a named group in one big regex; `finditer` walks the input and `match.lastgroup` says which group
      matched. Whitespace is skipped, and anything unexpected becomes a `LangError` with its **column**.
  - title: AST nodes as dataclasses
    files: [nodes.py]
    body: |
      Each node type is a tiny frozen dataclass. `to_source` turns a tree back into fully parenthesised text, which is the
      perfect way to *test* precedence: `parse("1 + 2 * 3")` must give `(1 + (2 * 3))`.
  - title: The recursive-descent parser
    files: [parser.py]
    body: |
      `expr` loops `while current is + or -`, building `Binary` nodes **left-associatively**. `power` recurses on its right
      side, so `2^3^2` = `2^(3^2)` (**right-associative**), like in maths. `expect(kind, what)` produces errors such as
      "Expected ')' but found end of input".
  - title: Evaluate with match/case
    files: [interpreter.py]
    body: |
      `match node:` with `case Binary(op, left, right, column):` destructures the dataclass, which is Python 3.10's
      structural pattern matching. Each case is a line or two. Names are looked up in local → global → constants scopes.
  - title: Functions and scopes
    files: [interpreter.py]
    body: |
      A user function stores its parameters and body tree. Calling it evaluates the body with a **fresh local scope**
      mapping parameters to argument values, so `r` inside `area(r)` doesn't touch the global `r`. A depth counter stops
      infinite recursion with a friendly error.
  - title: Test like a language designer
    files: [tests/test_interpreter.py]
    body: |
      Parametrised tables cover precedence shapes, values and **ten different error messages**. Errors are features: a
      good language tells you exactly what went wrong and where.
  - title: A REPL and a notebook UI
    files: [cli.py, web.py, templates/mini_interpreter/index.html]
    body: |
      The CLI is a classic read-eval-print loop with `:tree on`. The web UI keeps only the *source lines* in the session
      and rebuilds the interpreter by re-running them, so the state is reproducible. It shows tokens, an ASCII tree, a Mermaid
      diagram of the AST and the result.
exercises:
  - Add **comparison and conditionals** - `if(x > 0, x, -x)`. You'll need new tokens, a new grammar level and lazy evaluation of the branches.
  - Add **implicit multiplication** - `2pi`, `3(x + 1)`. Where in the grammar does it fit?
  - Write a **constant folder** that simplifies `2 * 3 + x` to `6 + x` before evaluation (a tree → tree function).
  - Compile the AST to **Python bytecode** with the `ast` module and compare speed with the tree walker.
---

## Three stages, one idea each

| Stage | Input → output | Key idea |
|---|---|---|
| Lexer | text → tokens | regular expressions, longest match |
| Parser | tokens → tree | grammar rules as methods, precedence by nesting |
| Interpreter | tree → value | recursion over the tree, scopes for variables |

Python itself works the same way. Try `python -c "import ast; print(ast.dump(ast.parse('1 + 2 * 3'), indent=2))"`.
