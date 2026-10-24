"""The game's rules, with no input() or print(): this module only knows about numbers and guesses."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class Difficulty(Enum):
    """Each level is (highest number, number of attempts)."""

    EASY = (50, 10)
    MEDIUM = (100, 7)
    HARD = (500, 9)

    @property
    def high(self) -> int:
        return self.value[0]

    @property
    def attempts(self) -> int:
        return self.value[1]


class Feedback(Enum):
    TOO_LOW = "Too low"
    TOO_HIGH = "Too high"
    CORRECT = "Correct!"


class GameOverError(Exception):
    """Raised when someone guesses after the game has finished."""


@dataclass
class GuessingGame:
    """One round: a secret number between 1 and `high`, and a limited number of attempts."""

    high: int
    max_attempts: int
    secret: int
    guesses: list[int] = field(default_factory=list)

    @classmethod
    def new(cls, difficulty: Difficulty, rng: random.Random | None = None) -> GuessingGame:
        """Start a game with a random secret. Pass your own `rng` to make the secret predictable in tests."""
        rng = rng or random.Random()
        return cls(high=difficulty.high, max_attempts=difficulty.attempts, secret=rng.randint(1, difficulty.high))

    # --- state, derived from the list of guesses rather than stored separately (one source of truth)
    @property
    def attempts_used(self) -> int:
        return len(self.guesses)

    @property
    def attempts_left(self) -> int:
        return self.max_attempts - self.attempts_used

    @property
    def is_won(self) -> bool:
        return bool(self.guesses) and self.guesses[-1] == self.secret

    @property
    def is_over(self) -> bool:
        return self.is_won or self.attempts_left == 0

    @property
    def range_hint(self) -> tuple[int, int]:
        """The smallest interval that can still contain the secret, given the guesses so far."""
        low, high = 1, self.high
        for g in self.guesses:
            if g < self.secret:
                low = max(low, g + 1)
            elif g > self.secret:
                high = min(high, g - 1)
        return low, high

    # --- behaviour
    def guess(self, number: int) -> Feedback:
        if self.is_over:
            raise GameOverError("The game is over - start a new one.")
        if not 1 <= number <= self.high:
            raise ValueError(f"Guess a number between 1 and {self.high}.")
        self.guesses.append(number)
        if number < self.secret:
            return Feedback.TOO_LOW
        if number > self.secret:
            return Feedback.TOO_HIGH
        return Feedback.CORRECT

    # --- serialisation, so the web UI can keep a game in the user's session between requests
    def to_dict(self) -> dict:
        return {"high": self.high, "max_attempts": self.max_attempts, "secret": self.secret, "guesses": list(self.guesses)}

    @classmethod
    def from_dict(cls, data: dict) -> GuessingGame:
        return cls(data["high"], data["max_attempts"], data["secret"], list(data["guesses"]))


def optimal_attempts(high: int) -> int:
    """With binary search you never need more than ⌈log2(high + 1)⌉ guesses."""
    return high.bit_length()
