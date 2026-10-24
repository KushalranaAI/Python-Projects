"""Statistics about a piece of English text: counts, reading time, most frequent words and readability.

Every measurement is a small pure function; `analyze` combines them into one TextReport.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
SENTENCE_END = re.compile(r"[.!?]+[\"')\]’”]*(?=\s|$)")     # closing quotes/brackets may follow the full stop
READING_WPM, SPEAKING_WPM = 238, 150
STOP_WORDS = frozenset("""a about after all also an and any are as at be because been but by can could did do does
for from had has have he her him his how i if in into is it its just me more most my no not of on one only or other our
out over she so some such than that the their them then there these they this to too up us was we were what when which
who will with would you your""".split())


def words(text: str) -> list[str]:
    return [w.lower().replace("’", "'") for w in WORD.findall(text)]


def sentences(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    count = len(SENTENCE_END.findall(stripped))
    ends_cleanly = SENTENCE_END.search(stripped[-3:]) is not None
    return count if ends_cleanly else count + 1     # a final sentence without punctuation still counts


def paragraphs(text: str) -> int:
    return len([p for p in re.split(r"\n\s*\n", text) if p.strip()])


def syllables(word: str) -> int:
    """Heuristic English syllable count: vowel groups, minus a silent final 'e', at least one."""
    word = word.lower()
    count = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and not word.endswith(("le", "ee")) and count > 1:
        count -= 1
    return max(count, 1)


def flesch_reading_ease(n_words: int, n_sentences: int, n_syllables: int) -> float:
    """206.835 − 1.015·(words/sentence) − 84.6·(syllables/word). Higher = easier; 60-70 is plain English."""
    if not n_words or not n_sentences:
        return 0.0
    return 206.835 - 1.015 * (n_words / n_sentences) - 84.6 * (n_syllables / n_words)


def ease_label(score: float) -> str:
    for threshold, label in [(90, "Very easy (age 11)"), (70, "Easy"), (60, "Plain English"), (50, "Fairly difficult"),
                             (30, "Difficult (college)")]:
        if score >= threshold:
            return label
    return "Very difficult (graduate)"


def minutes_to_text(minutes: float) -> str:
    seconds = round(minutes * 60)
    return f"{seconds} sec" if seconds < 60 else f"{seconds // 60} min {seconds % 60:02d} sec"


@dataclass(frozen=True)
class TextReport:
    characters: int
    characters_no_spaces: int
    words: int
    unique_words: int
    sentences: int
    paragraphs: int
    syllables: int
    top_words: list[tuple[str, int]]
    longest_words: list[str]
    length_histogram: dict[int, int]

    @property
    def avg_word_length(self) -> float:
        return self.characters_no_spaces / self.words if self.words else 0.0

    @property
    def avg_sentence_length(self) -> float:
        return self.words / self.sentences if self.sentences else 0.0

    @property
    def lexical_diversity(self) -> float:
        """Unique words / total words: 1.0 means no word repeats."""
        return self.unique_words / self.words if self.words else 0.0

    @property
    def reading_time(self) -> str:
        return minutes_to_text(self.words / READING_WPM)

    @property
    def speaking_time(self) -> str:
        return minutes_to_text(self.words / SPEAKING_WPM)

    @property
    def reading_ease(self) -> float:
        return round(flesch_reading_ease(self.words, self.sentences, self.syllables), 1)

    @property
    def reading_ease_label(self) -> str:
        return ease_label(self.reading_ease)


def analyze(text: str, top_n: int = 10) -> TextReport:
    tokens = words(text)
    counts = Counter(t for t in tokens if t not in STOP_WORDS and len(t) > 1)
    unique = sorted(set(tokens), key=lambda w: (-len(w), w))
    return TextReport(
        characters=len(text),
        characters_no_spaces=len(re.sub(r"\s", "", text)),
        words=len(tokens),
        unique_words=len(set(tokens)),
        sentences=sentences(text),
        paragraphs=paragraphs(text),
        syllables=sum(syllables(t) for t in tokens),
        top_words=counts.most_common(top_n),
        longest_words=unique[:5],
        length_histogram=dict(sorted(Counter(min(len(t), 12) for t in tokens).items())),
    )


SAMPLES = {
    "The Zen of Python": """Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex.
Complex is better than complicated. Flat is better than nested. Sparse is better than dense. Readability counts.
Special cases aren't special enough to break the rules. Although practicality beats purity.
Errors should never pass silently. Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess. There should be one - and preferably only one - obvious way to do it.
Although that way may not be obvious at first unless you're Dutch. Now is better than never.
Although never is often better than right now. If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea. Namespaces are one honking great idea - let's do more of those!""",
    "Alice in Wonderland (opening)": """Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, "and what is the use of a book," thought Alice "without pictures or conversations?"

So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.""",
}
