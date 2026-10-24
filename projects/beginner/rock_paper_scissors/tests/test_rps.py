import random

import pytest

from projects.beginner.rock_paper_scissors.game import Match
from projects.beginner.rock_paper_scissors.players import (CycleStrategy, FrequencyStrategy, MarkovStrategy, Strategy,
                                                           make_strategy)
from projects.beginner.rock_paper_scissors.rules import CLASSIC, LIZARD_SPOCK, Outcome


@pytest.mark.parametrize("mine, theirs, outcome", [
    ("rock", "scissors", Outcome.WIN), ("rock", "paper", Outcome.LOSE), ("paper", "paper", Outcome.DRAW), ("Scissors ", "paper", Outcome.WIN),
])
def test_classic_rules(mine, theirs, outcome):
    assert CLASSIC.judge(mine, theirs) is outcome


def test_every_lizard_spock_move_beats_exactly_two_others():
    for move in LIZARD_SPOCK.moves:
        assert len(LIZARD_SPOCK.beats[move]) == 2
        losses = [m for m in LIZARD_SPOCK.moves if move in LIZARD_SPOCK.beats[m]]
        assert len(losses) == 2


def test_explanations():
    assert CLASSIC.explain("paper", "rock") == "Paper covers rock."
    assert LIZARD_SPOCK.explain("rock", "spock") == "Spock vaporizes rock."


def test_invalid_move():
    with pytest.raises(ValueError):
        CLASSIC.validate("lizard")


def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        Strategy(CLASSIC)


def test_cycle_strategy_is_exploitable():
    match = Match(CycleStrategy(CLASSIC))
    for computer_move in ["rock", "paper", "scissors"] * 3:
        assert match.play(CLASSIC.counter(computer_move)).outcome is Outcome.WIN


def test_frequency_strategy_punishes_a_favourite():
    match = Match(FrequencyStrategy(CLASSIC, random.Random(0)))
    outcomes = [match.play("rock").outcome for _ in range(10)]
    assert outcomes[1:] == [Outcome.LOSE] * 9


def test_markov_strategy_learns_a_pattern():
    match = Match(MarkovStrategy(CLASSIC, random.Random(0)))
    for move in ["rock", "paper"] * 10:
        match.play(move)
    assert [r.outcome for r in match.rounds[-6:]] == [Outcome.LOSE] * 6


def test_score_and_win_rate():
    match = Match(CycleStrategy(CLASSIC))
    match.play("paper")      # vs rock: win
    match.play("paper")      # vs paper: draw
    match.play("paper")      # vs scissors: lose
    assert match.score == {Outcome.WIN: 1, Outcome.LOSE: 1, Outcome.DRAW: 1} and match.win_rate == 0.5


def test_factory():
    assert isinstance(make_strategy("markov", CLASSIC), MarkovStrategy)
    with pytest.raises(ValueError):
        make_strategy("cheater", CLASSIC)
