"""Command-line interface for semshift."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from semshift import __version__
from semshift.config import ConfigError, SemShiftConfig, load_config
from semshift.core.embeddings import DEFAULT_MODEL
from semshift.core.git_compare import GitCompareError
from semshift.core.git_compare import compare_git as compare_git_api
from semshift.core.loader import DEFAULT_MAX_FILE_SIZE, FileLoadError
from semshift.core.modes import MODES, list_modes
from semshift.core.report import (
    markdown_report,
    print_rich_report,
    result_to_json,
    write_markdown_report,
)
from semshift.core.semantic_diff import DEFAULT_MAX_CHUNKS, SemanticDiffResult
from semshift.core.semantic_diff import compare_files as compare_files_api
from semshift.core.semantic_diff import compare_text as compare_text_api
from semshift.utils.scoring import LABEL_ORDER, label_meets

app = typer.Typer(
    name="semshift",
    help=(
        "Local-first semantic review assistant. Flags likely drift, claim changes, "
        "tone shifts, and risk changes."
    ),
    no_args_is_help=True,
)
console = Console()

_DEFAULT_CONFIG_YML = """\
# SemShift configuration (.semshift.yml)
# These become the defaults for `semshift compare` and `semshift compare-git`.
# Explicit command-line flags always override them.

# Review mode: default | policy | prompt | research | resume | readme
mode: default

# Backend: tfidf (lexical, default) or a SentenceTransformers model (needs semshift[models])
model: tfidf

# Fail the command (exit 1) when drift reaches this label: low | medium | high | critical
# fail_on: high

# Git ref that `compare-git` diffs the working tree against
# ref: HEAD

# Limits for large or generated files
# max_file_size: 5242880
# max_chunks: 2000

# Number of top meaning changes to show
# top: 5
"""

_DEFAULT_WORKFLOW_YML = """\
name: SemShift Check

on:
  pull_request:
    paths:
      - "**/*.md"
      - "**/*.txt"
      - "**/*.yml"

permissions:
  contents: read
  pull-requests: write

jobs:
  semshift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: VeerajSai/SemShift@v0.2.0
        with:
          mode: policy
          fail_on: high
          pr_comment: "true"
          paths: "docs/**,**/*.md,**/*.txt"
          model: tfidf
          report: semshift-report.md
          artifact_name: semshift-report
