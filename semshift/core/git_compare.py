"""Compare working-tree files against a git ref for local pre-merge review.

This powers ``semshift compare-git`` — the "review my own uncommitted edits before
I merge" workflow. It reuses the same safe, no-shell git access pattern as the
GitHub Action (validated refs, ``git show`` without a shell, repo-root containment).
"""

from __future__ import annotations

import re
import subprocess  # nosec B404
from pathlib import Path

from semshift.core.embeddings import DEFAULT_MODEL
from semshift.core.loader import (
    DEFAULT_MAX_FILE_SIZE,
    SUPPORTED_EXTENSIONS,
    load_text_file_with_warnings,
)
from semshift.core.semantic_diff import (
    DEFAULT_MAX_CHUNKS,
    SemanticDiffResult,
    compare_text,
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9._/\-~^@{}]+$")


class GitCompareError(RuntimeError):
    """Raised when SemShift cannot compare against git."""


def is_safe_ref(ref: str) -> bool:
    """Return whether a git ref is safe to interpolate into a git argument."""
    return bool(ref and SAFE_REF_RE.fullmatch(ref) and ".." not in ref and not ref.startswith("-"))


def _run_git(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603 B607
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )


def repo_root(start: str | Path | None = None) -> Path:
    """Return the git repository root, or raise a clear error if not in a repo."""
    try:
        completed = _run_git(["rev-parse", "--show-toplevel"], cwd=Path(start) if start else None)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitCompareError(
            "Not inside a git repository (or git is not installed). "
            "Run semshift compare-git from within a git project."
        ) from exc
    return Path(completed.stdout.strip()).resolve()


def _git_show(ref: str, rel_path: str, *, root: Path) -> str | None:
    """Read a file at ``ref`` without invoking a shell. Returns None if absent at ref."""
    if not is_safe_ref(ref):
        raise GitCompareError(f"Unsafe git ref: {ref!r}")
    try:
        completed = _run_git(["show", "--no-ext-diff", f"{ref}:{rel_path}"], cwd=root)
    except subprocess.CalledProcessError:
        return None
    except OSError as exc:
        raise GitCompareError(f"git show failed for {rel_path}: {exc}") from exc
    return completed.stdout


def _relative_to_repo(path: str | Path, root: Path) -> str:
    candidate = Path(path)
    absolute = candidate if candidate.is_absolute() else (Path.cwd() / candidate)
    resolved = absolute.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise GitCompareError(f"Path is outside the git repository: {path}") from exc


def changed_files(ref: str, *, root: Path) -> list[str]:
    """Return supported files that changed vs ``ref`` (tracked diffs plus untracked)."""
    if not is_safe_ref(ref):
        raise GitCompareError(f"Unsafe git ref: {ref!r}")
    files: set[str] = set()
    try:
        diff = _run_git(["diff", "--name-only", "-z", "--diff-filter=ACMRD", ref], cwd=root)
        untracked = _run_git(["ls-files", "--others", "--exclude-standard", "-z"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitCompareError(f"git could not list changed files vs {ref!r}: {exc}") from exc
    for output in (diff.stdout, untracked.stdout):
        for raw in output.split("\0"):
            if raw and Path(raw).suffix.lower() in SUPPORTED_EXTENSIONS:
                files.add(raw)
    return sorted(files)


def compare_git(
    paths: list[str] | None = None,
    *,
    ref: str = "HEAD",
    mode: str = "default",
    model: str = DEFAULT_MODEL,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_chunks: int = DEFAULT_MAX_CHUNKS,
    start: str | Path | None = None,
) -> list[SemanticDiffResult]:
    """Compare working-tree file(s) against ``ref``.

    With no ``paths``, compares every supported changed/untracked file. Returns one
    :class:`SemanticDiffResult` per file (in stable path order).
    """
    if not is_safe_ref(ref):
        raise GitCompareError(f"Unsafe git ref: {ref!r}")
    root = repo_root(start)
    try:
        _run_git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd=root)
    except subprocess.CalledProcessError as exc:
        raise GitCompareError(f"Unknown or invalid git ref: {ref!r}") from exc
    except OSError as exc:  # pragma: no cover - git availability already checked
        raise GitCompareError(f"git rev-parse failed: {exc}") from exc
    if paths:
        rel_paths = sorted({_relative_to_repo(path, root) for path in paths})
    else:
        rel_paths = changed_files(ref, root=root)

    results: list[SemanticDiffResult] = []
    for rel in rel_paths:
        if Path(rel).suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise GitCompareError(
                f"Unsupported file extension for {rel!r}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        old_text = _git_show(ref, rel, root=root)
        worktree_path = root / rel
        if worktree_path.exists():
            loaded = load_text_file_with_warnings(worktree_path, max_file_size=max_file_size)
            new_text, warnings = loaded.text, loaded.warnings
        else:
            new_text, warnings = "", ()
        if old_text is None and not new_text:
            raise GitCompareError(f"File not found at {ref} or in the working tree: {rel}")
        results.append(
            compare_text(
                old=old_text or "",
                new=new_text,
                mode=mode,
                model=model,
                max_chunks=max_chunks,
                old_label=f"{ref}:{rel}",
                new_label=f"(working tree) {rel}",
                input_warnings=tuple(warnings),
            )
        )
    return results
