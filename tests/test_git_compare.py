"""Tests for git-aware comparison (``semshift compare-git``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from semshift.core.git_compare import (
    GitCompareError,
    changed_files,
    compare_git,
    is_safe_ref,
    repo_root,
)


def _weaken_policy(repo: Path) -> None:
    (repo / "policy.md").write_text(
        "# Data Sharing\n\nWe may share personal data with selected partners.\n",
        encoding="utf-8",
    )


def test_compare_git_detects_drift_against_head(git_repo: Path) -> None:
    _weaken_policy(git_repo)
    results = compare_git([str(git_repo / "policy.md")], ref="HEAD", mode="policy", start=git_repo)
    assert len(results) == 1
    assert results[0].drift_label in {"high", "critical"}
    assert results[0].old_label == "HEAD:policy.md"


def test_compare_git_no_paths_uses_changed_files(git_repo: Path) -> None:
    _weaken_policy(git_repo)
    results = compare_git(None, ref="HEAD", mode="policy", start=git_repo)
    assert len(results) == 1
    assert results[0].new_label.endswith("policy.md")


def test_compare_git_clean_tree_has_no_changes(git_repo: Path) -> None:
    assert compare_git(None, ref="HEAD", start=git_repo) == []


def test_changed_files_includes_untracked(git_repo: Path) -> None:
    (git_repo / "notes.md").write_text("brand new file\n", encoding="utf-8")
    changed = changed_files("HEAD", root=git_repo)
    assert "notes.md" in changed


def test_compare_git_unknown_ref_errors(git_repo: Path) -> None:
    with pytest.raises(GitCompareError, match="Unknown or invalid git ref"):
        compare_git([str(git_repo / "policy.md")], ref="does-not-exist", start=git_repo)


def test_compare_git_outside_repo_errors(tmp_path: Path) -> None:
    with pytest.raises(GitCompareError):
        compare_git(None, start=tmp_path)


def test_compare_git_unsupported_extension_errors(git_repo: Path) -> None:
    binary = git_repo / "image.bin"
    binary.write_text("x", encoding="utf-8")
    with pytest.raises(GitCompareError, match="Unsupported file extension"):
        compare_git([str(binary)], ref="HEAD", start=git_repo)


def test_compare_git_added_file(git_repo: Path) -> None:
    (git_repo / "new.md").write_text("Some entirely new content.\n", encoding="utf-8")
    results = compare_git([str(git_repo / "new.md")], ref="HEAD", start=git_repo)
    assert len(results) == 1
    assert results[0].old_label == "HEAD:new.md"


def test_repo_root_resolves(git_repo: Path) -> None:
    assert repo_root(git_repo).resolve() == git_repo.resolve()


def test_unsafe_refs_rejected() -> None:
    assert is_safe_ref("HEAD")
    assert is_safe_ref("origin/main")
    assert not is_safe_ref("--upload-pack=evil")
    assert not is_safe_ref("a..b")
    assert not is_safe_ref("")
