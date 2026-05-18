from semshift import compare_text
from semshift.integrations.github_action import (
    _combined_markdown,
    _pr_comment_body,
    _resolve_files,
)


def test_action_resolves_globbed_supported_files(tmp_path, monkeypatch) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "privacy.md").write_text("privacy", encoding="utf-8")
    (tmp_path / "docs" / "image.png").write_text("not supported", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _resolve_files("docs/*", "main") == ["docs/privacy.md"]


def test_action_combined_markdown_has_summary_table() -> None:
    result = compare_text(
        old="The model may fail.",
        new="The model is guaranteed accurate.",
        model="tfidf",
        old_label="base:README.md",
        new_label="README.md",
    )

    report = _combined_markdown([result])

    assert "| File | Score | Label | Risk flags | Changed claims |" in report
    assert "`README.md`" in report
    assert "## File Report" in report


def test_action_pr_comment_body_has_marker_and_summary() -> None:
    result = compare_text(
        old="We do not share personal data.",
        new="We may share personal data with selected partners.",
        mode="policy",
        model="tfidf",
        new_label="docs/privacy.md",
    )

    body = _pr_comment_body([result], "semshift-report.md")

    assert "<!-- semshift-report -->" in body
    assert "SemShift semantic review" in body
    assert "`docs/privacy.md`" in body
