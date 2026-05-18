"""Tests for the CLI interface."""

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


def test_cli_modes_command_lists_all_six_modes() -> None:
    result = runner.invoke(app, ["modes"])
    assert result.exit_code == 0
    for mode in ("default", "policy", "readme", "research", "resume", "prompt"):
        assert mode in result.stdout


def test_cli_compare_text_low_drift_exits_zero() -> None:
    result = runner.invoke(
        app,
        [
            "compare-text",
            "The system may produce errors.",
            "The system may produce errors.",
            "--model",
            "tfidf",
            "--fail-on",
            "medium",
        ],
    )
    assert result.exit_code == 0


def test_cli_json_output_has_required_keys(tmp_path) -> None:
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("old content", encoding="utf-8")
    new.write_text("new content", encoding="utf-8")

    result = runner.invoke(app, ["compare", str(old), str(new), "--json", "--model", "tfidf"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in ("mode", "drift_label", "summary", "risk_flags", "recommendations"):
        assert key in payload


def test_cli_invalid_mode_shows_error(tmp_path) -> None:
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text("text", encoding="utf-8")
    new.write_text("text", encoding="utf-8")

    result = runner.invoke(
        app, ["compare", str(old), str(new), "--mode", "invalidmode", "--model", "tfidf"]
    )
    assert result.exit_code != 0


def test_cli_invalid_fail_on_shows_error(tmp_path) -> None:
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text("text", encoding="utf-8")
    new.write_text("text changed", encoding="utf-8")

    result = runner.invoke(
        app,
        ["compare", str(old), str(new), "--fail-on", "extreme", "--model", "tfidf"],
    )
    assert result.exit_code != 0


def test_cli_top_option_limits_output(tmp_path) -> None:
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("A.\n\nB.\n\nC.\n\nD.\n\nE.", encoding="utf-8")
    new.write_text("X.\n\nY.\n\nZ.\n\nW.\n\nV.", encoding="utf-8")

    result1 = runner.invoke(app, ["compare", str(old), str(new), "--top", "1", "--model", "tfidf"])
    result5 = runner.invoke(app, ["compare", str(old), str(new), "--top", "5", "--model", "tfidf"])
    assert result1.exit_code == 0
    assert result5.exit_code == 0


def test_cli_compare_text_default_mode_works() -> None:
    result = runner.invoke(
        app,
        ["compare-text", "The model may fail.", "The model is reliable.", "--model", "tfidf"],
    )
    assert result.exit_code == 0


def test_cli_unsupported_file_extension_shows_error(tmp_path) -> None:
    f = tmp_path / "file.pdf"
    f.write_bytes(b"data")

    result = runner.invoke(app, ["compare", str(f), str(f), "--model", "tfidf"])
    assert result.exit_code == 2
    assert "SemShift error" in result.stderr


def test_cli_report_and_json_can_coexist(tmp_path) -> None:
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    report = tmp_path / "report.md"
    old.write_text("old content", encoding="utf-8")
    new.write_text("new content", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "compare", str(old), str(new),
            "--json", "--report", str(report),
            "--model", "tfidf",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)
    assert report.exists()
