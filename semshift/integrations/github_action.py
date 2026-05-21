"""GitHub Action entrypoint for SemShift."""

from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rich.console import Console
from rich.markup import escape as rich_escape

from semshift.core.embeddings import DEFAULT_MODEL
from semshift.core.loader import DEFAULT_MAX_FILE_SIZE, SUPPORTED_EXTENSIONS, FileLoadError
from semshift.core.report import markdown_report
from semshift.core.semantic_diff import DEFAULT_MAX_CHUNKS, SemanticDiffResult, compare_text
from semshift.utils.scoring import LABEL_ORDER, label_meets
from semshift.utils.text import escape_markdown_text, markdown_code

MAX_COMMENT_LENGTH = 60_000
SAFE_REF_RE = re.compile(r"^[A-Za-z0-9._/\-~^]+$")
CONSOLE = Console()
ERROR_CONSOLE = Console(stderr=True)


def main(argv: list[str] | None = None) -> int:
    """Run SemShift over a comma-separated file list in GitHub Actions."""
    parser = argparse.ArgumentParser(description="Run SemShift in GitHub Actions.")
    parser.add_argument(
        "--files",
        default="",
        help=(
            "Comma-separated files or glob patterns. "
            "When omitted, SemShift compares changed supported files in the PR."
        ),
    )
    parser.add_argument(
        "--paths",
        default="",
        help="Comma-separated include globs applied to changed or explicit files.",
    )
    parser.add_argument(
        "--exclude-paths",
        default="",
        help="Comma-separated exclude globs applied to changed or explicit files.",
    )
    parser.add_argument("--mode", default="default")
    parser.add_argument("--fail-on", default="")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--report", default="semshift-report.md")
    parser.add_argument("--artifact-name", default="semshift-report")
    parser.add_argument("--base-ref", default="", help="Base branch/ref to compare against.")
    parser.add_argument(
        "--pr-comment", default="false", help="Post or update a pull request comment."
    )
    parser.add_argument("--github-token", default="", help="GitHub token for PR comments.")
    parser.add_argument("--max-file-size", type=int, default=DEFAULT_MAX_FILE_SIZE)
    parser.add_argument("--max-chunks", type=int, default=DEFAULT_MAX_CHUNKS)
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF") or "HEAD^"
    if not _is_safe_ref(base_ref):
        ERROR_CONSOLE.print(f"[red]SemShift error:[/red] unsafe base ref: {rich_escape(base_ref)}")
        return 2

    report_path = _safe_output_path(args.report, repo_root)
    if report_path is None:
        ERROR_CONSOLE.print(
            f"[red]SemShift error:[/red] unsafe report path: {rich_escape(args.report)}"
        )
        return 2

    files = _resolve_files(
        args.files,
        base_ref,
        paths=args.paths,
        exclude_paths=args.exclude_paths,
    )
    if not files:
        CONSOLE.print("No supported files were provided or changed. Nothing to compare.")
        _write_action_summary("# SemShift\n\nNo supported files were compared.\n")
        _write_action_outputs([], report_path)
        return 0

    results: list[SemanticDiffResult] = []
    skipped: list[str] = []
    failed = False

    for file_name in files:
        try:
            old_text = _git_show(base_ref, file_name)
            new_text, warnings = _read_worktree_text(
                file_name,
                repo_root=repo_root,
                max_file_size=args.max_file_size,
            )
        except FileLoadError as exc:
            skipped.append(str(exc))
            CONSOLE.print(
                f"[yellow]Skipping[/yellow] {rich_escape(file_name)}: {rich_escape(str(exc))}"
            )
            continue

        if old_text is None and not new_text:
            message = f"not present in base or working tree: {file_name}"
            skipped.append(message)
            CONSOLE.print(
                f"[yellow]Skipping[/yellow] {rich_escape(file_name)}: {rich_escape(message)}"
            )
            continue

        try:
            result = compare_text(
                old=old_text or "",
                new=new_text,
                mode=args.mode,
                model=args.model,
                max_chunks=args.max_chunks,
                old_label=f"{base_ref}:{file_name}",
                new_label=file_name,
                input_warnings=tuple(warnings),
            )
        except ValueError as exc:
            ERROR_CONSOLE.print(f"[red]SemShift error:[/red] {rich_escape(str(exc))}")
            return 2

        results.append(result)
        CONSOLE.print(
            f"{rich_escape(file_name)}: {result.overall_score:.2f} {result.drift_label.upper()}"
        )
        try:
            if label_meets(result.drift_label, args.fail_on):
                failed = True
        except ValueError as exc:
            ERROR_CONSOLE.print(f"[red]SemShift error:[/red] {rich_escape(str(exc))}")
            return 2

    report = _combined_markdown(results, skipped=skipped)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    workflow_run_url = _workflow_run_url()
    _write_action_summary(
        _summary_markdown(
            results,
            args.fail_on,
            report_path,
            skipped=skipped,
            artifact_name=args.artifact_name,
            workflow_run_url=workflow_run_url,
        )
    )
    _write_action_outputs(results, report_path)
    if _truthy(args.pr_comment):
        _maybe_post_pr_comment(
            _pr_comment_body(
                results,
                report_path,
                skipped=skipped,
                artifact_name=args.artifact_name,
                workflow_run_url=workflow_run_url,
            ),
            args.github_token,
        )
    CONSOLE.print(f"SemShift report written to {report_path}")
    if failed:
        message = _failure_message(
            _worst_label(results),
            args.fail_on,
            report_path,
            artifact_name=args.artifact_name,
            workflow_run_url=workflow_run_url,
        )
        _github_error(message)
        ERROR_CONSOLE.print(f"[red]{rich_escape(message)}[/red]")
        return 1
    return 0


