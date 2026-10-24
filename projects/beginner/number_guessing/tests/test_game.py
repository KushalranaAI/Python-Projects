import random

import pytest

from projects.beginner.number_guessing.game import Difficulty, Feedback, GameOverError, GuessingGame, optimal_attempts


def make_game(secret: int = 42, high: int = 100, attempts: int = 5) -> GuessingGame:
    return GuessingGame(high=high, max_attempts=attempts, secret=secret)


def test_feedback_points_towards_the_secret():
    game = make_game(secret=42)
    assert game.guess(10) is Feedback.TOO_LOW
    assert game.guess(90) is Feedback.TOO_HIGH
    assert game.guess(42) is Feedback.CORRECT
    assert game.is_won and game.is_over


def test_running_out_of_attempts_ends_the_game():
    game = make_game(attempts=2)
    game.guess(1)
    game.guess(2)
    assert game.is_over and not game.is_won
    with pytest.raises(GameOverError):
        game.guess(3)


def test_out_of_range_guess_is_rejected_and_not_counted():
    game = make_game(high=50)
    with pytest.raises(ValueError):
        game.guess(51)
    assert game.attempts_used == 0


def test_range_hint_narrows_after_each_guess():
    game = make_game(secret=42)
    game.guess(30)
    game.guess(60)
    assert game.range_hint == (31, 59)


def test_new_game_uses_the_injected_random_generator():
    a = GuessingGame.new(Difficulty.MEDIUM, random.Random(7))
    b = GuessingGame.new(Difficulty.MEDIUM, random.Random(7))
    assert a.secret == b.secret and 1 <= a.secret <= 100


def test_round_trip_through_a_dict():
    game = make_game()
    game.guess(10)
    assert GuessingGame.from_dict(game.to_dict()) == game


@pytest.mark.parametrize("high, expected", [(1, 1), (100, 7), (500, 9)])
def test_binary_search_bound(high, expected):
    assert optimal_attempts(high) == expected
