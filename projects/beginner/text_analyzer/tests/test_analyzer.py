import pytest

from projects.beginner.text_analyzer.analyzer import (analyze, ease_label, flesch_reading_ease, minutes_to_text, paragraphs,
                                                      sentences, syllables, words)


def test_words_keep_apostrophes_and_ignore_punctuation():
    assert words("It's a dog's life - isn't it? 42!") == ["it's", "a", "dog's", "life", "isn't", "it"]


@pytest.mark.parametrize("text, n", [("", 0), ("One. Two! Three?", 3), ("No full stop", 1), ("Wait... what?!", 2), ("3.14 is pi.", 1), ('He said "Hi." Then left', 2), ('"Why?" she asked.', 2)])
def test_sentences(text, n):
    assert sentences(text) == n


def test_paragraphs():
    assert paragraphs("a\n\nb\n   \nc") == 3


@pytest.mark.parametrize("word, n", [("cat", 1), ("table", 2), ("beautiful", 3), ("readability", 5), ("make", 1), ("rhythm", 1)])
def test_syllables(word, n):
    assert syllables(word) == n


def test_flesch_and_labels():
    assert flesch_reading_ease(100, 10, 130) == pytest.approx(206.835 - 10.15 - 109.98)
    assert flesch_reading_ease(0, 0, 0) == 0
    assert ease_label(95).startswith("Very easy") and ease_label(10).startswith("Very difficult")


def test_minutes_to_text():
    assert minutes_to_text(0.5) == "30 sec" and minutes_to_text(2.25) == "2 min 15 sec"


def test_report():
    r = analyze("The cat sat. The cat ran! A dog barked loudly.")
    assert (r.words, r.unique_words, r.sentences) == (10, 8, 3)
    assert r.top_words[0] == ("cat", 2)
    assert r.longest_words[:2] == ["barked", "loudly"]     # equal length → alphabetical
    assert r.lexical_diversity == pytest.approx(0.8)
    assert sum(r.length_histogram.values()) == r.words


def test_empty_text():
    r = analyze("")
    assert r.words == 0 and r.reading_ease == 0 and r.avg_word_length == 0
