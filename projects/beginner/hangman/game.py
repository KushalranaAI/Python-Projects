"""Hangman rules. The whole game state is the secret word plus the set of letters guessed so far."""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from enum import Enum

from .words import CATEGORIES

MAX_MISSES = 6


class GuessResult(Enum):
    HIT = "hit"
    MISS = "miss"
    REPEAT = "repeat"


class GameOverError(Exception):
    pass


@dataclass
class HangmanGame:
    word: str
    category: str = ""
    guessed: set[str] = field(default_factory=set)
    wrong_words: int = 0                 # whole-word guesses that were wrong; each costs a life
    max_misses: int = MAX_MISSES

    def __post_init__(self):
        self.word = self.word.lower().strip()
        if not self.word or not all(c in string.ascii_lowercase or c in " -" for c in self.word):
            raise ValueError("The word may contain only letters, spaces and hyphens.")

    @classmethod
    def random(cls, category: str | None = None, rng: random.Random | None = None) -> HangmanGame:
        rng = rng or random.Random()
        category = category if category in CATEGORIES else rng.choice(list(CATEGORIES))
        return cls(rng.choice(CATEGORIES[category]), category)

    @property
    def letters(self) -> set[str]:
        return {c for c in self.word if c.isalpha()}

    @property
    def misses(self) -> list[str]:
        return sorted(self.guessed - self.letters)

    @property
    def mistakes(self) -> int:
        return len(self.misses) + self.wrong_words

    @property
    def lives_left(self) -> int:
        return self.max_misses - self.mistakes

    @property
    def masked(self) -> str:
        """'dataclass' with {a, s} guessed → '_ a _ a _ _ a s s'. Spaces and hyphens are always shown."""
        return " ".join(c if c in self.guessed or not c.isalpha() else "_" for c in self.word)

    @property
    def is_won(self) -> bool:
        return self.letters <= self.guessed

    @property
    def is_lost(self) -> bool:
        return self.lives_left <= 0

    @property
    def is_over(self) -> bool:
        return self.is_won or self.is_lost

    def guess(self, letter: str) -> GuessResult:
        if self.is_over:
            raise GameOverError("The game is over.")
        letter = letter.strip().lower()
        if len(letter) != 1 or letter not in string.ascii_lowercase:
            raise ValueError("Guess a single letter a-z.")
        if letter in self.guessed:
            return GuessResult.REPEAT
        self.guessed.add(letter)
        return GuessResult.HIT if letter in self.letters else GuessResult.MISS

    def guess_word(self, attempt: str) -> bool:
        """Guessing the whole word: right → win, wrong → costs one life."""
        if self.is_over:
            raise GameOverError("The game is over.")
        if attempt.strip().lower() == self.word:
            self.guessed |= self.letters
            return True
        self.wrong_words += 1
        return False

    def to_dict(self) -> dict:
        return {"word": self.word, "category": self.category, "guessed": sorted(self.guessed), "wrong_words": self.wrong_words}

    @classmethod
    def from_dict(cls, data: dict) -> HangmanGame:
        return cls(data["word"], data["category"], set(data["guessed"]), data.get("wrong_words", 0))
