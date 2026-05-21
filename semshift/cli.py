"""Command-line interface for semshift."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from semshift import __version__
from semshift.core.embeddings import DEFAULT_MODEL
from semshift.core.loader import DEFAULT_MAX_FILE_SIZE, FileLoadError
from semshift.core.modes import MODES, list_modes
from semshift.core.report import print_rich_report, result_to_json, write_markdown_report
from semshift.core.semantic_diff import DEFAULT_MAX_CHUNKS
from semshift.core.semantic_diff import compare_files as compare_files_api
from semshift.core.semantic_diff import compare_text as compare_text_api
from semshift.utils.scoring import label_meets

app = typer.Typer(
    name="semshift",
    help=(
        "Local-first semantic review assistant. Flags likely drift, claim changes, "
        "tone shifts, and risk changes."
    ),
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
    try:
        result = compare_files_api(
            old,
            new,
            mode=mode,
            model=model,
            max_file_size=max_file_size,
            max_chunks=max_chunks,
        )
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
