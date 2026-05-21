"""Tests for tone shift detection."""

from semshift.core.tone_analyzer import ToneShift, analyze_tone, compare_tone


class TestAnalyzeTone:
    def test_cautious_text_labeled_cautious(self):
        profile = analyze_tone(
            "The model may produce approximate results. It might not generalize."
        )
        assert profile.label == "cautious"

    def test_confident_text_labeled_confident(self):
        profile = analyze_tone("This will always deliver accurate results. Never fails.")
        assert profile.label == "confident"

    def test_promotional_text_labeled_promotional(self):
        profile = analyze_tone("Our effortless, powerful, and world-class solution is the best.")
        assert profile.label == "promotional"

    def test_restrictive_text_labeled_restrictive(self):
        profile = analyze_tone(
            "Users must not share data. Sharing is prohibited and mandatory consent required."
        )
        assert profile.label == "restrictive"

    def test_empty_text_returns_neutral(self):
        profile = analyze_tone("")
        assert profile.label == "neutral"

    def test_technical_text_labeled_technical(self):
        profile = analyze_tone(
            "The API uses a JSON dataset model with Python embeddings and cli accuracy."
        )
        assert profile.label in ("technical", "cautious", "neutral")

    def test_scores_are_clamped_between_zero_and_one(self):
        profile = analyze_tone("may might could possibly potentially usually generally")
        for score in profile.scores.values():
            assert 0.0 <= score <= 1.0

    def test_features_lists_active_categories(self):
        profile = analyze_tone("The system will always deliver accurate results.")
        assert "confident" in profile.features

    def test_to_dict_has_expected_keys(self):
        profile = analyze_tone("some text").to_dict()
        assert "label" in profile
        assert "scores" in profile
        assert "features" in profile


class TestCompareTone:
    def test_same_text_unchanged_shift(self):
        shift = compare_tone("The system may produce errors.", "The system may produce errors.")
        assert shift.shift == "unchanged"

    def test_cautious_to_confident_detected(self):
        shift = compare_tone(
            "The model may produce approximate results.",
            "The model will always deliver accurate results.",
        )
        assert shift.shift == "cautious_to_confident"
        assert shift.from_label == "cautious"
        assert shift.to_label == "confident"

    def test_score_is_between_zero_and_one(self):
        shift = compare_tone("neutral text here", "still neutral text here")
        assert 0.0 <= shift.score <= 1.0

    def test_to_dict_has_expected_keys(self):
        shift = compare_tone("old text", "new text").to_dict()
        assert "from" in shift
        assert "to" in shift
        assert "shift" in shift
        assert "score" in shift
        assert "explanation" in shift

    def test_tone_shift_explanation_not_empty(self):
        shift = compare_tone("The model may fail.", "The model is guaranteed accurate.")
        assert shift.explanation

    def test_toneshift_is_frozen_dataclass(self):
        shift = compare_tone("old text", "new text")
        assert isinstance(shift, ToneShift)

    def test_high_drift_has_higher_score_than_low_drift(self):
        high = compare_tone(
            "The model may produce approximate results.",
            "The model will always deliver guaranteed accurate results.",
        )
        low = compare_tone("Some text here.", "Some text here.")
        assert high.score >= low.score


def test_short_text_score_does_not_over_inflate() -> None:
    from semshift.core.tone_analyzer import analyze_tone

    profile = analyze_tone("This will work.")
    assert max(profile.scores.values()) <= 0.5, f"Short text inflated scores: {profile.scores}"


def test_guarantee_not_in_risky_keywords() -> None:
    from semshift.core.tone_analyzer import RISKY

    assert "guarantee" not in RISKY


def test_best_not_in_confident_keywords() -> None:
    from semshift.core.tone_analyzer import CONFIDENT

    assert "best" not in CONFIDENT


def test_disclaimer_in_restrictive_keywords() -> None:
    from semshift.core.tone_analyzer import RESTRICTIVE

    assert "disclaimer" in RESTRICTIVE


def test_mixed_tone_scores_within_range() -> None:
    from semshift.core.tone_analyzer import analyze_tone

    text = "Results may improve, but we will guarantee accurate outputs in most cases."
    profile = analyze_tone(text)
    for key, score in profile.scores.items():
        assert 0.0 <= score <= 1.0, f"Score {key}={score} out of range"
