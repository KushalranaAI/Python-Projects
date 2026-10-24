"""Terminal quiz."""

from __future__ import annotations

from .quiz import QuestionBank, QuizSession

LETTERS = "ABCD"


def main() -> None:
    bank = QuestionBank.from_json()
    print(f"🧠 Python Quiz - {len(bank)} questions in {', '.join(bank.categories)}")
    quiz = QuizSession.start(bank, count=10)
    while not quiz.finished:
        q = quiz.current
        print(f"\nQ{quiz.position + 1}/{quiz.total} [{q.category}] {q.prompt}")
        for letter, option in zip(LETTERS, q.options):
            print(f"  {letter}) {option}")
        while (choice := input("Your answer: ").strip().upper()) not in LETTERS[: len(q.options)]:
            print("Type A, B, C or D.")
        result = quiz.answer(LETTERS.index(choice))
        print("✅ Correct!" if result.correct else f"❌ It's {LETTERS[q.answer]}) {q.correct_option}")
        print("  ", q.explanation)
    print(f"\nScore: {quiz.score}/{quiz.total} ({quiz.percent}%)")
    for category, (right, total) in quiz.score_by_category().items():
        print(f"  {category:<16} {right}/{total}")


if __name__ == "__main__":
    main()
