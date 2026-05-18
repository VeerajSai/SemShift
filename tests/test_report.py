from semshift import compare_text
from semshift.core.report import markdown_report, write_markdown_report


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

