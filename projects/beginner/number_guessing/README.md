---
title: Number Guessing Game
order: 1
icon: 🎯
time: 1-2 hours
summary: The computer picks a secret number and you find it with hints. Your first project that separates the game's rules from its input and output.
python_skills:
  - Variables, conditionals and while loops
  - Functions with type hints
  - The random module (and how to make it testable)
  - Enums for fixed sets of options
  - The walrus operator for input loops
oop_concepts:
  - A dataclass for the game's state
  - Properties for values derived from state
  - Alternative constructors with @classmethod
  - A custom exception class
clean_code:
  - No input()/print() inside the game logic
  - One source of truth (attempts are derived from the guess list)
  - Inject randomness so tests are deterministic
  - Validate input at the boundary, raise clear errors
features:
  - Three difficulty levels
  - Too high / too low feedback, plus the remaining possible range
  - A binary-search bound showing the optimal number of guesses
  - Terminal version and web version sharing the same game class
architecture: |
  classDiagram
    class Difficulty {
      <<enum>>
      EASY
      MEDIUM
      HARD
      +high int
      +attempts int
    }
    class Feedback {
      <<enum>>
      TOO_LOW
      TOO_HIGH
      CORRECT
    }
    class GuessingGame {
      +high int
      +max_attempts int
      +secret int
      +guesses list~int~
      +new(difficulty, rng)$ GuessingGame
      +guess(number) Feedback
      +attempts_left int
      +is_won bool
      +is_over bool
      +range_hint tuple
      +to_dict() dict
      +from_dict(data)$ GuessingGame
    }
    class GameOverError
    GuessingGame ..> Difficulty : created from
    GuessingGame ..> Feedback : returns
    GuessingGame ..> GameOverError : raises
flow: |
  sequenceDiagram
    participant U as You
    participant W as web.py (route)
    participant S as Session
    participant G as GuessingGame
    U->>W: POST /guess number=37
    W->>S: load dict
    S-->>W: {"secret": 42, "guesses": [...]}
    W->>G: GuessingGame.from_dict(...)
    W->>G: guess(37)
    G-->>W: Feedback.TOO_LOW
    W->>S: save game.to_dict()
    W-->>U: redirect → page shows "Too low"
steps:
  - title: Write down the rules before any code
    body: |
      A good project starts on paper. List the **nouns** (game, secret, guess, difficulty, attempt) and the
      **rules** (a guess is too low, too high or correct; the game ends when you win or run out of attempts; guesses
      must be in range). Nouns become classes and attributes; rules become methods.
  - title: Model the fixed options with Enums
    files: [game.py]
    body: |
      Difficulty levels and feedback are *closed sets*. An `Enum` is much clearer than magic strings like `"easy"`,
      which typos break silently.
      ```python
      class Difficulty(Enum):
          EASY = (50, 10)      # (highest number, attempts)

          @property
          def high(self) -> int:
              return self.value[0]
      ```
  - title: Create the game class with a dataclass
    files: [game.py]
    body: |
      `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you. Store only the essential state: the bounds,
      the secret and the list of guesses. Everything else (attempts left, won or not) is a **property computed from
      that list**, so the values can never disagree with each other.
      ```python
      @property
      def attempts_left(self) -> int:
          return self.max_attempts - len(self.guesses)
      ```
  - title: Make randomness injectable
    files: [game.py, tests/test_game.py]
    body: |
      `GuessingGame.new(difficulty, rng=None)` is an *alternative constructor* (`@classmethod`). It accepts an optional
      `random.Random`, so tests can pass `random.Random(7)` and always get the same secret. Hidden randomness is
      the classic reason code is "impossible to test".
  - title: Implement guess() and its error cases
    files: [game.py]
    body: |
      Guard clauses first: raise `GameOverError` when the game has ended, and `ValueError` when the number is out of
      range. Then record the guess and return a `Feedback`. The method never prints: it *returns* information
      and lets the caller decide how to show it.
  - title: Test the rules with pytest
    files: [tests/test_game.py]
    body: |
      Because the game is pure logic, tests are a few lines each: build a game with a known secret, call `guess`,
      and assert on the result. `pytest.raises` checks the error cases, and `parametrize` runs one test over many inputs.
      Run them with `python -m pytest projects/beginner/number_guessing/tests`.
  - title: Add a thin terminal interface
    files: [cli.py, __main__.py]
    body: |
      `cli.py` handles only conversation: asking, re-asking on bad input, printing feedback. Notice that
      `ask_number` loops until the input is a whole number, while the *range* check stays in the game,
      where the rule belongs. `__main__.py` makes `python -m projects.beginner.number_guessing` work.
  - title: Add a Flask UI with the same class
    files: [web.py, templates/number_guessing/index.html]
    body: |
      HTTP is stateless, so between requests the game lives in the session as a plain dict (`to_dict` /
      `from_dict`). Each route follows the same pattern: **load → call one domain method → save → redirect**.
      Redirecting after a POST stops the browser from re-submitting a guess when you refresh.
exercises:
  - Add a **"computer guesses"** mode where *you* pick the number and the program finds it with binary search. Reuse `Feedback`.
  - Keep a **high-score table** (fewest guesses per difficulty) in a JSON file. Put the file handling in its own class.
  - Add a `CUSTOM` difficulty where the player chooses the range. Which code has to change, and which doesn't?
  - 'Flask''s session cookie is **signed, not encrypted**: open your browser''s dev tools, base64-decode the cookie, and you''ll see the secret! Fix it by keeping games in a server-side `dict[str, GuessingGame]` and storing only a random game id in the session.'
  - Show **"warmer / colder"** hints by comparing the distance of the last two guesses. Write the tests first.
---

## What you'll learn

This is the smallest project in the course, but it already has the structure of all the others:

| File | Responsibility | Knows about |
|---|---|---|
| `game.py` | the rules | numbers and guesses only |
| `cli.py` | terminal conversation | `input()`, `print()`, the game |
| `web.py` + template | browser conversation | Flask, the session, the game |
| `tests/` | proof that the rules work | the game |

Try deleting `cli.py` and `web.py`: the tests still pass. That's the sign of a well-separated design.

## Why binary search is optimal

If the secret is in a range of size *n*, a guess in the middle halves the range whatever the answer.
After *k* guesses at most n / 2^k candidates remain, so ⌈log₂(n+1)⌉ guesses always suffice:
7 for 1-100 and 9 for 1-500. That's why "Hard" gives you exactly 9 attempts. The progress bar in the app shows the
remaining range shrinking with each guess.
