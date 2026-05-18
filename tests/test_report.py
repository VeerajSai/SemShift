"""Tests for Rich, JSON, and markdown reporting."""

import io
import json

from rich.console import Console

from semshift import compare_text
from semshift.core.report import (
    markdown_report,
    print_rich_report,
    result_to_json,
    write_markdown_report,
)


def test_markdown_report_contains_score_breakdown_and_risk_flags(tmp_path) -> None:
    result = compare_text(
        old="We do not share personal data. We retain logs for 30 days.",
        new="We may share personal data with partners. We retain logs for 180 days.",
        mode="policy",
        model="tfidf",
    )
    report = markdown_report(result)

    assert "## Score Breakdown" in report
    assert "## Risk Flags" in report
    assert "third-party sharing" in report

    nested_path = tmp_path / "reports" / "semshift.md"
    write_markdown_report(result, nested_path)
    assert nested_path.exists()


def test_result_to_json_is_valid_json() -> None:
    result = compare_text(old="old text", new="new text", model="tfidf")
    payload = json.loads(result_to_json(result))
    assert isinstance(payload, dict)


def test_result_to_json_has_all_required_keys() -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    payload = json.loads(result_to_json(result))
    required = {
        "files", "mode", "scores", "drift_label", "summary",
        "chunk_matches", "claim_changes", "tone_shift", "risk_flags",
        "recommendations", "embedding_backend", "warnings",
    }
    assert required.issubset(set(payload.keys()))


def test_result_to_json_drift_label_is_string() -> None:
    result = compare_text(old="a", new="b", model="tfidf")
    payload = json.loads(result_to_json(result))
    assert isinstance(payload["drift_label"], str)
    assert payload["drift_label"] in {"low", "medium", "high", "critical"}


def test_print_rich_report_does_not_raise() -> None:
    result = compare_text(
        old="We do not share personal data.",
        new="We may share personal data with partners.",
        mode="policy",
        model="tfidf",
    )
    console = Console(file=io.StringIO())
    print_rich_report(result, console=console)


def test_print_rich_report_with_no_changes_does_not_raise() -> None:
    result = compare_text(old="same text", new="same text", model="tfidf")
    console = Console(file=io.StringIO())
    print_rich_report(result, console=console)


def test_markdown_report_header_correct() -> None:
    result = compare_text(old="a", new="b", old_label="old.md", new_label="new.md", model="tfidf")
    report = markdown_report(result)
    assert "# SemShift Report" in report
    assert "old.md" in report
    assert "new.md" in report


def test_markdown_report_includes_summary() -> None:
    result = compare_text(old="old text", new="new text", model="tfidf")
    report = markdown_report(result)
    assert "## Summary" in report


def test_markdown_report_top_meaning_changes_present_when_drift() -> None:
    result = compare_text(
        old="We do not share data.",
        new="We sell data to third parties.",
        mode="policy",
        model="tfidf",
    )
    report = markdown_report(result, top=3)
    assert "## Top Meaning Changes" in report


def test_markdown_report_no_top_changes_section_when_unchanged() -> None:
    result = compare_text(old="same text", new="same text", model="tfidf")
    report = markdown_report(result)
    assert "## Top Meaning Changes" not in report


def test_write_markdown_report_creates_nested_directories(tmp_path) -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    out = tmp_path / "deep" / "nested" / "report.md"
    write_markdown_report(result, out)
    assert out.exists()


def test_write_markdown_report_returns_path(tmp_path) -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    out = tmp_path / "report.md"
    returned = write_markdown_report(result, out)
    assert returned == out


def test_markdown_report_includes_recommendations() -> None:
    result = compare_text(old="old", new="new", model="tfidf")
    report = markdown_report(result)
    assert "## Recommended Next Steps" in report


def test_markdown_report_includes_warnings_when_present() -> None:
    result = compare_text(old="", new="new content", model="tfidf")
    report = markdown_report(result)
    if result.warnings:
        assert "## Warnings" in report


def test_markdown_report_respects_top_limit() -> None:
    result = compare_text(
        old="A.\n\nB.\n\nC.\n\nD.\n\nE.\n\nF.",
        new="X.\n\nY.\n\nZ.\n\nW.\n\nV.\n\nU.",
        model="tfidf",
    )
    report_top2 = markdown_report(result, top=2)
    report_top5 = markdown_report(result, top=5)
    count2 = report_top2.count("### ")
    count5 = report_top5.count("### ")
    assert count2 <= count5


def test_result_to_json_score_is_float() -> None:
    result = compare_text(old="a", new="b", model="tfidf")
    payload = json.loads(result_to_json(result))
    assert isinstance(payload["scores"]["overall_semantic_drift"], float)
