"""Tests for semantic diff orchestration."""

import pytest

from semshift import compare_text
from semshift.core.loader import FileLoadError
from semshift.core.semantic_diff import (
    ChunkMatch,
    chunk_new_text,
    chunk_old_text,
    chunk_section,
    compact_change_title,
    compare_files,
    top_meaning_changes,
)


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


def test_compare_files_end_to_end(tmp_path) -> None:
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text("We do not share personal data.", encoding="utf-8")
    new.write_text("We may share personal data with partners.", encoding="utf-8")

    result = compare_files(old, new, mode="policy", model="tfidf")

    assert result.old_label == str(old)
    assert result.new_label == str(new)
    assert result.mode == "policy"
    assert result.drift_label in {"medium", "high", "critical"}


def test_compare_files_missing_file_raises(tmp_path) -> None:
    with pytest.raises(FileLoadError, match="File not found"):
        compare_files(tmp_path / "missing.md", tmp_path / "also_missing.md")


def test_compare_files_unsupported_extension_raises(tmp_path) -> None:
    f = tmp_path / "file.exe"
    f.write_bytes(b"data")
    with pytest.raises(FileLoadError, match="Unsupported file extension"):
        compare_files(f, f)


def test_empty_old_text_produces_warning() -> None:
    result = compare_text(old="", new="Some new content.", model="tfidf")
    assert any("empty" in w.lower() for w in result.warnings)


def test_empty_new_text_produces_warning() -> None:
    result = compare_text(old="Some old content.", new="", model="tfidf")
    assert any("empty" in w.lower() for w in result.warnings)


def test_both_empty_texts_produce_warnings() -> None:
    result = compare_text(old="", new="", model="tfidf")
    assert len(result.warnings) >= 2


def test_result_overall_score_is_between_zero_and_one() -> None:
    result = compare_text(old="old content", new="new content", model="tfidf")
    assert 0.0 <= result.overall_score <= 1.0


def test_result_overall_score_equals_scores_overall_semantic_drift() -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    assert result.overall_score == result.scores.overall_semantic_drift


def test_result_drift_label_consistent_with_score() -> None:
    result = compare_text(
        old="We do not share personal data.",
        new="We may share personal data with selected partners.",
        mode="policy",
        model="tfidf",
    )
    from semshift.utils.scoring import drift_label

    assert result.drift_label == drift_label(result.overall_score)


def test_result_to_dict_has_required_keys() -> None:
    result = compare_text(old="old text", new="new text", model="tfidf")
    d = result.to_dict()
    expected = {
        "files",
        "mode",
        "scores",
        "overall_score",
        "drift_score",
        "drift_label",
        "summary",
        "chunk_matches",
        "matched_chunks",
        "claim_changes",
        "tone_shift",
        "risk_flags",
        "recommendations",
        "embedding_backend",
        "embedding_backend_type",
        "warnings",
        "metadata",
    }
    assert expected.issubset(set(d.keys()))


def test_result_to_dict_files_has_old_and_new() -> None:
    result = compare_text(old="a", new="b", old_label="old.md", new_label="new.md", model="tfidf")
    d = result.to_dict()
    assert d["files"]["old"] == "old.md"
    assert d["files"]["new"] == "new.md"


def test_result_scores_to_dict_all_floats() -> None:
    result = compare_text(old="a", new="b", model="tfidf")
    for value in result.scores.to_dict().values():
        assert isinstance(value, float)


def test_result_summary_is_list_of_strings() -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    assert isinstance(result.summary, list)
    assert all(isinstance(item, str) for item in result.summary)


def test_result_recommendations_is_list_of_strings() -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    assert isinstance(result.recommendations, list)
    assert all(isinstance(r, str) for r in result.recommendations)


def test_result_embedding_backend_is_tfidf() -> None:
    result = compare_text(old="hello", new="world", model="tfidf")
    assert result.embedding_backend == "tfidf"


def test_top_meaning_changes_returns_highest_drift_first() -> None:
    result = compare_text(
        old="Para one.\n\nPara two.\n\nPara three.",
        new="Completely different.\n\nAlso new.\n\nYet another.",
        model="tfidf",
    )
    changes = top_meaning_changes(result, limit=3)
    drifts = [m.drift_score for m in changes]
    assert drifts == sorted(drifts, reverse=True)


