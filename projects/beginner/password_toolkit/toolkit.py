"""Generate strong passwords and passphrases, and estimate how strong a password is.

Security note: we use `secrets` (a cryptographically secure generator), never `random`, whose output
can be predicted from a few hundred values. The generator is injectable so tests can be deterministic.
"""

from __future__ import annotations

import math
import re
import secrets
import string
from dataclasses import dataclass, field

from .wordlist import WORDS

AMBIGUOUS = set("Il1O0o")
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/"
COMMON_PASSWORDS = {"password", "123456", "123456789", "qwerty", "abc123", "111111", "letmein", "iloveyou",
                    "admin", "welcome", "monkey", "dragon", "football", "sunshine", "princess", "password1"}
SEQUENCES = ["abcdefghijklmnopqrstuvwxyz", "0123456789", "qwertyuiop", "asdfghjkl", "zxcvbnm"]


@dataclass(frozen=True)
class PasswordPolicy:
    length: int = 16
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False

    def character_classes(self) -> list[str]:
        classes = [chars for enabled, chars in [(self.lowercase, string.ascii_lowercase), (self.uppercase, string.ascii_uppercase),
                                                (self.digits, string.digits), (self.symbols, SYMBOLS)] if enabled]
        if self.exclude_ambiguous:
            classes = ["".join(c for c in chars if c not in AMBIGUOUS) for chars in classes]
        return classes

    def validate(self) -> None:
        classes = self.character_classes()
        if not classes:
            raise ValueError("Choose at least one type of character.")
        if not len(classes) <= self.length <= 128:
            raise ValueError(f"Length must be between {len(classes)} and 128.")

    @property
    def pool_size(self) -> int:
        return sum(len(c) for c in self.character_classes())

    @property
    def entropy_bits(self) -> float:
        return self.length * math.log2(self.pool_size)


class PasswordGenerator:
    def __init__(self, rng: secrets.SystemRandom | None = None):
        self.rng = rng or secrets.SystemRandom()

    def password(self, policy: PasswordPolicy) -> str:
        """Guarantee one character from every chosen class, fill the rest from the whole pool, then shuffle."""
        policy.validate()
        classes = policy.character_classes()
        pool = "".join(classes)
        chars = [self.rng.choice(c) for c in classes]
        chars += [self.rng.choice(pool) for _ in range(policy.length - len(chars))]
        self.rng.shuffle(chars)
        return "".join(chars)

    def passphrase(self, words: int = 5, separator: str = "-", capitalize: bool = True) -> str:
        if not 3 <= words <= 12:
            raise ValueError("Use between 3 and 12 words.")
        chosen = [self.rng.choice(WORDS) for _ in range(words)]
        return separator.join(w.capitalize() if capitalize else w for w in chosen)

    @staticmethod
    def passphrase_entropy(words: int) -> float:
        return words * math.log2(len(WORDS))


@dataclass
class StrengthReport:
    password: str
    entropy_bits: float
    score: int                                     # 0 (very weak) … 4 (very strong)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    LABELS = ("Very weak", "Weak", "Fair", "Strong", "Very strong")

    @property
    def label(self) -> str:
        return self.LABELS[self.score]

    @property
    def crack_time(self) -> str:
        """Average time to guess at 10 billion guesses per second (an offline attack on a fast hash)."""
        seconds = 2 ** self.entropy_bits / 2 / 1e10
        for unit, size in [("centuries", 3.15e9), ("years", 3.15e7), ("days", 86400), ("hours", 3600), ("minutes", 60), ("seconds", 1)]:
            if seconds >= size:
                return f"{seconds / size:,.0f} {unit}" if seconds / size < 1e6 else f"more than a million {unit}"
        return "instantly"


def _pool_size(password: str) -> int:
    pool = 0
    pool += 26 if re.search(r"[a-z]", password) else 0
    pool += 26 if re.search(r"[A-Z]", password) else 0
    pool += 10 if re.search(r"\d", password) else 0
    pool += 33 if re.search(r"[^a-zA-Z\d]", password) else 0
    return pool


def check_strength(password: str) -> StrengthReport:
    """A simple estimator: character-pool entropy, minus penalties for the patterns attackers try first."""
    lowered = password.lower()
    warnings, suggestions = [], []
    # A run like "aaaa" adds almost no information, so collapse runs and count each repeat as half a character.
    collapsed = re.sub(r"(.)\1+", r"\1", password)
    effective_length = len(collapsed) + 0.5 * (len(password) - len(collapsed))
    bits = effective_length * math.log2(_pool_size(password)) if password else 0.0
    if lowered in COMMON_PASSWORDS:
        warnings.append("This is one of the most common passwords.")
        bits = min(bits, 4)
    if re.search(r"(.)\1{2,}", password):
        warnings.append("Repeated characters (like 'aaa') are easy to guess.")
    if any(lowered[i:i + 4] in seq or lowered[i:i + 4] in seq[::-1] for seq in SEQUENCES for i in range(len(lowered) - 3)):
        warnings.append("Contains a sequence like 'abcd', '1234' or 'qwer'.")
        bits *= 0.75
    if re.fullmatch(r"[A-Za-z]+\d{1,4}[!.?]?", password):
        warnings.append("Word + numbers (+ symbol) is the first pattern attackers try.")
        bits *= 0.6
    if len(password) < 12:
        suggestions.append("Use at least 12 characters - length matters most.")
    if _pool_size(password) < 60:
        suggestions.append("Mix lowercase, uppercase, digits and symbols - or use a long passphrase.")
    score = 0 if bits < 36 else 1 if bits < 50 else 2 if bits < 65 else 3 if bits < 80 else 4
    return StrengthReport(password, round(bits, 1), score, warnings, suggestions)
