import copy
import json

import pytest

from projects.advanced.text_adventure.engine import Game, GameState, World, mermaid_map

WALKTHROUGH = ["take lamp", "e", "take note", "n", "take key", "s", "use lamp", "down", "take gear", "up", "w",
               "n", "use key", "n", "take codex", "s", "s"]


@pytest.fixture
def game() -> Game:
    return Game(World.load())


def test_world_file_is_valid():
    World.load().validate()


def test_bad_world_is_rejected(tmp_path):
    data = copy.deepcopy(World.load().data)
    data["rooms"]["hall"]["exits"]["south"] = "nowhere"
    (tmp_path / "w.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="nowhere"):
        World.load(tmp_path / "w.json")


def test_full_walkthrough_wins(game):
    for command in WALKTHROUGH:
        reply = game.handle(command)
    assert game.state.won and "You win" in reply
    assert "already won" in game.handle("look")


def test_locked_door(game):
    game.handle("n")
    assert "locked" in game.handle("n")


def test_darkness_needs_a_lit_lamp(game):
    game.handle("e")
    assert "pitch black" in game.handle("down")
    assert "can't see" in game.handle("take gear")


def test_puzzle_requires_the_gear(game):
    for command in ["take lamp", "e", "n", "take key", "s", "w", "n", "use key", "n"]:
        game.handle(command)
    assert "empty slot" in game.handle("take codex")


@pytest.mark.parametrize("command, fragment", [("dance", "don't know"), ("", "Say something"), ("go sideways", "can't go"),
                                               ("take unicorn", "no unicorn"), ("drop lamp", "aren't carrying")])
def test_friendly_errors(game, command, fragment):
    assert fragment in game.handle(command)


def test_synonyms_and_filler_words(game):
    assert "brass lamp" in game.handle("grab the brass lamp")
    assert "carry" in game.handle("i")
    assert "Narrow Corridor" in game.handle("walk to the east")


def test_save_and_restore(game):
    for command in WALKTHROUGH[:5]:
        game.handle(command)
    restored = Game(game.world, GameState.from_dict(json.loads(json.dumps(game.state.to_dict()))))
    assert restored.state == game.state and "iron key" in restored.handle("inventory")


def test_map_shows_only_visited_rooms(game):
    game.handle("e")
    text = mermaid_map(game)
    assert "Narrow Corridor" in text and "Great Hall" in text and "Vault" not in text
