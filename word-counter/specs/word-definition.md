# Word Definition

Defines what counts as a "word" for the word counter.

## Rules
- A word is a sequence of alphanumeric characters (letters and digits)
- Punctuation is stripped: "hello," and "hello" are the same word
- Hyphens split words: "well-known" becomes "well" and "known"
- Apostrophes are kept within words: "don't" is one word
- Numbers are words: "42" counts as a word
- Unicode letters are supported: "cafe" and non-ASCII characters are valid words
