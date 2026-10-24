"""Computer opponents. Each strategy is a class with the same method, choose(history),
so the game can use any of them without knowing which one it has. That's polymorphism.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import Counter

from .rules import Ruleset


class Strategy(ABC):
    name: str = "strategy"
    description: str = ""

    def __init__(self, rules: Ruleset, rng: random.Random | None = None):
        self.rules = rules
        self.rng = rng or random.Random()

    @abstractmethod
    def choose(self, history: list[tuple[str, str]]) -> str:
        """history = [(human_move, computer_move), ...] of earlier rounds."""


class RandomStrategy(Strategy):
    name = "random"
    description = "Picks uniformly at random - impossible to exploit, impossible to beat on average."

    def choose(self, history):
        return self.rng.choice(self.rules.moves)


class CycleStrategy(Strategy):
    name = "cycle"
    description = "Plays the moves in a fixed order. Spot the pattern and you'll win every round."

    def choose(self, history):
        return self.rules.moves[len(history) % len(self.rules.moves)]


class FrequencyStrategy(Strategy):
    name = "frequency"
    description = "Counts your moves and counters your favourite. Humans have favourites!"

    def choose(self, history):
        if not history:
            return self.rng.choice(self.rules.moves)
        favourite, _ = Counter(human for human, _ in history).most_common(1)[0]
        return self.rules.counter(favourite)


class MarkovStrategy(Strategy):
    name = "markov"
    description = "Learns what you tend to play *after* each move, then counters the prediction."

    def choose(self, history):
        if len(history) < 2:
            return self.rng.choice(self.rules.moves)
        last = history[-1][0]
        followers = Counter(nxt for (prev, _), (nxt, _) in zip(history, history[1:]) if prev == last)
        if not followers:
            return self.rng.choice(self.rules.moves)
        predicted, _ = followers.most_common(1)[0]
        return self.rules.counter(predicted)


STRATEGIES: dict[str, type[Strategy]] = {cls.name: cls for cls in (RandomStrategy, CycleStrategy, FrequencyStrategy, MarkovStrategy)}


def make_strategy(name: str, rules: Ruleset, rng: random.Random | None = None) -> Strategy:
    """A tiny factory: turn a name from a form or command line into a strategy object."""
    try:
        return STRATEGIES[name](rules, rng)
    except KeyError:
        raise ValueError(f"Unknown opponent {name!r}. Choose from: {', '.join(STRATEGIES)}.") from None
