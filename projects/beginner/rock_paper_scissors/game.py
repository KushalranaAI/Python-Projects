"""A match: plays rounds against a strategy and keeps the score."""

from __future__ import annotations

from dataclasses import dataclass, field

from .players import Strategy
from .rules import Outcome


@dataclass(frozen=True)
class Round:
    human: str
    computer: str
    outcome: Outcome
    explanation: str


@dataclass
class Match:
    opponent: Strategy
    history: list[tuple[str, str]] = field(default_factory=list)

    def play(self, human_move: str) -> Round:
        rules = self.opponent.rules
        human_move = rules.validate(human_move)
        computer_move = self.opponent.choose(self.history)    # decided BEFORE seeing the human's move
        self.history.append((human_move, computer_move))
        return Round(human_move, computer_move, rules.judge(human_move, computer_move), rules.explain(human_move, computer_move))

    @property
    def rounds(self) -> list[Round]:
        rules = self.opponent.rules
        return [Round(h, c, rules.judge(h, c), rules.explain(h, c)) for h, c in self.history]

    @property
    def score(self) -> dict[Outcome, int]:
        counts = dict.fromkeys(Outcome, 0)
        for r in self.rounds:
            counts[r.outcome] += 1
        return counts

    @property
    def win_rate(self) -> float:
        decided = self.score[Outcome.WIN] + self.score[Outcome.LOSE]
        return self.score[Outcome.WIN] / decided if decided else 0.0
