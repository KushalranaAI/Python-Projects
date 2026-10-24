---
title: Quiz App
order: 5
icon: 🧠
time: 2-3 hours
summary: A multiple-choice quiz with categories, scoring, explanations and a review screen. It ships with 30 questions about Python itself, so building it doubles as revision.
python_skills:
  - Loading structured data from JSON
  - random.sample for picking without repeats
  - zip, enumerate, sum over generators
  - dict.setdefault for grouping
oop_concepts:
  - Value objects validated in __post_init__
  - A bank class with __len__ (a 'dunder' method)
  - A session object that holds progress
  - A result object with a computed property
clean_code:
  - Content (questions) separate from code
  - Store ids, not whole objects, in the session
  - Fail fast on bad data (invalid answer index, duplicate ids)
  - Tests that build tiny fake data instead of using the real file
features:
  - 30 questions in 5 categories (Basics, Data structures, Functions, OOP, Clean code)
  - Choose category and length; immediate feedback with an explanation
  - Final score, score per category and a full review
architecture: |
  classDiagram
    class Question {
      <<frozen dataclass>>
      +id int
      +category str
      +prompt str
      +options tuple
      +answer int
      +explanation str
      +is_correct(choice) bool
      +correct_option str
    }
    class QuestionBank {
      -_by_id dict
      +from_json(path)$ QuestionBank
      +__len__() int
      +get(id) Question
      +categories list
      +pick(count, category, rng) list
    }
    class QuizSession {
      +bank QuestionBank
      +question_ids list~int~
      +choices list~int~
      +start(bank, count, category, rng)$ QuizSession
      +current Question
      +answer(choice) AnswerResult
      +score int
      +percent int
      +score_by_category() dict
      +to_dict() dict
    }
    class AnswerResult {
      +question Question
      +choice int
      +correct bool
    }
    QuestionBank "1" o-- "*" Question
    QuizSession --> QuestionBank
    QuizSession ..> AnswerResult : creates
flow: |
  stateDiagram-v2
    [*] --> Choosing : open page
    Choosing --> Answering : start(category, count)
    Answering --> Answering : answer() & more questions
    Answering --> Finished : answer() on last question
    Finished --> Choosing : reset
steps:
  - title: Put the content in a data file
    files: [questions.json]
    body: |
      Questions are **content**, not code. Keeping them in JSON means anyone can add questions without touching Python,
      and the code stays short. Each question has an id, category, prompt, options, the index of the right answer and an explanation.
  - title: Validate each Question when it's created
    files: [quiz.py]
    body: |
      A frozen dataclass with `__post_init__` refuses broken data (fewer than two options, an answer index out of range)
      the moment the file is loaded, not halfway through someone's quiz. This is **fail fast**.
  - title: Wrap the questions in a QuestionBank
    files: [quiz.py]
    body: |
      `QuestionBank.from_json` is an alternative constructor. `__len__` lets you write `len(bank)`, a first taste of
      Python's *data model*. `pick` uses `random.sample`, which never returns the same question twice.
  - title: Track one run with QuizSession
    files: [quiz.py]
    body: |
      The session stores only `question_ids` and `choices`. Score, percentage, current question and per-category
      results are all **computed** from them. A tiny state like this is easy to save in a cookie and to test.
  - title: Test with a hand-made mini bank
    files: [tests/test_quiz.py]
    body: |
      Tests build a 3-question bank in a fixture, so they're independent of the real JSON file. One extra test checks
      that the *real* file loads, which catches content mistakes too.
  - title: Two interfaces, one session class
    files: [cli.py, web.py, templates/quiz_app/index.html]
    body: |
      The CLI loops over `quiz.current`, and the web app does one step per request. Both call `answer()` and display
      `AnswerResult`. The flow is a small **state machine**: choosing → answering → finished.
exercises:
  - 'Add a **timer**: each answer records how many seconds it took, and the summary shows the slowest questions.'
  - "Support **multiple-correct** questions (`answers: [0, 2]`). Which classes change?"
  - Save high scores per category to a JSON file with a `ScoreBoard` class and show the top 5.
  - Write 10 new questions for a "Files & errors" category and check them with the existing tests.
---

## Data vs. code

The quiz engine knows nothing about Python trivia, and the questions know nothing about the engine. Replace
`questions.json` with geography questions and the app becomes a geography quiz. This separation is the same idea
as configuration files, CMS content and database rows: the engine handles **behaviour**, the data supplies the **content**.
