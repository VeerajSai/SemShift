from semshift import compare_text
from semshift.integrations.github_action import (
    _combined_markdown,
    _normalize_repo_path,
    _pr_comment_body,
    _resolve_files,
    _truncate_comment_body,
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


def test_action_rejects_parent_traversal(tmp_path, monkeypatch) -> None:
    (tmp_path / "safe.md").write_text("safe", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _resolve_files("../secret.md, safe.md", "main") == ["safe.md"]
    assert _normalize_repo_path("../secret.md", tmp_path) is None


def test_action_rejects_absolute_paths(tmp_path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")

    assert _normalize_repo_path(str(outside.resolve()), tmp_path) is None


def test_action_comment_body_escapes_html() -> None:
    result = compare_text(
        old="Old text",
        new="<script>alert(1)</script>",
        model="tfidf",
        new_label="docs/<script>.md",
    )

    body = _pr_comment_body([result], "semshift-report.md")

    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_action_comment_body_truncates() -> None:
    body = _truncate_comment_body("a" * 200, max_length=140)

    assert len(body) <= 140
    assert "Report truncated" in body
