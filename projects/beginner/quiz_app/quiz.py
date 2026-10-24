"""Questions, a question bank loaded from JSON, and a quiz session that tracks progress and score."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BANK = Path(__file__).with_name("questions.json")


@dataclass(frozen=True)
class Question:
    id: int
    category: str
    prompt: str
    options: tuple[str, ...]
    answer: int
    explanation: str = ""

    def __post_init__(self):
        if len(self.options) < 2:
            raise ValueError(f"Question {self.id} needs at least two options.")
        if not 0 <= self.answer < len(self.options):
            raise ValueError(f"Question {self.id}: answer index {self.answer} is out of range.")

    def is_correct(self, choice: int) -> bool:
        return choice == self.answer

    @property
    def correct_option(self) -> str:
        return self.options[self.answer]


class QuestionBank:
    def __init__(self, questions: list[Question]):
        ids = [q.id for q in questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Question ids must be unique.")
        self._by_id = {q.id: q for q in questions}

    @classmethod
    def from_json(cls, path: Path = DEFAULT_BANK) -> QuestionBank:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Question(q["id"], q["category"], q["prompt"], tuple(q["options"]), q["answer"], q.get("explanation", ""))
                    for q in raw])

    def __len__(self) -> int:
        return len(self._by_id)

    def get(self, question_id: int) -> Question:
        return self._by_id[question_id]

    @property
    def categories(self) -> list[str]:
        return sorted({q.category for q in self._by_id.values()})

    def pick(self, count: int, category: str | None = None, rng: random.Random | None = None) -> list[Question]:
        pool = [q for q in self._by_id.values() if category in (None, q.category)]
        if not pool:
            raise ValueError(f"No questions in category {category!r}.")
        return (rng or random.Random()).sample(pool, min(count, len(pool)))


@dataclass(frozen=True)
class AnswerResult:
    question: Question
    choice: int

    @property
    def correct(self) -> bool:
        return self.question.is_correct(self.choice)


class QuizFinishedError(Exception):
    pass


@dataclass
class QuizSession:
    """One run through a list of questions. Only ids and choices are stored, so it serialises to a tiny dict."""

    bank: QuestionBank
    question_ids: list[int]
    choices: list[int] = field(default_factory=list)

    @classmethod
    def start(cls, bank: QuestionBank, count: int = 10, category: str | None = None, rng: random.Random | None = None) -> QuizSession:
        return cls(bank, [q.id for q in bank.pick(count, category, rng)])

    @property
    def total(self) -> int:
        return len(self.question_ids)

    @property
    def position(self) -> int:
        return len(self.choices)

    @property
    def finished(self) -> bool:
        return self.position >= self.total

    @property
    def current(self) -> Question:
        if self.finished:
            raise QuizFinishedError("No more questions.")
        return self.bank.get(self.question_ids[self.position])

    def answer(self, choice: int) -> AnswerResult:
        question = self.current
        if not 0 <= choice < len(question.options):
            raise ValueError("Pick one of the options.")
        self.choices.append(choice)
        return AnswerResult(question, choice)

    @property
    def results(self) -> list[AnswerResult]:
        return [AnswerResult(self.bank.get(qid), c) for qid, c in zip(self.question_ids, self.choices)]

    @property
    def score(self) -> int:
        return sum(r.correct for r in self.results)

    @property
    def percent(self) -> int:
        return round(100 * self.score / self.position) if self.position else 0

    def score_by_category(self) -> dict[str, tuple[int, int]]:
        table: dict[str, list[int]] = {}
        for r in self.results:
            right_total = table.setdefault(r.question.category, [0, 0])
            right_total[0] += r.correct
            right_total[1] += 1
        return {cat: (right, total) for cat, (right, total) in table.items()}

    def to_dict(self) -> dict:
        return {"question_ids": self.question_ids, "choices": self.choices}

    @classmethod
    def from_dict(cls, bank: QuestionBank, data: dict) -> QuizSession:
        return cls(bank, list(data["question_ids"]), list(data["choices"]))