def _repo_root() -> Path:
    try:
        completed = subprocess.run(  # nosec B603 B607
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd().resolve()
    return Path(completed.stdout.strip()).resolve()


def _resolve_files(
    raw_files: str,
    base_ref: str,
    *,
    paths: str = "",
    exclude_paths: str = "",
) -> list[str]:
    """Resolve explicit files/globs or changed files into safe repo-relative paths."""
    repo_root = _repo_root()
    patterns = _split_patterns(raw_files)
    if not patterns:
        return _filter_paths(
            _changed_supported_files(base_ref),
            include_patterns=_split_patterns(paths),
            exclude_patterns=_split_patterns(exclude_paths),
        )

    files: set[str] = set()
    for pattern in patterns:
        for match in glob.glob(pattern, recursive=True) or [pattern]:
            normalized = _normalize_repo_path(match, repo_root)
            if normalized is not None and _is_supported(Path(normalized)):
                path = repo_root / normalized
                if path.exists() and not path.is_file():
                    continue
                files.add(normalized)
    return _filter_paths(
        sorted(files),
        include_patterns=_split_patterns(paths),
        exclude_patterns=_split_patterns(exclude_paths),
    )


def _split_patterns(raw_patterns: str) -> list[str]:
    return [item.strip().replace("\\", "/") for item in raw_patterns.split(",") if item.strip()]


def _filter_paths(
    files: list[str],
    *,
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> list[str]:
    filtered = []
    for file_name in files:
        normalized = file_name.replace("\\", "/")
        if include_patterns and not _matches_any_pattern(normalized, include_patterns):
            continue
        if exclude_patterns and _matches_any_pattern(normalized, exclude_patterns):
            continue
        filtered.append(normalized)
    return sorted(filtered)


def _matches_any_pattern(file_name: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        normalized_pattern = pattern.removeprefix("./")
        if normalized_pattern.endswith("/"):
            normalized_pattern += "**"
        if fnmatch.fnmatchcase(file_name, normalized_pattern):
            return True
        if normalized_pattern.startswith("**/") and fnmatch.fnmatchcase(
            file_name, normalized_pattern[3:]
        ):
            return True
    return False


def _changed_supported_files(base_ref: str) -> list[str]:
    """Return changed supported files using NUL-delimited git output."""
    if not _is_safe_ref(base_ref):
        return []
    repo_root = _repo_root()
    candidates = [f"origin/{base_ref}...HEAD", f"{base_ref}...HEAD", base_ref]
    for candidate in candidates:
        try:
            completed = subprocess.run(  # nosec B603 B607
                ["git", "diff", "--name-only", "-z", "--diff-filter=ACMRD", candidate],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        files = []
        for raw in completed.stdout.split("\0"):
            if not raw:
                continue
            normalized = _normalize_repo_path(raw, repo_root)
            if normalized is not None and _is_supported(Path(normalized)):
                files.append(normalized)
        if files:
            return sorted(set(files))
    return []


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _git_show(base_ref: str, file_name: str) -> str | None:
    """Read a file from a safe git ref without invoking a shell."""
    if not _is_safe_ref(base_ref):
        return None
    repo_root = _repo_root()
    normalized = _normalize_repo_path(file_name, repo_root)
    if normalized is None:
        return None
    refs = [f"origin/{base_ref}:{normalized}", f"{base_ref}:{normalized}"]
    for ref in refs:
        try:
            completed = subprocess.run(  # nosec B603 B607
                ["git", "show", "--no-ext-diff", ref],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return completed.stdout
        except (OSError, subprocess.CalledProcessError):
            continue
    return None


def _read_worktree_text(
    file_name: str,
    *,
    repo_root: Path,
    max_file_size: int,
) -> tuple[str, list[str]]:
    normalized = _normalize_repo_path(file_name, repo_root)
    if normalized is None:
        raise FileLoadError(f"unsafe path rejected: {file_name}")
    path = repo_root / normalized
    if not path.exists():
        return "", []
    from semshift.core.loader import load_text_file_with_warnings

    loaded = load_text_file_with_warnings(path, max_file_size=max_file_size)
    return loaded.text, list(loaded.warnings)


def _combined_markdown(
    results: list[SemanticDiffResult],
    *,
    skipped: list[str] | None = None,
) -> str:
    if not results and not skipped:
        return "# SemShift Report\n\nNo matching files were compared.\n"

    sections = ["# SemShift Report", ""]
    if results:
        sections.extend(_summary_table(results))
        sections.append("")
        for result in results:
            sections.append(
                markdown_report(result).replace("# SemShift Report", "## File Report", 1)
            )
            sections.append("")
    if skipped:
        sections.extend(["## Skipped Files", ""])
        sections.extend(f"- {escape_markdown_text(item)}" for item in skipped)
        sections.append("")
    sections.append(
        "_SemShift flags likely semantic drift. It is not a legal opinion, "
        "fact-checker, scientific authority, or replacement for human review._"
    )
    return "\n".join(sections).rstrip() + "\n"


def _summary_markdown(
    results: list[SemanticDiffResult],
    fail_on: str,
    report_path: Path,
    *,
    skipped: list[str] | None = None,
    artifact_name: str = "semshift-report",
    workflow_run_url: str | None = None,
) -> str:
    lines = ["# SemShift", ""]
    if not results:
        lines.append("No supported files were compared.")
    else:
        worst = _worst_label(results)
        lines.append(f"Compared **{len(results)}** file(s). Worst drift: **{worst.upper()}**.")
        if fail_on:
            if label_meets(worst, fail_on):
                lines.append(f"Result: failing because `{worst}` meets `fail_on: {fail_on}`.")
            else:
                lines.append(f"Result: warn-only/pass for `fail_on: {fail_on}`.")
        lines.append("")
        lines.extend(_summary_table(results))
    lines.append(
        "Full report: "
        f"{markdown_code(report_path.as_posix())} in artifact "
        f"{markdown_code(artifact_name)}."
    )
    if workflow_run_url:
        lines.append(f"Workflow run: {workflow_run_url}")
    if skipped:
        lines.extend(["", "Skipped files:", ""])
        lines.extend(f"- {escape_markdown_text(item)}" for item in skipped[:10])
    lines.append("")
    return "\n".join(lines)


def _summary_table(results: list[SemanticDiffResult]) -> list[str]:
    lines = [
        "| File | Score | Label | Risk flags | Changed claims |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            "| "
            f"{markdown_code(result.new_label, max_chars=140)} | "
            f"{result.overall_score:.2f} | "
            f"{result.drift_label.upper()} | "
            f"{len(result.risk_flags)} | "
            f"{result.claim_changes.change_count} |"
        )
    return lines


def _write_action_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write(markdown.rstrip() + "\n")


def _write_action_outputs(results: list[SemanticDiffResult], report_path: Path) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"report_path={report_path.as_posix()}\n")
        handle.write(f"worst_label={_worst_label(results)}\n")


def _pr_comment_body(
    results: list[SemanticDiffResult],
    report_path: str | Path,
    *,
    skipped: list[str] | None = None,
    artifact_name: str = "semshift-report",
    workflow_run_url: str | None = None,
) -> str:
    body = ["<!-- semshift-report -->", "# SemShift semantic review", ""]
    if not results:
        body.append("No supported files were compared.")
    else:
        worst = _worst_label(results)
        body.append(f"Compared **{len(results)}** file(s). Worst drift: **{worst.upper()}**.")
        body.append("")
        body.extend(_summary_table(results))
    body.append(
        "Full Markdown report: "
        f"{markdown_code(Path(report_path).as_posix())} in artifact "
        f"{markdown_code(artifact_name)}."
    )
    if workflow_run_url:
        body.append(f"Workflow run artifacts: {workflow_run_url}")
    if skipped:
        body.extend(["", "Skipped files:", ""])
        body.extend(f"- {escape_markdown_text(item)}" for item in skipped[:10])
    body.extend(
        [
            "",
            "_SemShift flags likely semantic drift. It is not a legal opinion, fact-checker, "
            "scientific authority, or replacement for human review._",
        ]
    )
    return _truncate_comment_body("\n".join(body) + "\n")


def _truncate_comment_body(body: str, *, max_length: int = MAX_COMMENT_LENGTH) -> str:
    if len(body) <= max_length:
        return body
    footer = (
        "\n\n_Report truncated for GitHub comment length. "
        "Open the SemShift report artifact for full details._\n"
    )
    return body[: max_length - len(footer)].rstrip() + footer


def _maybe_post_pr_comment(body: str, github_token: str) -> None:
    token = github_token or os.environ.get("GITHUB_TOKEN", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not event_path or not repo:
        CONSOLE.print(
            "Skipping PR comment: missing GITHUB_TOKEN, GITHUB_EVENT_PATH, or GITHUB_REPOSITORY."
        )
        return

    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        number = event.get("pull_request", {}).get("number") or event.get("number")
        if not number:
            CONSOLE.print("Skipping PR comment: this event is not a pull request.")
            return
        comments_url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
        existing_url = _find_existing_comment(comments_url, token)
        if existing_url:
            _github_request(existing_url, token, method="PATCH", payload={"body": body})
            CONSOLE.print("Updated SemShift PR comment.")
        else:
            _github_request(comments_url, token, method="POST", payload={"body": body})
            CONSOLE.print("Created SemShift PR comment.")
    except (OSError, KeyError, ValueError, HTTPError, URLError) as exc:
        ERROR_CONSOLE.print(f"Skipping PR comment: {rich_escape(str(exc))}")


def _workflow_run_url() -> str | None:
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not repo or not run_id:
        return None
    return f"{server_url}/{repo}/actions/runs/{run_id}#artifacts"


def _failure_message(
    worst_label: str,
    fail_on: str,
    report_path: Path,
    *,
    artifact_name: str,
    workflow_run_url: str | None,
) -> str:
    message = (
        f"SemShift detected {worst_label.upper()} drift meeting fail_on '{fail_on}'. "
        f"Review {report_path.as_posix()} in artifact '{artifact_name}'."
    )
    if workflow_run_url:
        message += f" Artifacts: {workflow_run_url}"
    return message


def _github_error(message: str) -> None:
    escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    sys.stderr.write(f"::error title=SemShift drift detected::{escaped}\n")


def _find_existing_comment(comments_url: str, token: str) -> str | None:
    comments = _github_request(comments_url, token, method="GET")
    if not isinstance(comments, list):
        return None
    for comment in comments:
        body = str(comment.get("body", ""))
        user = comment.get("user") or {}
        if "<!-- semshift-report -->" in body and user.get("type") == "Bot":
            return str(comment.get("url"))
    return None


def _github_request(
    url: str,
    token: str,
    *,
    method: str,
    payload: dict[str, str] | None = None,
) -> object:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "semshift-action",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=15) as response:  # nosec B310
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _safe_output_path(raw_path: str, repo_root: Path) -> Path | None:
    normalized = _normalize_lexical_path(raw_path)
    if normalized is None:
        return None
    output_path = (repo_root / normalized).resolve()
    if not _is_relative_to(output_path, repo_root):
        return None
    return output_path


def _normalize_repo_path(raw_path: str, repo_root: Path) -> str | None:
    normalized = _normalize_lexical_path(raw_path)
    if normalized is None:
        return None
    candidate = repo_root / normalized
    if candidate.exists():
        resolved = candidate.resolve()
        if not _is_relative_to(resolved, repo_root.resolve()):
            return None
        try:
            return resolved.relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return None
    return normalized.as_posix()


def _normalize_lexical_path(raw_path: str) -> Path | None:
    if "\x00" in raw_path:
        return None
    path = Path(raw_path)
    if path.is_absolute() or path.drive:
        return None
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    if not path.parts:
        return None
    return Path(*path.parts)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_safe_ref(ref: str) -> bool:
    return bool(ref and SAFE_REF_RE.fullmatch(ref) and ".." not in ref and not ref.startswith("-"))


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _worst_label(results: list[SemanticDiffResult]) -> str:
    if not results:
        return "low"
    return max(results, key=lambda result: LABEL_ORDER[result.drift_label]).drift_label


if __name__ == "__main__":
    raise SystemExit(main())
