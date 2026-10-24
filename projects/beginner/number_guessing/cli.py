"""Terminal interface: reads input, prints messages and delegates every rule to GuessingGame."""

from __future__ import annotations

from .game import Difficulty, Feedback, GuessingGame, optimal_attempts


def ask_difficulty() -> Difficulty:
    options = {str(i): d for i, d in enumerate(Difficulty, start=1)}
    for key, d in options.items():
        print(f"  {key}) {d.name.title():<7} 1-{d.high}, {d.attempts} attempts")
    while (choice := input("Choose a difficulty [1]: ").strip() or "1") not in options:
        print("Please type one of:", ", ".join(options))
    return options[choice]


def ask_number(prompt: str) -> int:
    while True:
        text = input(prompt).strip()
        if text.lstrip("-").isdigit():
            return int(text)
        print("That's not a whole number - try again.")


def play_round() -> None:
    game = GuessingGame.new(ask_difficulty())
    print(f"\nI'm thinking of a number between 1 and {game.high}. "
          f"(Binary search needs at most {optimal_attempts(game.high)} guesses.)")
    while not game.is_over:
        try:
            feedback = game.guess(ask_number(f"[{game.attempts_left} left] Your guess: "))
        except ValueError as error:
            print(error)
            continue
        print(feedback.value)
    if game.is_won:
        print(f"🎉 You got it in {game.attempts_used} guesses!")
    else:
        print(f"Out of attempts - the number was {game.secret}.")


def main() -> None:
    print("🎯 Number Guessing Game")
    while True:
        play_round()
        if input("\nPlay again? [y/N] ").strip().lower() != "y":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
