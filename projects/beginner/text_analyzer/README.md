---
title: Text Analyzer
order: 9
icon: 📊
time: 2 hours
summary: Paste any text and get word counts, reading time, the most frequent words, a word-length histogram and a readability score. Practise text processing with regex and Counter.
python_skills:
  - Regular expressions (findall, split, lookahead)
  - collections.Counter for frequencies
  - Sets for unique values, frozenset for constants
  - Reading files from command-line arguments (sys.argv)
oop_concepts:
  - A report dataclass with derived @property values
  - Module-level pure functions composed by one entry point
  - Immutable result objects (frozen=True)
clean_code:
  - One small function per measurement, each easy to test
  - Named constants (READING_WPM) instead of magic numbers
  - Formulas with a docstring that cites them
  - Guard against division by zero (empty text) in one place
features:
  - Words, unique words, sentences, paragraphs, characters
  - Reading and speaking time
  - Top words without stop words, longest words
  - Word-length histogram and Flesch reading-ease score
architecture: |
  classDiagram
    class TextReport {
      <<frozen dataclass>>
      +characters int
      +words int
      +unique_words int
      +sentences int
      +paragraphs int
      +syllables int
      +top_words list
      +longest_words list
      +length_histogram dict
      +avg_word_length float
      +lexical_diversity float
      +reading_time str
      +reading_ease float
      +reading_ease_label str
    }
    class analyzer {
      <<module>>
      +words(text) list
      +sentences(text) int
      +paragraphs(text) int
      +syllables(word) int
      +flesch_reading_ease(w, s, syl) float
      +analyze(text) TextReport
    }
    analyzer ..> TextReport : builds
flow: |
  flowchart LR
    T[text] --> W["words() regex"]
    T --> S["sentences()"]
    T --> P["paragraphs()"]
    W --> C[Counter → top words]
    W --> Y["syllables() per word"]
    W & S & Y --> F["Flesch score"]
    C & F --> R[TextReport]
steps:
  - title: Decide what a "word" is
    files: [analyzer.py]
    body: |
      `text.split()` thinks "dog's," and "life -" are words. A regex is precise: `[A-Za-z]+(?:['’][A-Za-z]+)*` means
      letters, optionally followed by an apostrophe and more letters. Write the definition once and test it with a tricky sentence.
  - title: One function per measurement
    files: [analyzer.py, tests/test_analyzer.py]
    body: |
      `sentences`, `paragraphs`, `syllables`, `flesch_reading_ease`: each takes simple input, returns a number and is
      tested on its own. Small functions are easier to name, test and reuse than one 80-line function.
  - title: Count with Counter
    files: [analyzer.py]
    body: |
      `Counter(words).most_common(10)` replaces a manual dict-and-sort loop. Stop words ("the", "and") are filtered
      with a `frozenset`, since set membership is O(1).
  - title: Collect results in a report object
    files: [analyzer.py]
    body: |
      `analyze()` computes the raw numbers once and returns a frozen `TextReport`. Averages, times and labels are
      properties derived from those numbers, so the empty-text case (division by zero) is handled in one place each.
  - title: Two interfaces
    files: [cli.py, web.py, templates/text_analyzer/index.html]
    body: |
      The CLI reads a file passed on the command line or pasted text. The web view caps input at 200,000 characters.
      **Always bound user input**: a 2 GB paste shouldn't take down your server. Bars and the histogram are plain HTML/CSS
      widths computed from the report.
exercises:
  - 'Add **n-grams**: the most frequent two-word phrases.'
  - Compare two texts side by side and highlight which words are distinctive for each (hint - ratios of frequencies).
  - Detect the **language** of a text by comparing stop-word frequencies for English, Spanish and German.
  - Add **sentiment** with a small positive/negative word list. What goes wrong with "not good"?
---

## The Flesch reading-ease formula

`206.835 − 1.015 × (words per sentence) − 84.6 × (syllables per word)`

Long sentences and long words make text harder. The Zen of Python scores about 62 ("plain English"); the opening of
*Alice in Wonderland* scores about 33 ("difficult"): Lewis Carroll packs it into two sentences of more than 50 words each. It's a rough heuristic: it doesn't know what the words *mean*, and our syllable counter is itself a
heuristic, which the tests pin down for common cases.
