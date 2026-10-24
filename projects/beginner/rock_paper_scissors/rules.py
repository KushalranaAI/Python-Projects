"""Game rules as data: which move beats which, and why. Two rule sets: classic and Lizard-Spock."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Outcome(Enum):
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"


@dataclass(frozen=True)
class Ruleset:
    name: str
    beats: dict[str, dict[str, str]]          # move -> {move it beats: verb}

    @property
    def moves(self) -> list[str]:
        return list(self.beats)

    def validate(self, move: str) -> str:
        move = move.strip().lower()
        if move not in self.beats:
            raise ValueError(f"'{move}' isn't a move. Choose from: {', '.join(self.moves)}.")
        return move

    def judge(self, mine: str, theirs: str) -> Outcome:
        mine, theirs = self.validate(mine), self.validate(theirs)
        if mine == theirs:
            return Outcome.DRAW
        return Outcome.WIN if theirs in self.beats[mine] else Outcome.LOSE

    def explain(self, mine: str, theirs: str) -> str:
        if mine == theirs:
            return f"Both chose {mine}."
        winner, loser = (mine, theirs) if theirs in self.beats[mine] else (theirs, mine)
        return f"{winner.title()} {self.beats[winner][loser]} {loser}."

    def counter(self, move: str) -> str:
        """A move that beats `move` (first one in table order)."""
        return next(m for m, victims in self.beats.items() if move in victims)


CLASSIC = Ruleset("classic", {
    "rock": {"scissors": "crushes"},
    "paper": {"rock": "covers"},
    "scissors": {"paper": "cuts"},
})

LIZARD_SPOCK = Ruleset("lizard-spock", {
    "rock": {"scissors": "crushes", "lizard": "crushes"},
    "paper": {"rock": "covers", "spock": "disproves"},
    "scissors": {"paper": "cuts", "lizard": "decapitates"},
    "lizard": {"spock": "poisons", "paper": "eats"},
    "spock": {"scissors": "smashes", "rock": "vaporizes"},
})

RULESETS = {r.name: r for r in (CLASSIC, LIZARD_SPOCK)}
