"""Tests for text utility helpers."""

from semshift.utils.text import (
    normalize_whitespace,
    quote,
    split_sentences,
    token_overlap,
    token_set,
    truncate,
)


class TestNormalizeWhitespace:
    def test_collapses_multiple_spaces(self):
        assert normalize_whitespace("foo  bar") == "foo bar"

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_whitespace("  hello  ") == "hello"

    def test_collapses_tabs_and_newlines(self):
        assert normalize_whitespace("foo\t\nbar") == "foo bar"

    def test_empty_string_returns_empty(self):
        assert normalize_whitespace("") == ""

    def test_already_clean_string_unchanged(self):
        assert normalize_whitespace("hello world") == "hello world"


class TestSplitSentences:
    def test_splits_on_period_followed_by_uppercase(self):
        sentences = split_sentences("First claim. Second claim.")
        assert len(sentences) == 2
        assert sentences[0] == "First claim."
        assert sentences[1] == "Second claim."

    def test_does_not_split_on_period_without_uppercase(self):
        sentences = split_sentences("e.g. this does not split")
        assert len(sentences) == 1

    def test_empty_string_returns_empty_list(self):
        assert split_sentences("") == []

    def test_single_sentence_returned_as_list(self):
        result = split_sentences("Only one sentence here.")
        assert result == ["Only one sentence here."]

    def test_normalizes_internal_whitespace(self):
        result = split_sentences("  First  sentence.  Second sentence.  ")
        assert len(result) == 2

    def test_splits_on_question_and_exclamation(self):
        result = split_sentences("Is this right? Yes it is! Good.")
        assert len(result) == 3


class TestTokenSet:
    def test_returns_lowercase_tokens(self):
        tokens = token_set("Hello World")
        assert "hello" in tokens
        assert "world" in tokens
        assert "Hello" not in tokens

    def test_ignores_punctuation_and_numbers(self):
        tokens = token_set("foo, bar.")
        assert "foo" in tokens
        assert "bar" in tokens
        assert "," not in tokens

    def test_empty_string_returns_empty_set(self):
        assert token_set("") == set()

    def test_deduplicates_repeated_words(self):
        tokens = token_set("hello hello world")
        assert tokens == {"hello", "world"}


class TestTokenOverlap:
    def test_identical_texts_score_is_one(self):
        score = token_overlap("the cat sat", "the cat sat")
        assert abs(score - 1.0) < 1e-9

    def test_no_overlap_score_is_zero(self):
        score = token_overlap("foo bar", "baz qux")
        assert score == 0.0

    def test_partial_overlap_is_between_zero_and_one(self):
        score = token_overlap("foo bar baz", "foo baz qux")
        assert 0.0 < score < 1.0

    def test_empty_left_returns_zero(self):
        assert token_overlap("", "something") == 0.0

    def test_empty_right_returns_zero(self):
        assert token_overlap("something", "") == 0.0

    def test_empty_both_returns_zero(self):
        assert token_overlap("", "") == 0.0


class TestTruncate:
    def test_short_text_unchanged(self):
        assert truncate("hello", max_chars=100) == "hello"

    def test_long_text_truncated_with_ellipsis(self):
        result = truncate("a" * 300, max_chars=50)
        assert result.endswith("...")
        assert len(result) <= 50

    def test_exactly_at_limit_not_truncated(self):
        text = "a" * 100
        assert truncate(text, max_chars=100) == text

    def test_normalizes_whitespace_before_truncating(self):
        result = truncate("  foo   bar  ", max_chars=100)
        assert result == "foo bar"

    def test_empty_string(self):
        assert truncate("") == ""


class TestQuote:
    def test_adds_quotes_around_text(self):
        result = quote("hello world")
        assert result == '"hello world"'

    def test_truncates_long_text_within_quotes(self):
        result = quote("a" * 300, max_chars=50)
        assert result.startswith('"')
        assert result.endswith('"')
        assert "..." in result

    def test_empty_string_quoted(self):
        result = quote("")
        assert result == '""'
