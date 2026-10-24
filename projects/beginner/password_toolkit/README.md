---
title: Password Toolkit
order: 4
icon: 🔐
time: 2 hours
summary: Generate secure passwords and passphrases, and estimate a password's strength with entropy and pattern checks. A first look at writing security-sensitive code.
python_skills:
  - The secrets module (and why random isn't safe)
  - String constants and set operations
  - Regular expressions for pattern detection
  - math.log2 and a little information theory
  - getpass for hidden terminal input
oop_concepts:
  - A policy object (frozen dataclass) that validates itself
  - Dependency injection (the random generator is a constructor parameter)
  - "@staticmethod and class-level constants"
  - A report object with computed properties
clean_code:
  - Security defaults - safe by default, opt-in to weaker choices
  - Name your magic numbers (score thresholds, guess rate)
  - Small single-purpose functions (`_pool_size`, `check_strength`)
  - Never put secrets in URLs or logs (POST, not GET)
features:
  - Password generator with length and character-class options
  - Guarantees at least one character of every chosen class
  - Passphrase generator ("Moon-Lake-Fork-Gold-Rush")
  - Strength meter with entropy, estimated crack time, warnings and tips
architecture: |
  classDiagram
    class PasswordPolicy {
      <<frozen dataclass>>
      +length int
      +lowercase bool
      +uppercase bool
      +digits bool
      +symbols bool
      +exclude_ambiguous bool
      +character_classes() list~str~
      +validate()
      +pool_size int
      +entropy_bits float
    }
    class PasswordGenerator {
      -rng SystemRandom
      +password(policy) str
      +passphrase(words, separator) str
      +passphrase_entropy(words)$ float
    }
    class StrengthReport {
      +password str
      +entropy_bits float
      +score int
      +warnings list
      +suggestions list
      +label str
      +crack_time str
    }
    PasswordGenerator ..> PasswordPolicy : uses
    check_strength ..> StrengthReport : creates
flow: |
  flowchart LR
    P[password] --> E["entropy = length × log2(pool)"]
    E --> C{common? repeats?<br/>sequences? word+digits?}
    C -->|penalties| B[adjusted bits]
    B --> S["score 0-4<br/>+ crack time"]
steps:
  - title: Learn why `random` is not for secrets
    body: |
      `random` uses the Mersenne Twister. It's fast and fine for games, but after seeing 624 outputs an attacker
      can predict every future one. `secrets.SystemRandom` uses the operating system's cryptographic
      generator. Rule: **anything that protects something uses `secrets`.**
  - title: Describe the options as a policy object
    files: [toolkit.py]
    body: |
      Instead of a function with six boolean parameters, `PasswordPolicy` groups them in a frozen dataclass with
      safe defaults (16 characters, all classes). It knows its own rules: `validate()` and the computed
      `pool_size` and `entropy_bits`.
  - title: Generate with a guarantee
    files: [toolkit.py]
    body: |
      Picking 16 random characters from the pool can, by chance, contain no digit. So we first take one character from
      **each** class, fill up from the full pool, then `shuffle` so the guaranteed characters aren't always at the start.
  - title: Inject the generator for testing
    files: [toolkit.py, tests/test_toolkit.py]
    body: |
      `PasswordGenerator(rng=None)` defaults to `secrets.SystemRandom()`, but tests pass `random.Random(42)`.
      `random.Random` has the same `choice`/`shuffle` methods, which is *duck typing*.
  - title: Measure strength with entropy, then penalise patterns
    files: [toolkit.py]
    body: |
      Entropy = length × log2(pool size): 16 characters from 94 symbols ≈ 105 bits. But humans don't pick
      randomly. `check_strength` cuts the estimate for common passwords, repeats, keyboard sequences and the
      *Word + 1234 + !* pattern. Each check is one readable `if`, with its message next to it.
  - title: Present results as a report object
    files: [toolkit.py]
    body: |
      `StrengthReport` holds the numbers and computes `label` and `crack_time` as properties. The CLI and the web
      template just read them. Thresholds live in one place.
  - title: Handle secrets carefully in the interfaces
    files: [cli.py, web.py]
    body: |
      The CLI reads with `getpass` so the password isn't echoed. The web form uses **POST** so it never appears in the
      URL, browser history or server logs, and nothing is stored.
exercises:
  - Replace the 400-word list with the **EFF large wordlist** (7,776 words). How many bits does a 6-word passphrase have now?
  - Check passwords against the **Have I Been Pwned** range API using k-anonymity (send only the first 5 SHA-1 characters).
  - Add a **"pronounceable"** generator that alternates consonants and vowels. What does it cost in entropy?
  - Detect **leetspeak** words (`p@ssw0rd`) by normalising characters before the common-password check.
---

## Entropy in one table

| Password style | Pool | Length | Bits | Time to crack at 10¹⁰/s |
|---|---|---|---|---|
| lowercase word | 26 | 8 | 38 | ~12 seconds |
| mixed + digits + symbols | 94 | 8 | 52 | ~2 days |
| mixed + digits + symbols | 94 | 16 | 105 | longer than the universe has existed |
| 5 words from 7,776 | 7,776 | 5 words | 65 | ~1,000 years |

This estimator is deliberately simple. It can't know that `Tr0ub4dor&3` is just "troubadour" with substitutions,
so it overrates that one. Real estimators such as Dropbox's *zxcvbn* also check large dictionaries; adding one is an exercise.

**Length beats complexity.** A long passphrase is both stronger and easier to remember than `P@ssw0rd!`.
