from semshift import compare_text


def test_policy_semantic_drift_flags_risk() -> None:
    result = compare_text(
        old="We do not share personal data. We retain logs for 30 days.",
        new="We may share personal data with selected partners. We retain logs for 180 days.",
        mode="policy",
        model="tfidf",
    )

    assert result.drift_label in {"high", "critical"}
    assert result.scores.risk_shift >= 0.75
    assert any(flag.category == "third-party sharing" for flag in result.risk_flags)
    assert result.claim_changes.modified_numbers


def test_added_and_removed_chunks_are_classified() -> None:
    result = compare_text(
        old="Stable introduction.\n\nThis paragraph will be removed.",
        new="Stable introduction.\n\nThis paragraph is newly added.",
        model="tfidf",
    )

    statuses = {match.status for match in result.chunk_matches}

    assert "removed" in statuses or "semantically changed" in statuses
    assert "added" in statuses or "semantically changed" in statuses


def test_low_drift_for_same_text() -> None:
    result = compare_text(
        old="The tool may produce approximate matches.",
        new="The tool may produce approximate matches.",
        model="tfidf",
    )

    assert result.overall_score < 0.2
    assert result.drift_label == "low"