"""

OldFileArgument = Annotated[Path, typer.Argument(help="Old file path.")]
NewFileArgument = Annotated[Path, typer.Argument(help="New file path.")]
OldTextArgument = Annotated[str, typer.Argument(help="Old text.")]
NewTextArgument = Annotated[str, typer.Argument(help="New text.")]
ModeOption = Annotated[
    str,
    typer.Option(
        "--mode",
        "-m",
        help=f"Review mode. One of: {', '.join(list_modes())}.",
    ),
]
ModelOption = Annotated[
    str,
    typer.Option(
        "--model",
        help=(
            "Backend name. Use 'tfidf' or 'lexical' for the deterministic lexical backend, "
            "or install semshift[models] for optional SentenceTransformers embeddings."
        ),
    ),
]
JsonOption = Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")]
FailOnOption = Annotated[
    str | None,
    typer.Option(
        "--fail-on",
        help="Exit with code 1 when drift label meets threshold: low, medium, high, critical.",
    ),
]
ReportOption = Annotated[Path | None, typer.Option("--report", help="Write a markdown report.")]
TopOption = Annotated[
    int,
    typer.Option(
        "--top",
        min=1,
        max=25,
        help="Number of top meaning changes to show in terminal and markdown reports.",
    ),
]
MaxFileSizeOption = Annotated[
    int,
    typer.Option(
        "--max-file-size",
        min=1,
        help="Maximum bytes to read from each file before truncating with a warning.",
    ),
]
MaxChunksOption = Annotated[
    int,
    typer.Option(
        "--max-chunks",
        min=1,
        help="Maximum chunks to compare per side before truncating with a warning.",
    ),
]
VersionOption = Annotated[
    bool | None,
    typer.Option(
        "--version",
        callback=lambda value: _show_version(value),
        help="Show the SemShift version and exit.",
        is_eager=True,
    ),
]


def _show_version(value: bool | None) -> None:
    if value:
        typer.echo(f"semshift {__version__}")
        raise typer.Exit()


@app.callback()
def root(version: VersionOption = None) -> None:
    """Configure global CLI options."""
    _ = version


@app.command()
def compare(
    ctx: typer.Context,
    old: OldFileArgument,
    new: NewFileArgument,
    mode: ModeOption = "default",
    model: ModelOption = DEFAULT_MODEL,
    json_output: JsonOption = False,
    fail_on: FailOnOption = None,
    report: ReportOption = None,
    top: TopOption = 5,
    max_file_size: MaxFileSizeOption = DEFAULT_MAX_FILE_SIZE,
    max_chunks: MaxChunksOption = DEFAULT_MAX_CHUNKS,
) -> None:
    """Compare two files for meaning-level drift."""
    merged = _merge_config(
        ctx,
        mode=mode,
        model=model,
        fail_on=fail_on,
        top=top,
        max_file_size=max_file_size,
        max_chunks=max_chunks,
    )
    try:
        result = compare_files_api(
            old,
            new,
            mode=merged["mode"],
            model=merged["model"],
            max_file_size=merged["max_file_size"],
            max_chunks=merged["max_chunks"],
        )
    except (FileLoadError, OSError, ValueError) as exc:
        _exit_with_error(str(exc))

    if report:
        write_markdown_report(result, report, top=merged["top"])

    if json_output:
        typer.echo(result_to_json(result))
    else:
        print_rich_report(result, console=console, top=merged["top"])
        if report:
            console.print(f"\n[green]Markdown report written to:[/green] {report}")

    _maybe_fail(result.drift_label, merged["fail_on"])


@app.command("compare-git")
def compare_git(
    ctx: typer.Context,
    paths: Annotated[
        list[str] | None,
        typer.Argument(help="Files to review. Default: all changed/untracked supported files."),
    ] = None,
    ref: Annotated[
        str, typer.Option("--ref", help="Git ref to compare the working tree against.")
    ] = "HEAD",
    mode: ModeOption = "default",
    model: ModelOption = DEFAULT_MODEL,
    json_output: JsonOption = False,
    fail_on: FailOnOption = None,
    report: ReportOption = None,
    top: TopOption = 5,
    max_file_size: MaxFileSizeOption = DEFAULT_MAX_FILE_SIZE,
    max_chunks: MaxChunksOption = DEFAULT_MAX_CHUNKS,
) -> None:
    """Review uncommitted edits: compare working-tree files against a git ref."""
    merged = _merge_config(
        ctx,
        mode=mode,
        model=model,
        fail_on=fail_on,
        ref=ref,
        top=top,
        max_file_size=max_file_size,
        max_chunks=max_chunks,
    )
    try:
        results = compare_git_api(
            paths,
            ref=merged["ref"],
            mode=merged["mode"],
            model=merged["model"],
            max_file_size=merged["max_file_size"],
            max_chunks=merged["max_chunks"],
        )
    except (GitCompareError, FileLoadError, OSError, ValueError) as exc:
        _exit_with_error(str(exc))

    if not results:
        console.print(f"No changed supported files to review against [cyan]{merged['ref']}[/cyan].")
        return

    if report:
        combined = "\n\n".join(markdown_report(result, top=merged["top"]) for result in results)
        Path(report).parent.mkdir(parents=True, exist_ok=True)
        Path(report).write_text(combined, encoding="utf-8")

    if json_output:
        typer.echo(json.dumps([result.to_dict() for result in results], indent=2))
    else:
        for result in results:
            print_rich_report(result, console=console, top=merged["top"])
            console.print()
        if report:
            console.print(f"[green]Markdown report written to:[/green] {report}")

    _maybe_fail(_worst_label(results), merged["fail_on"])


@app.command()
def init(
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files.")] = False,
    workflow: Annotated[
        bool,
        typer.Option("--workflow/--no-workflow", help="Also scaffold a GitHub Actions workflow."),
    ] = True,
) -> None:
    """Scaffold a .semshift.yml config (and an optional GitHub Actions workflow)."""
    created: list[str] = []
    skipped: list[str] = []

    targets: list[tuple[Path, str]] = [(Path(".semshift.yml"), _DEFAULT_CONFIG_YML)]
    if workflow:
        targets.append((Path(".github/workflows/semshift.yml"), _DEFAULT_WORKFLOW_YML))

    for path, content in targets:
        if path.exists() and not force:
            skipped.append(str(path))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(str(path))

    for path_str in created:
        console.print(f"[green]created[/green] {path_str}")
    for path_str in skipped:
        console.print(
            f"[yellow]exists, skipped[/yellow] {path_str} (use [cyan]--force[/cyan] to overwrite)"
        )
    if created:
        console.print(
            "\nEdit [cyan].semshift.yml[/cyan] to set your defaults, then run "
            "[cyan]semshift compare-git[/cyan]."
        )


@app.command("compare-text")
def compare_text(
    old: OldTextArgument,
    new: NewTextArgument,
    mode: ModeOption = "default",
    model: ModelOption = DEFAULT_MODEL,
    json_output: JsonOption = False,
    fail_on: FailOnOption = None,
    report: ReportOption = None,
    top: TopOption = 5,
    max_chunks: MaxChunksOption = DEFAULT_MAX_CHUNKS,
) -> None:
    """Compare two raw strings for meaning-level drift."""
    try:
        result = compare_text_api(old=old, new=new, mode=mode, model=model, max_chunks=max_chunks)
    except ValueError as exc:
        _exit_with_error(str(exc))

    if report:
        write_markdown_report(result, report, top=top)

    if json_output:
        typer.echo(result_to_json(result))
    else:
        print_rich_report(result, console=console, top=top)
        if report:
            console.print(f"\n[green]Markdown report written to:[/green] {report}")

    _maybe_fail(result.drift_label, fail_on)


@app.command("modes")
def modes() -> None:
    """List supported review modes."""
    table = Table(title="SemShift Modes")
    table.add_column("Mode", style="bold cyan")
    table.add_column("Review focus")
    for mode in list_modes():
        table.add_row(mode, MODES[mode].description)
    console.print(table)


def _merge_config(ctx: typer.Context, **values: object) -> dict[str, object]:
    """Override option values with .semshift.yml where the CLI used the default.

    Precedence: built-in default < .semshift.yml < explicit CLI flag.
    """
    try:
        config: SemShiftConfig = load_config()
    except ConfigError as exc:
        _exit_with_error(str(exc))

    config_values: dict[str, object | None] = {
        "mode": config.mode,
        "model": config.model,
        "fail_on": config.fail_on,
        "ref": config.ref,
        "top": config.top,
        "max_file_size": config.max_file_size,
        "max_chunks": config.max_chunks,
    }
    merged = dict(values)
    for name, value in values.items():
        config_value = config_values.get(name)
        if config_value is None:
            merged[name] = value
            continue
        source = ctx.get_parameter_source(name)
        used_default = source is None or source.name in {"DEFAULT", "DEFAULT_MAP"}
        merged[name] = config_value if used_default else value
    return merged


def _worst_label(results: list[SemanticDiffResult]) -> str:
    if not results:
        return "low"
    return max(results, key=lambda result: LABEL_ORDER[result.drift_label]).drift_label


def _maybe_fail(label: str, fail_on: str | None) -> None:
    if not fail_on:
        return
    try:
        should_fail = label_meets(label, fail_on)
    except ValueError as exc:
        _exit_with_error(str(exc))
    if should_fail:
        typer.secho(
            f"SemShift failed because drift label '{label}' meets --fail-on '{fail_on}'.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def _exit_with_error(message: str) -> NoReturn:
    typer.secho(f"SemShift error: {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=2)


def main() -> None:
    """Console script entrypoint."""
    app()


if __name__ == "__main__":
    main()
