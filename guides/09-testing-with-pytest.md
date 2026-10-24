---
title: Testing with pytest
order: 9
icon: 🧪
summary: How to write fast, readable tests - plain asserts, fixtures, parametrize, tmp_path, monkeypatch and fakes for time and randomness.
---

## Why test?
Tests let you change code without fear. Every project here has a `tests/` folder, and the **Run the tests** button on
each project page runs them.

```bash
python -m pytest                                   # everything
python -m pytest projects/beginner/todo_list -v    # one project, verbose
python -m pytest -k streak                         # tests whose name contains "streak"
```

## A test is a function that asserts

```python
def test_feedback_points_towards_the_secret():
    game = GuessingGame(high=100, max_attempts=5, secret=42)    # arrange
    feedback = game.guess(10)                                   # act
    assert feedback is Feedback.TOO_LOW                         # assert
```

Name tests after the **behaviour**, not the method: `test_running_out_of_attempts_ends_the_game`.

## Expected errors

```python
with pytest.raises(GameOverError):
    game.guess(3)

with pytest.raises(ValueError, match="Line 2"):     # match is a regex - escape ( ) [ ] .
    parse_items("ok, 1\nbroken", bill)
```

## Parametrize: many cases, one test

```python
@pytest.mark.parametrize("value, src, dst, expected", [
    (100, "°C", "°F", 212), (-40, "°C", "°F", -40), (1, "GiB", "MiB", 1024),
])
def test_known_conversions(value, src, dst, expected):
    assert registry.convert(value, src, dst) == pytest.approx(expected)
```

`pytest.approx` compares floats with a tolerance, so `0.1 + 0.2 == 0.3` passes.

## Fixtures: shared setup

```python
@pytest.fixture
def todo() -> TodoList:
    t = TodoList()
    t.add("Write tests", Priority.HIGH)
    return t

def test_toggle(todo):          # pytest passes the fixture's return value in by name
    ...
```

Built-in fixtures you'll use:
- `tmp_path`: a fresh temporary folder per test (files, SQLite databases)
- `monkeypatch`: temporarily change environment variables or attributes

## Fakes for time and randomness

| Hidden dependency | Make it injectable | In tests |
|---|---|---|
| `random.randint` | `rng: random.Random` parameter | `random.Random(42)` |
| `date.today()` | `today: date` parameter | `date(2026, 3, 18)` |
| `datetime.now()` | `clock` callable | a `FakeClock` you can move forward |
| a real database | a repository object | `tmp_path / "test.db"` |

## Test properties, not just examples
Some of the strongest tests check **invariants**: shares always sum to the bill's total, a search breakdown sums to
the score, `decode(encode(n)) == n`, `save` then `load` gives back an equal object.
