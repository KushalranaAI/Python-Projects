import random

import pytest

from projects.beginner.quiz_app.quiz import Question, QuestionBank, QuizFinishedError, QuizSession


@pytest.fixture
def bank() -> QuestionBank:
    return QuestionBank([
        Question(1, "Maths", "1+1?", ("1", "2"), 1),
        Question(2, "Maths", "2*3?", ("6", "5"), 0),
        Question(3, "Words", "Opposite of hot?", ("cold", "warm", "wet"), 0),
    ])


def test_bundled_bank_is_valid():
    real = QuestionBank.from_json()
    assert len(real) == 30 and "OOP" in real.categories


def test_invalid_questions_are_rejected():
    with pytest.raises(ValueError):
        Question(9, "x", "?", ("only one",), 0)
    with pytest.raises(ValueError):
        Question(9, "x", "?", ("a", "b"), 5)


def test_duplicate_ids_are_rejected():
    q = Question(1, "x", "?", ("a", "b"), 0)
    with pytest.raises(ValueError):
        QuestionBank([q, q])


def test_pick_by_category(bank):
    assert {q.id for q in bank.pick(10, "Maths")} == {1, 2}


def test_session_scores_answers(bank):
    quiz = QuizSession(bank, [1, 2, 3])
    assert quiz.answer(1).correct
    assert not quiz.answer(1).correct
    quiz.answer(0)
    assert quiz.finished and quiz.score == 2 and quiz.percent == 67
    assert quiz.score_by_category() == {"Maths": (1, 2), "Words": (1, 1)}
    with pytest.raises(QuizFinishedError):
        quiz.current


def test_invalid_choice_is_not_recorded(bank):
    quiz = QuizSession(bank, [1])
    with pytest.raises(ValueError):
        quiz.answer(7)
    assert quiz.position == 0


def test_start_is_reproducible_with_a_seed(bank):
    a = QuizSession.start(bank, 2, rng=random.Random(1))
    b = QuizSession.start(bank, 2, rng=random.Random(1))
    assert a.question_ids == b.question_ids and len(a.question_ids) == 2


def test_session_round_trip(bank):
    quiz = QuizSession(bank, [3, 1])
    quiz.answer(0)
    again = QuizSession.from_dict(bank, quiz.to_dict())
    assert again.question_ids == [3, 1] and again.score == 1 and again.current.id == 1
