"""Terminal interface."""

from __future__ import annotations

from .art import drawing
from .game import GuessResult, HangmanGame
from .words import CATEGORIES


def main() -> None:
    print("🪢 Hangman - categories:", ", ".join(CATEGORIES))
    game = HangmanGame.random(input("Category (Enter for random): ").strip().title() or None)
    print(f"Category: {game.category}")
    while not game.is_over:
        print(f"\n{drawing(game.mistakes)}")
        print(f"\n  {game.masked}    lives: {game.lives_left}   misses: {' '.join(game.misses) or '-'}")
        text = input("Letter (or the whole word): ").strip()
        try:
            if len(text) > 1:
                print("✅ Yes!" if game.guess_word(text) else "❌ Not the word.")
                continue
            result = game.guess(text)
            print({GuessResult.HIT: "✅ Yes!", GuessResult.MISS: "❌ No.", GuessResult.REPEAT: "You already tried that."}[result])
        except ValueError as error:
            print(error)
    print(drawing(6) if game.is_lost else "")
    print(f"{'🎉 You won!' if game.is_won else '💀 You lost.'} The word was: {game.word.upper()}")


if __name__ == "__main__":
    main()
