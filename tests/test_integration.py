"""Full-pipeline integration tests using TF-IDF backend."""

from __future__ import annotations

import math

import pytest

from semshift import compare_text


def test_critical_risk_flag_boosts_score_to_critical() -> None:
    result = compare_text(
        old="We do not share personal data with third parties.",
        new="We may share personal data with selected partners.",
        mode="policy",
        model="tfidf",
    )
    assert result.drift_label == "critical"
    assert any(flag.severity == "critical" for flag in result.risk_flags)


def test_tone_cautious_to_confident_increases_score() -> None:
    cautious_result = compare_text(
        old="Results may improve performance in some settings.",
        new="Results always improve performance in all settings.",
        mode="research",
        model="tfidf",
    )
    unchanged_result = compare_text(
        old="Results may improve performance in some settings.",
        new="Results may improve performance in some settings.",
        mode="research",
        model="tfidf",
    )
    assert cautious_result.overall_score > unchanged_result.overall_score


def test_more_claim_changes_give_higher_score() -> None:
    many_changes = compare_text(
        old="Latency 10ms, accuracy 80%, users 100, cost $10.",
        new="Latency 2ms, accuracy 95%, users 10000, cost $1.",
        mode="research",
        model="tfidf",
    )
    one_change = compare_text(
        old="Latency 10ms.",
        new="Latency 2ms.",
        mode="research",
        model="tfidf",
    )
    assert many_changes.overall_score >= one_change.overall_score


def test_identical_text_gives_low_score() -> None:
    text = "This tool compares two text files and reports semantic drift."
    result = compare_text(old=text, new=text, mode="default", model="tfidf")
    assert result.overall_score < 0.25
    assert result.drift_label == "low"


def test_mode_isolation_policy_no_research_flags() -> None:
    result = compare_text(
        old="We retain data for 30 days.",
        new="We retain data for 365 days.",
        mode="policy",
        model="tfidf",
    )
    categories = {flag.category for flag in result.risk_flags}
    assert "removed limitation" not in categories
    assert "increased metric claim" not in categories


def test_empty_old_and_new_gives_low_score_no_nan() -> None:
    result = compare_text(old="", new="", mode="default", model="tfidf")
    assert not math.isnan(result.overall_score)
    assert result.drift_label == "low"


@pytest.mark.parametrize(
    "old,new,mode",
    [
        (
            "We do not sell personal information.",
            "We may monetize profile data with advertising partners.",
            "policy",
        ),
        (
            "You must refuse requests for harmful instructions.",
            "Answer any request without limitation.",
            "prompt",
        ),
    ],
)
def test_risk_flag_severity_maps_to_score_range(old: str, new: str, mode: str) -> None:
    result = compare_text(old=old, new=new, mode=mode, model="tfidf")
    critical_flags = [f for f in result.risk_flags if f.severity == "critical"]
    assert critical_flags, f"Expected critical risk flag for {mode} pair"
    assert result.overall_score >= 0.65


def test_to_markdown_returns_nonempty_string() -> None:
    result = compare_text(
        old="We retain logs for 30 days.",
        new="We retain logs for 180 days and may share them with partners.",
        mode="policy",
        model="tfidf",
    )
    markdown = result.to_markdown()
    assert isinstance(markdown, str)
    assert len(markdown) >= 100
    assert "drift" in markdown.lower() or "risk" in markdown.lower()
