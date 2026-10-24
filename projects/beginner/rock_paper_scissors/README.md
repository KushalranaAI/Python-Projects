---
title: Rock Paper Scissors
order: 7
icon: ✌️
time: 2-3 hours
summary: The classic game, plus Lizard-Spock rules and four computer opponents, two of which learn your habits. Your first taste of polymorphism with abstract base classes.
python_skills:
  - collections.Counter and most_common
  - zip over a list and its shifted copy (pairs of rounds)
  - Nested dictionaries as rule tables
  - Class attributes vs instance attributes
oop_concepts:
  - Abstract base class (ABC) with an @abstractmethod
  - Polymorphism - four strategies, one interface
  - The Strategy pattern
  - A factory function that maps names to classes
clean_code:
  - Rules as data (adding a move = editing a dict)
  - The computer chooses before it sees your move (no accidental cheating)
  - Behaviour you can test - deterministic opponents
  - Docstrings that explain *why*
features:
  - Classic and Rock-Paper-Scissors-Lizard-Spock rules
  - Opponents - random, cycle, frequency (counters your favourite), markov (learns sequences)
  - Score, win rate and round history
  - Explanations like "Spock vaporizes rock."
architecture: |
  classDiagram
    class Ruleset {
      <<frozen dataclass>>
      +name str
      +beats dict
      +moves list
      +judge(mine, theirs) Outcome
      +explain(mine, theirs) str
      +counter(move) str
    }
    class Strategy {
      <<abstract>>
      +rules Ruleset
      +rng Random
      +choose(history)* str
    }
    class RandomStrategy
    class CycleStrategy
    class FrequencyStrategy
    class MarkovStrategy
    class Match {
      +opponent Strategy
      +history list
      +play(move) Round
      +score dict
      +win_rate float
    }
    Strategy <|-- RandomStrategy
    Strategy <|-- CycleStrategy
    Strategy <|-- FrequencyStrategy
    Strategy <|-- MarkovStrategy
    Match --> Strategy : plays against
    Strategy --> Ruleset
flow: |
  sequenceDiagram
    participant H as You
    participant M as Match
    participant S as Strategy (any subclass)
    participant R as Ruleset
    H->>M: play("rock")
    M->>S: choose(history)
    S-->>M: "paper"
    M->>R: judge("rock", "paper")
    R-->>M: Outcome.LOSE
    M-->>H: Round(... "Paper covers rock.")
steps:
  - title: Encode the rules as a table
    files: [rules.py]
    body: |
      `beats = {"rock": {"scissors": "crushes"}, ...}` holds *who beats whom* and *the verb*. `judge`, `explain` and
      `counter` are each a couple of lines that read the table. Lizard-Spock is just a bigger table, with no new code.
  - title: Define what every opponent must do
    files: [players.py]
    body: |
      `Strategy` is an **abstract base class**: it declares `choose(history)` with `@abstractmethod` but doesn't
      implement it. Python refuses to create a `Strategy()` directly (there's a test for that) and forces every subclass
      to implement `choose`.
  - title: Write four strategies
    files: [players.py]
    body: |
      Each subclass overrides `choose` in its own way: random, cycling, countering your most frequent move, or a
      tiny **Markov model** that learns "after rock, they usually play paper". The game code never checks which one it
      has, and that's **polymorphism**.
  - title: A factory for user choices
    files: [players.py]
    body: |
      `STRATEGIES = {cls.name: cls for cls in (...)}` maps names to classes, and `make_strategy("markov", rules)` builds one.
      Forms and the CLI pass strings; the factory turns them into objects and raises a friendly error for unknown names.
  - title: The match and its score
    files: [game.py]
    body: |
      `Match.play` asks the opponent **first** and only then records your move, so the computer can't peek. Score and
      win rate are properties computed from `history`.
  - title: Prove the learning opponents learn
    files: [tests/test_rps.py]
    body: |
      With a seeded RNG the tests are deterministic: always playing rock loses to *frequency* after round 1, and alternating
      rock/paper loses to *markov*. The test documents the behaviour better than a comment would.
  - title: Interfaces
    files: [cli.py, web.py, templates/rock_paper_scissors/index.html]
    body: |
      The web session stores just the rules name, the opponent name and the history (plain strings), and rebuilds the
      `Match` each request. Notice how `load_match` and `save` keep the routes tiny.
exercises:
  - Add a `MetaStrategy` that runs all other strategies and plays whichever has won most so far.
  - Add **best of N** matches with a `MatchResult` and a winner announcement.
  - Make the Markov strategy look at the last **two** moves. Does it beat you faster?
  - Add a third rule set of your own invention. Write a test that every move wins and loses equally often.
---

## Can a computer read your mind?

Humans are bad at being random. We avoid repeating ourselves, we have favourites, we follow patterns. The *frequency*
and *markov* opponents exploit exactly that, and in practice they beat most people over 30+ rounds. The *random* opponent
can't be beaten on average, but it can't exploit you either: against it every strategy wins a third of the time.