def test_top_meaning_changes_excludes_unchanged() -> None:
    result = compare_text(
        old="Same intro.\n\nDifferent section content here.",
        new="Same intro.\n\nCompletely changed section content.",
        model="tfidf",
    )
    changes = top_meaning_changes(result)
    assert all(m.status != "unchanged" for m in changes)


def test_top_meaning_changes_respects_limit() -> None:
    result = compare_text(
        old="A.\n\nB.\n\nC.\n\nD.\n\nE.",
        new="X.\n\nY.\n\nZ.\n\nW.\n\nV.",
        model="tfidf",
    )
    assert len(top_meaning_changes(result, limit=2)) <= 2


def test_chunk_section_uses_heading_when_available() -> None:
    from semshift.core.chunker import TextChunk

    chunk = TextChunk(id="chunk-001", text="text", heading="My Section", start_line=1, end_line=2)
    match = ChunkMatch(
        status="semantically changed", similarity=0.5, drift_score=0.7, old_chunk=chunk
    )
    assert chunk_section(match) == "My Section"


def test_chunk_section_falls_back_to_line_range() -> None:
    from semshift.core.chunker import TextChunk

    chunk = TextChunk(id="chunk-001", text="text", heading=None, start_line=5, end_line=8)
    match = ChunkMatch(status="added", similarity=0.0, drift_score=0.75, new_chunk=chunk)
    assert "5" in chunk_section(match)
    assert "8" in chunk_section(match)


def test_chunk_section_returns_unknown_when_no_chunk() -> None:
    match = ChunkMatch(status="removed", similarity=0.0, drift_score=0.75)
    assert chunk_section(match) == "Unknown"


def test_chunk_old_text_returns_added_placeholder_when_no_old() -> None:
    from semshift.core.chunker import TextChunk

    chunk = TextChunk(id="chunk-001", text="new text", heading=None, start_line=1, end_line=1)
    match = ChunkMatch(status="added", similarity=0.0, drift_score=0.75, new_chunk=chunk)
    assert "[added]" in chunk_old_text(match)


def test_chunk_new_text_returns_removed_placeholder_when_no_new() -> None:
    from semshift.core.chunker import TextChunk

    chunk = TextChunk(id="chunk-001", text="old text", heading=None, start_line=1, end_line=1)
    match = ChunkMatch(status="removed", similarity=0.0, drift_score=0.75, old_chunk=chunk)
    assert "[removed]" in chunk_new_text(match)


def test_compact_change_title_format() -> None:
    from semshift.core.chunker import TextChunk

    chunk = TextChunk(id="chunk-001", text="text", heading="Section", start_line=1, end_line=2)
    match = ChunkMatch(
        status="semantically changed", similarity=0.4, drift_score=0.65, old_chunk=chunk
    )
    title = compact_change_title(match)
    assert "Section" in title
    assert "SEMANTICALLY CHANGED" in title
    assert "0.65" in title


def test_chunk_match_to_dict_has_required_keys() -> None:
    from semshift.core.chunker import TextChunk

    chunk = TextChunk(id="chunk-001", text="text", heading=None, start_line=1, end_line=1)
    match = ChunkMatch(status="added", similarity=0.0, drift_score=0.75, new_chunk=chunk)
    d = match.to_dict()
    assert set(d.keys()) == {
        "status",
        "similarity",
        "drift_score",
        "old_chunk",
        "new_chunk",
        "why_it_matters",
    }


def test_invalid_mode_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown mode"):
        compare_text(old="a", new="b", mode="invalid_mode")


def test_default_labels_are_old_text_and_new_text() -> None:
    result = compare_text(old="a", new="b")
    assert result.old_label == "old text"
    assert result.new_label == "new text"


def test_custom_labels_set_correctly() -> None:
    result = compare_text(old="a", new="b", old_label="base.md", new_label="head.md")
    assert result.old_label == "base.md"
    assert result.new_label == "head.md"
