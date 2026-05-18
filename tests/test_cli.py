import json
from inspect import signature

from typer.testing import CliRunner

from semshift.cli import app


def _cli_runner() -> CliRunner:
    kwargs = {}
    if "mix_stderr" in signature(CliRunner).parameters:
        kwargs["mix_stderr"] = False
    return CliRunner(**kwargs)


runner = _cli_runner()


def test_cli_compare_json(tmp_path) -> None:
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text("We do not share personal data.", encoding="utf-8")
    new.write_text("We may share personal data with partners.", encoding="utf-8")

    result = runner.invoke(
        app,
        ["compare", str(old), str(new), "--mode", "policy", "--model", "tfidf", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "policy"
    assert payload["drift_label"] in {"high", "critical"}


def test_cli_compare_text_writes_report(tmp_path) -> None:
    report = tmp_path / "report.md"

    result = runner.invoke(
        app,
        [
            "compare-text",
            "The model may be wrong.",
            "The model is guaranteed accurate.",
            "--model",
            "tfidf",
            "--report",
            str(report),
        ],
    )

    assert result.exit_code == 0
    assert report.exists()
    assert "SemShift Report" in report.read_text(encoding="utf-8")


def test_cli_fail_on_prints_clear_reason() -> None:
    result = runner.invoke(
        app,
        [
            "compare-text",
            "We do not share data.",
            "We may share data with partners.",
            "--mode",
            "policy",
            "--model",
            "tfidf",
            "--fail-on",
            "high",
            "--json",
        ],
    )

    assert result.exit_code == 1
    assert "meets --fail-on" in result.stderr


def test_cli_missing_file_error_is_human_readable(tmp_path) -> None:
    missing = tmp_path / "missing.md"
    new = tmp_path / "new.md"
    new.write_text("hello", encoding="utf-8")

    result = runner.invoke(app, ["compare", str(missing), str(new), "--model", "tfidf"])

    assert result.exit_code == 2
    assert "SemShift error: File not found" in result.stderr
