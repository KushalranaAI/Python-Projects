---
title: Hangman
order: 10
icon: 🪢
time: 2 hours
summary: Guess the word letter by letter before the drawing is complete. A compact lesson in modelling game state with sets and deriving everything else from it.
python_skills:
  - Set operations - difference, subset, union
  - String methods and the string module
  - Multi-line strings for ASCII art
  - Generating SVG in a template
oop_concepts:
  - Minimal state (word + guessed letters), with everything else derived
  - Alternative constructor (HangmanGame.random)
  - Enum results instead of booleans or strings
  - Serialisation methods (to_dict / from_dict)
clean_code:
  - Return a result, let the interface choose the message
  - Validate inputs with clear errors
  - Data (word lists, art) in separate modules
  - Tests for edge cases (spaces, repeats, invalid input)
features:
  - Three categories (Python terms, animals, countries) or random
  - On-screen keyboard and an SVG drawing that grows with each miss
  - Guess the whole word for a quick win (a wrong word costs a life)
  - Terminal version with ASCII art
architecture: |
  classDiagram
    class HangmanGame {
      +word str
      +category str
      +guessed set~str~
      +wrong_words int
      +max_misses int
      +random(category, rng)$ HangmanGame
      +guess(letter) GuessResult
      +guess_word(attempt) bool
      +letters set
      +misses list
      +mistakes int
      +lives_left int
      +masked str
      +is_won bool
      +is_lost bool
    }
    class GuessResult {
      <<enum>>
      HIT
      MISS
      REPEAT
    }
    HangmanGame ..> GuessResult
    HangmanGame ..> CATEGORIES : picks from
flow: |
  flowchart LR
    G["guessed = {a, s, x}"] --> L["letters(word) = {c, l, a, s}"]
    L --> MASK["masked: _ _ a s s"]
    G --> MISS["misses = guessed − letters = {x}"]
    MISS --> LIVES["lives = 6 − |misses| − wrong words"]
    G --> WIN{"letters ⊆ guessed?"}
steps:
  - title: Find the smallest state
    files: [game.py]
    body: |
      What do you *need* to remember? The word and the set of letters guessed. Masked word, misses, lives, won or lost:
      all of these can be **computed**, so they're properties. Less stored state means fewer bugs.
  - title: Let sets do the work
    files: [game.py]
    body: |
      `misses = guessed - letters` (set difference), `is_won = letters <= guessed` (subset). Set operations read
      almost like the rules of the game.
  - title: Return results, don't print
    files: [game.py]
    body: |
      `guess()` returns `GuessResult.HIT / MISS / REPEAT`. The CLI turns that into "✅ Yes!", the web UI into a flash
      message. Invalid input raises `ValueError`, and guessing after the end raises `GameOverError`.
  - title: Keep data out of logic
    files: [words.py, art.py]
    body: |
      Word lists and ASCII drawings are plain data in their own modules. Adding a category or redrawing the art never
      touches `game.py`.
  - title: Test the edge cases
    files: [tests/test_hangman.py]
    body: |
      Repeat guesses don't cost a life, uppercase input works, multi-word answers show their spaces, and every word in
      the lists is valid. The last test checks your *data* with your *code*.
  - title: An on-screen keyboard and an SVG drawing
    files: [web.py, templates/hangman/index.html]
    body: |
      Each letter is a submit button with `name="letter" value="e"`. Used letters are disabled. The gallows is an inline
      SVG: each body part appears when the number of misses reaches its threshold, with no images needed.
exercises:
  - Add **difficulty levels** that change `max_misses` and word length.
  - Add a **hint** button that reveals one letter but costs a life.
  - Track **statistics** (games played, win rate, streak) in a JSON file with a `Stats` class.
  - Add a **two-player mode** where one player enters the word (hidden) for the other.
---

## Why derived state matters

A common beginner version stores `lives`, `misses`, `masked_word` and `won` as separate variables, updating
all four after every guess. Forget one update and the game shows 3 lives but has already ended. Here there's
**one** thing to update (`guessed.add(letter)`), and every view of the game is always consistent.
