"""Shared pytest fixtures."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with one committed file (``policy.md``).

    The working tree starts clean and equal to ``HEAD``; tests edit files and then
    compare the working tree against the ref.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "SemShift Test"], repo)
    _git(["config", "commit.gpgsign", "false"], repo)
    (repo / "policy.md").write_text(
        "# Data Sharing\n\nWe do not share personal data with third parties.\n",
        encoding="utf-8",
    )
    _git(["add", "."], repo)
    _git(["commit", "-m", "initial"], repo)
    return repo
