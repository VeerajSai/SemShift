"""GitHub Action entrypoint for semshift."""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from semshift.core.embeddings import DEFAULT_MODEL
from semshift.core.loader import SUPPORTED_EXTENSIONS
from semshift.core.report import markdown_report
from semshift.core.semantic_diff import SemanticDiffResult, compare_text
from semshift.utils.scoring import LABEL_ORDER, label_meets


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
    parser.add_argument("--mode", default="default")
    parser.add_argument("--fail-on", default="")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--report", default="semshift-report.md")
    parser.add_argument("--base-ref", default="", help="Base branch/ref to compare against.")
    parser.add_argument("--pr-comment", default="false", help="Post or update a pull request comment.")
    parser.add_argument("--github-token", default="", help="GitHub token for PR comments.")
    args = parser.parse_args(argv)

    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF") or "HEAD^"
    files = _resolve_files(args.files, base_ref)
    if not files:
        print("No supported files were provided or changed. Nothing to compare.")
        _write_action_summary("# SemShift\n\nNo supported files were compared.\n")
        return 0

    results: list[SemanticDiffResult] = []
    failed = False

    for file_name in files:
        new_path = Path(file_name)
        old_text = _git_show(base_ref, file_name)
        new_text = new_path.read_text(encoding="utf-8", errors="replace") if new_path.exists() else ""
        if old_text is None and not new_text:
            print(f"Skipping {file_name}: not present in base or working tree.")
            continue
        result = compare_text(
            old=old_text or "",
            new=new_text,
            mode=args.mode,
            model=args.model,
            old_label=f"{base_ref}:{file_name}",
            new_label=file_name,
        )
        results.append(result)
        print(f"{file_name}: {result.overall_score:.2f} {result.drift_label.upper()}")
        try:
            if args.fail_on and label_meets(result.drift_label, args.fail_on):
                failed = True
        except ValueError as exc:
            print(f"SemShift error: {exc}", file=sys.stderr)
            return 2

    report_path = Path(args.report)
    report = _combined_markdown(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    _write_action_summary(_summary_markdown(results, args.fail_on, report_path))
    _write_action_outputs(results, report_path)
    if _truthy(args.pr_comment):
        _maybe_post_pr_comment(_pr_comment_body(results, report_path), args.github_token)
    print(f"SemShift report written to {report_path}")
    return 1 if failed else 0


def _resolve_files(raw_files: str, base_ref: str) -> list[str]:
    patterns = [item.strip() for item in raw_files.split(",") if item.strip()]
    if not patterns:
        return _changed_supported_files(base_ref)

    files: set[str] = set()
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            for match in matches:
                path = Path(match)
                if path.is_file() and _is_supported(path):
                    files.add(path.as_posix())
        else:
            path = Path(pattern)
            if _is_supported(path):
                files.add(path.as_posix())
    return sorted(files)


def _changed_supported_files(base_ref: str) -> list[str]:
    candidates = [f"origin/{base_ref}...HEAD", f"{base_ref}...HEAD", f"{base_ref}"]
    for candidate in candidates:
        try:
            completed = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=ACMRD", candidate],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError:
            continue
        files = [
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip() and _is_supported(Path(line.strip()))
        ]
        if files:
            return sorted(set(files))
    return []


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _git_show(base_ref: str, file_name: str) -> str | None:
    refs = [f"origin/{base_ref}:{file_name}", f"{base_ref}:{file_name}"]
    for ref in refs:
        try:
            completed = subprocess.run(
                ["git", "show", ref],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return completed.stdout
        except subprocess.CalledProcessError:
            continue
    return None


def _combined_markdown(results: list[SemanticDiffResult]) -> str:
    if not results:
        return "# SemShift Report\n\nNo matching files were compared.\n"

    sections = ["# SemShift Report", ""]
    sections.extend(_summary_table(results))
    sections.append("")
    for result in results:
        sections.append(markdown_report(result).replace("# SemShift Report", "## File Report", 1))
        sections.append("")
    return "\n".join(sections)


def _summary_markdown(
    results: list[SemanticDiffResult],
    fail_on: str,
    report_path: Path,
) -> str:
    lines = ["# SemShift", ""]
    if not results:
        return "# SemShift\n\nNo supported files were compared.\n"

    worst = _worst_label(results)
    lines.append(f"Compared **{len(results)}** file(s). Worst drift: **{worst.upper()}**.")
    if fail_on:
        lines.append(f"Failure threshold: `{fail_on}`.")
    lines.append(f"Full report artifact: `{report_path}`.")
    lines.append("")
    lines.extend(_summary_table(results))
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
            f"`{result.new_label}` | "
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


def _pr_comment_body(results: list[SemanticDiffResult], report_path: Path) -> str:
    body = ["<!-- semshift-report -->", "# SemShift semantic review", ""]
    if not results:
        body.append("No supported files were compared.")
        return "\n".join(body) + "\n"

    worst = _worst_label(results)
    body.append(f"Compared **{len(results)}** file(s). Worst drift: **{worst.upper()}**.")
    body.append(f"Full markdown report is available in the workflow artifact: `{report_path}`.")
    body.append("")
    body.extend(_summary_table(results))
    body.append("")
    body.append("_SemShift is heuristic. Treat this as a review queue, not a final verdict._")
    return "\n".join(body) + "\n"


def _maybe_post_pr_comment(body: str, github_token: str) -> None:
    token = github_token or os.environ.get("GITHUB_TOKEN", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not event_path or not repo:
        print("Skipping PR comment: missing GITHUB_TOKEN, GITHUB_EVENT_PATH, or GITHUB_REPOSITORY.")
        return

    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        number = event.get("pull_request", {}).get("number") or event.get("number")
        if not number:
            print("Skipping PR comment: this event is not a pull request.")
            return
        comments_url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
        existing_url = _find_existing_comment(comments_url, token)
        if existing_url:
            _github_request(existing_url, token, method="PATCH", payload={"body": body})
            print("Updated SemShift PR comment.")
        else:
            _github_request(comments_url, token, method="POST", payload={"body": body})
            print("Created SemShift PR comment.")
    except (OSError, KeyError, ValueError, HTTPError, URLError) as exc:
        print(f"Skipping PR comment: {exc}", file=sys.stderr)


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
    with urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _worst_label(results: list[SemanticDiffResult]) -> str:
    if not results:
        return "low"
    return max(results, key=lambda result: LABEL_ORDER[result.drift_label]).drift_label


if __name__ == "__main__":
    raise SystemExit(main())
