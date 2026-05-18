"""Command-line interface for semshift."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from semshift.core.embeddings import DEFAULT_MODEL
from semshift.core.loader import FileLoadError
from semshift.core.modes import MODES, list_modes
from semshift.core.report import print_rich_report, result_to_json, write_markdown_report
from semshift.core.semantic_diff import compare_files as compare_files_api
from semshift.core.semantic_diff import compare_text as compare_text_api
from semshift.utils.scoring import label_meets

app = typer.Typer(
    name="semshift",
    help="Git diff for meaning. Detect semantic drift, claim changes, tone shifts, and risk shifts.",
    no_args_is_help=True,
)
console = Console()

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
        help="SentenceTransformers model name. Use 'tfidf' for deterministic local fallback.",
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


@app.command()
def compare(
    old: OldFileArgument,
    new: NewFileArgument,
    mode: ModeOption = "default",
    model: ModelOption = DEFAULT_MODEL,
    json_output: JsonOption = False,
    fail_on: FailOnOption = None,
    report: ReportOption = None,
    top: TopOption = 5,
) -> None:
    """Compare two files for meaning-level drift."""
    try:
        result = compare_files_api(old, new, mode=mode, model=model)
    except (FileLoadError, OSError, ValueError) as exc:
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
) -> None:
    """Compare two raw strings for meaning-level drift."""
    try:
        result = compare_text_api(old=old, new=new, mode=mode, model=model)
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
