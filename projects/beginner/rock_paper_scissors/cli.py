"""Terminal interface."""

from __future__ import annotations

from .game import Match
from .players import STRATEGIES, make_strategy
from .rules import RULESETS, Outcome


def main() -> None:
    print("✊✋✌️  Rock Paper Scissors")
    rules = RULESETS["lizard-spock" if input("Lizard-Spock rules? [y/N] ").lower() == "y" else "classic"]
    for name, cls in STRATEGIES.items():
        print(f"  {name:<10} {cls.description}")
    while True:
        try:
            match = Match(make_strategy(input("Opponent [frequency]: ").strip() or "frequency", rules))
            break
        except ValueError as error:
            print(error)
    print(f"Moves: {', '.join(rules.moves)}. Type 'q' to stop.")
    while (move := input("> ").strip().lower()) not in {"q", "quit"}:
        try:
            r = match.play(move)
        except ValueError as error:
            print(error)
            continue
        print(f"  computer: {r.computer} → {r.explanation} You {r.outcome.value}!")
    s = match.score
    print(f"Final: {s[Outcome.WIN]} wins, {s[Outcome.LOSE]} losses, {s[Outcome.DRAW]} draws ({match.win_rate:.0%} of decided rounds)")


if __name__ == "__main__":
    main()
