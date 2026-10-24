import random

import pytest

from projects.beginner.hangman.art import STAGES, drawing
from projects.beginner.hangman.game import GameOverError, GuessResult, HangmanGame
from projects.beginner.hangman.words import CATEGORIES


def test_masking_and_winning():
    game = HangmanGame("class")
    assert game.masked == "_ _ _ _ _"
    assert game.guess("s") is GuessResult.HIT
    assert game.masked == "_ _ _ s s"
    for letter in "cla":
        game.guess(letter)
    assert game.is_won and game.is_over


def test_spaces_and_hyphens_are_shown():
    assert HangmanGame("new zealand").masked == "_ _ _   _ _ _ _ _ _ _"


def test_misses_cost_lives_and_end_the_game():
    game = HangmanGame("a")
    for letter in "bcdefg":
        assert game.guess(letter) is GuessResult.MISS
    assert game.is_lost and game.misses == list("bcdefg")
    with pytest.raises(GameOverError):
        game.guess("a")


def test_repeat_guess_is_free():
    game = HangmanGame("abc")
    game.guess("z")
    assert game.guess("Z") is GuessResult.REPEAT and game.lives_left == 5


@pytest.mark.parametrize("bad", ["", "ab", "1", "é"])
def test_invalid_guesses(bad):
    with pytest.raises(ValueError):
        HangmanGame("abc").guess(bad)


def test_guessing_the_whole_word():
    game = HangmanGame("python")
    assert not game.guess_word("java") and game.lives_left == 5
    assert game.guess_word("Python") and game.is_won


def test_random_game_uses_category_and_seed():
    game = HangmanGame.random("Animals", random.Random(3))
    assert game.word in CATEGORIES["Animals"] and game.category == "Animals"


def test_round_trip():
    game = HangmanGame("loop", "Python")
    game.guess("o")
    game.guess("x")
    assert HangmanGame.from_dict(game.to_dict()) == game


def test_word_lists_are_valid_words():
    for words in CATEGORIES.values():
        for word in words:
            HangmanGame(word)


def test_art_has_a_stage_per_miss():
    assert len(STAGES) == 7 and drawing(99) == STAGES[-1]
