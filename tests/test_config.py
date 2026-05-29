"""Tests for .semshift.yml loading and CLI merge precedence."""

from __future__ import annotations

import json
from inspect import signature
from pathlib import Path

import pytest
from typer.testing import CliRunner

from semshift.cli import app
from semshift.config import ConfigError, SemShiftConfig, find_config, load_config


def _runner() -> CliRunner:
    kwargs = {}
    if "mix_stderr" in signature(CliRunner).parameters:
        kwargs["mix_stderr"] = False
    return CliRunner(**kwargs)


runner = _runner()


def test_missing_config_returns_empty(tmp_path: Path) -> None:
    assert load_config(start=tmp_path) == SemShiftConfig()


def test_load_valid_config(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text(
        "mode: policy\nmodel: tfidf\nfail_on: high\nmax_chunks: 500\n"
        "paths:\n  - docs/**\n  - prompts/**\n",
        encoding="utf-8",
    )
    config = load_config(start=tmp_path)
    assert config.mode == "policy"
    assert config.fail_on == "high"
    assert config.max_chunks == 500
    assert config.paths == ("docs/**", "prompts/**")


def test_single_string_list_is_normalized(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text("paths: docs/**\n", encoding="utf-8")
    assert load_config(start=tmp_path).paths == ("docs/**",)


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text("mode: [unterminated\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(start=tmp_path)


def test_non_mapping_raises(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="must contain a YAML mapping"):
        load_config(start=tmp_path)


def test_unknown_key_raises(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text("bogus: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Unknown key"):
        load_config(start=tmp_path)


def test_wrong_type_raises(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text("max_chunks: not-a-number\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="must be an integer"):
        load_config(start=tmp_path)


def test_find_config_walks_up(tmp_path: Path) -> None:
    (tmp_path / ".semshift.yml").write_text("mode: policy\n", encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    found = find_config(start=nested)
    assert found is not None and found.parent == tmp_path


def _write_pair(tmp_path: Path) -> tuple[Path, Path]:
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text("We do not share personal data with third parties.", encoding="utf-8")
    new.write_text("We may share personal data with selected partners.", encoding="utf-8")
    return old, new


def test_cli_uses_config_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".semshift.yml").write_text("mode: policy\n", encoding="utf-8")
    old, new = _write_pair(tmp_path)
    result = runner.invoke(app, ["compare", str(old), str(new), "--model", "tfidf", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["mode"] == "policy"


def test_cli_flag_overrides_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".semshift.yml").write_text("mode: policy\n", encoding="utf-8")
    old, new = _write_pair(tmp_path)
    result = runner.invoke(
        app, ["compare", str(old), str(new), "--mode", "research", "--model", "tfidf", "--json"]
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["mode"] == "research"


def test_cli_invalid_config_reports_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".semshift.yml").write_text("bogus: 1\n", encoding="utf-8")
    old, new = _write_pair(tmp_path)
    result = runner.invoke(app, ["compare", str(old), str(new), "--model", "tfidf"])
    assert result.exit_code == 2
    assert "Unknown key" in result.stderr


def test_init_scaffolds_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / ".semshift.yml").exists()
    assert (tmp_path / ".github" / "workflows" / "semshift.yml").exists()


def test_init_does_not_overwrite_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".semshift.yml").write_text("mode: research\n", encoding="utf-8")
    result = runner.invoke(app, ["init", "--no-workflow"])
    assert result.exit_code == 0
    assert (tmp_path / ".semshift.yml").read_text(encoding="utf-8") == "mode: research\n"
    assert "skipped" in result.stdout
