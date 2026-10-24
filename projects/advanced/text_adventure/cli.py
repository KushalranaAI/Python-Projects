"""Play in the terminal. 'save' / 'load' write the game state to a JSON file."""

from __future__ import annotations

import json

from projects.ui_kit import data_path

from .engine import Game, GameState, World


def main() -> None:
    world = World.load()
    game = Game(world)
    save_file = data_path("adventure_save.json")
    print(f"📜 {world.data['title']}\n\n{world.data['intro']}\n\n{game.describe_room()}")
    while not game.state.won:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text in {"quit", "q"}:
            break
        if text == "save":
            save_file.write_text(json.dumps(game.state.to_dict()))
            print(f"Saved to {save_file}")
            continue
        if text == "load" and save_file.exists():
            game = Game(world, GameState.from_dict(json.loads(save_file.read_text())))
            print(game.describe_room())
            continue
        print(game.handle(text))


if __name__ == "__main__":
    main()
