import random
import string

import pytest

from projects.beginner.password_toolkit.toolkit import (AMBIGUOUS, SYMBOLS, PasswordGenerator, PasswordPolicy,
                                                        check_strength)


@pytest.fixture
def gen() -> PasswordGenerator:
    return PasswordGenerator(random.Random(42))   # deterministic for tests only - real use is secrets.SystemRandom


def test_password_has_requested_length_and_every_class(gen):
    for _ in range(50):
        pw = gen.password(PasswordPolicy(length=8))
        assert len(pw) == 8
        assert any(c.islower() for c in pw) and any(c.isupper() for c in pw)
        assert any(c.isdigit() for c in pw) and any(c in SYMBOLS for c in pw)


def test_disabled_classes_never_appear(gen):
    pw = gen.password(PasswordPolicy(length=64, symbols=False, uppercase=False))
    assert set(pw) <= set(string.ascii_lowercase + string.digits)


def test_ambiguous_characters_can_be_excluded(gen):
    pw = gen.password(PasswordPolicy(length=128, exclude_ambiguous=True))
    assert not set(pw) & AMBIGUOUS


@pytest.mark.parametrize("policy", [PasswordPolicy(lowercase=False, uppercase=False, digits=False, symbols=False),
                                    PasswordPolicy(length=3), PasswordPolicy(length=500)])
def test_invalid_policies_are_rejected(gen, policy):
    with pytest.raises(ValueError):
        gen.password(policy)


def test_entropy_of_a_policy():
    assert PasswordPolicy(length=10, uppercase=False, symbols=False).entropy_bits == pytest.approx(10 * 5.169925, rel=1e-6)


def test_passphrase(gen):
    phrase = gen.passphrase(4, separator=" ")
    assert len(phrase.split()) == 4 and all(w[0].isupper() for w in phrase.split())
    with pytest.raises(ValueError):
        gen.passphrase(2)


@pytest.mark.parametrize("password, max_score", [("password", 0), ("123456", 0), ("aaaaaaaa", 0), ("Summer2024!", 2), ("abcd1234", 1)])
def test_weak_passwords_score_low(password, max_score):
    assert check_strength(password).score <= max_score


def test_strong_password_scores_high():
    report = check_strength("r7#Vq!m2Lp@x9Zw$")
    assert report.score == 4 and not report.warnings


def test_common_password_warns():
    assert "most common" in check_strength("qwerty").warnings[0]


def test_crack_time_text():
    assert check_strength("").crack_time == "instantly"
    assert "centuries" in check_strength("r7#Vq!m2Lp@x9Zw$").crack_time
