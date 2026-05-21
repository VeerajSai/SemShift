"""Rich, JSON, and markdown reporting."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from semshift.core.semantic_diff import (
    SemanticDiffResult,
    chunk_new_text,
    chunk_old_text,
    chunk_section,
    compact_warning,
    top_meaning_changes,
)
from semshift.utils.text import escape_markdown_text, markdown_code, truncate

LABEL_STYLE = {
    "low": "green",
    "medium": "yellow",
    "high": "bold orange3",
    "critical": "bold red",
}


def result_to_json(result: SemanticDiffResult, *, indent: int = 2) -> str:
    """Serialize a result to JSON."""
    return result.to_json(indent=indent)


def print_rich_report(
    result: SemanticDiffResult,
    console: Console | None = None,
    *,
    top: int = 5,
) -> None:
    """Print a human-readable terminal report with Rich."""
    console = console or Console()
    style = LABEL_STYLE.get(result.drift_label, "white")
    title = Text("SemShift Report", style="bold")
    subtitle = (
        f"{result.old_label} -> {result.new_label}\n"
        f"Mode: {result.mode} | Backend: {result.embedding_backend or 'unknown'} "
        f"({result.embedding_backend_type})"
    )
    console.print(Panel(subtitle, title=title, border_style="cyan"))

    score_text = Text()
    score_text.append("Overall drift score: ", style="bold")
    score_text.append(f"{result.overall_score:.2f} ", style=style)
    score_text.append(result.drift_label.upper(), style=style)
    console.print(score_text)
    console.print()

    console.print("[bold]Review Summary[/bold]")
    for item in result.summary:
        console.print(f"- {item}")
    console.print()

    _print_score_breakdown(result, console)

    changes = top_meaning_changes(result, limit=top)
    if changes:
        table = Table(title="Meaning Changes To Review", show_lines=True)
        table.add_column("#", justify="right", style="dim", width=3)
        table.add_column("Section")
        table.add_column("Drift", justify="right")
        table.add_column("Old")
        table.add_column("New")
        table.add_column("Why it matters")
        for index, match in enumerate(changes, start=1):
            table.add_row(
                str(index),
                chunk_section(match),
                f"{match.drift_score:.2f} {match.status}",
                truncate(match.old_chunk.text if match.old_chunk else "[added]", 100),
                truncate(match.new_chunk.text if match.new_chunk else "[removed]", 100),
                match.why_it_matters,
            )
        console.print(table)
        console.print()

    _print_claim_changes(result, console)
    _print_risk_flags(result, console)

    console.print("[bold]Recommended Next Steps[/bold]")
    for recommendation in result.recommendations:
        console.print(f"- {recommendation}")

    if result.warnings:
        console.print()
        console.print("[bold yellow]Warnings[/bold yellow]")
        for warning in result.warnings:
            console.print(f"- {compact_warning(warning)}")


def write_markdown_report(result: SemanticDiffResult, path: str | Path, *, top: int = 5) -> Path:
    """Write a polished markdown report to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.to_markdown(top=top), encoding="utf-8")
    return output_path


def markdown_report(result: SemanticDiffResult, *, top: int = 5) -> str:
    """Generate a markdown report suitable for PR comments or artifacts."""
    lines = [
        "# SemShift Report",
        "",
        f"**Files:** {markdown_code(result.old_label)} -> {markdown_code(result.new_label)}",
        f"**Mode:** {markdown_code(result.mode)}",
        f"**Backend:** {markdown_code(result.embedding_backend or 'unknown')} ({result.embedding_backend_type})",
        "",
        f"**Overall drift score:** `{result.overall_score:.2f}` **{result.drift_label.upper()}**",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"- {escape_markdown_text(item)}" for item in result.summary)

    lines.extend(["", "## Score Breakdown", ""])
    for key, value in result.scores.to_dict().items():
        lines.append(f"- `{key}`: `{value:.2f}`")

    changes = top_meaning_changes(result, limit=top)
    if changes:
        lines.extend(["", "## Top Meaning Changes", ""])
        for index, match in enumerate(changes, start=1):
            lines.extend(
                [
                    f"### {index}. {escape_markdown_text(chunk_section(match))}",
                    "",
                    f"- **Status:** {match.status}",
                    f"- **Drift:** `{match.drift_score:.2f}`",
                    f"- **Old:** {escape_markdown_text(chunk_old_text(match))}",
                    f"- **New:** {escape_markdown_text(chunk_new_text(match))}",
                    f"- **Why it matters:** {escape_markdown_text(match.why_it_matters)}",
                    "",
                ]
            )

    claim_changes = result.claim_changes
    if claim_changes.change_count:
        lines.extend(["## Claim Signals", ""])
        for item in claim_changes.modified_numbers:
            lines.append(
                f"- **Modified number:** {escape_markdown_text(str(item['old']))} -> "
                f"{escape_markdown_text(str(item['new']))}"
            )
        for item in claim_changes.strengthened_claims:
            lines.append(
                f"- **Strengthened:** {escape_markdown_text(item.get('old', ''))} -> "
                f"{escape_markdown_text(item.get('new', ''))}"
            )
        for item in claim_changes.softened_claims:
            lines.append(
                f"- **Softened:** {escape_markdown_text(item.get('old', ''))} -> "
                f"{escape_markdown_text(item.get('new', ''))}"
            )
        for label, items in (
            ("Added", claim_changes.added_claims),
            ("Removed", claim_changes.removed_claims),
        ):
            visible, hidden_count = _visible_claim_items(items)
            for item in visible:
                lines.append(f"- **{label}:** {escape_markdown_text(item)}")
            if hidden_count:
                lines.append(f"- **{label}:** {hidden_count} lower-signal entity claim(s) hidden")
        lines.append("")

    if result.risk_flags:
        lines.extend(["## Risk Flags", ""])
        for flag in result.risk_flags:
            lines.append(
                f"- **{flag.severity.upper()} {escape_markdown_text(flag.category)}:** "
                f"{escape_markdown_text(flag.why)}"
            )
        lines.append("")

    lines.extend(["## Recommended Next Steps", ""])
    lines.extend(f"- {escape_markdown_text(item)}" for item in result.recommendations)

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {escape_markdown_text(warning)}" for warning in result.warnings)

    return "\n".join(lines).rstrip() + "\n"


def _print_score_breakdown(result: SemanticDiffResult, console: Console) -> None:
    table = Table(title="Score Breakdown", show_header=True)
    table.add_column("Signal")
    table.add_column("Score", justify="right")
    table.add_column("Why it exists")
    explanations = {
        "overall_semantic_drift": "Weighted blend used for the final label.",
        "added_meaning": "Share of new chunks with no strong old match.",
        "removed_meaning": "Share of old chunks with no strong new match.",
        "claim_change": "Numbers, dates, metrics, modals, strong phrases, and policy terms.",
        "tone_shift": "Confidence, caution, promotion, restriction, and risk language.",
        "risk_shift": f"Mode-specific risk flags for {result.mode}.",
    }
    for key, value in result.scores.to_dict().items():
        table.add_row(key.replace("_", " "), f"{value:.2f}", explanations[key])
    console.print(table)
    console.print()


def _print_claim_changes(result: SemanticDiffResult, console: Console) -> None:
    changes = result.claim_changes
    if not changes.change_count:
        return
    console.print("[bold]Claim Signals[/bold]")
    for item in changes.modified_numbers[:8]:
        console.print(f"- Modified number: {item['old']} -> {item['new']}")
    for item in changes.strengthened_claims[:8]:
        console.print(f"- Strengthened: {item.get('old', '')} -> {item.get('new', '')}")
    for item in changes.softened_claims[:8]:
        console.print(f"- Softened: {item.get('old', '')} -> {item.get('new', '')}")
    for label, items in (("Added", changes.added_claims), ("Removed", changes.removed_claims)):
        visible, hidden_count = _visible_claim_items(items)
        for item in visible[:6]:
            console.print(f"- {label}: {item}")
        if hidden_count:
            console.print(f"- {label}: {hidden_count} lower-signal entity claim(s) hidden")
    console.print()


def _print_risk_flags(result: SemanticDiffResult, console: Console) -> None:
    if not result.risk_flags:
        return
    console.print("[bold]Risk Flags[/bold]")
    for flag in result.risk_flags:
        style = LABEL_STYLE.get(flag.severity, "white")
        console.print(f"- [{style}]{flag.severity.upper()}[/{style}] {flag.category}: {flag.why}")
    console.print()


def _visible_claim_items(items: list[str]) -> tuple[list[str], int]:
    visible = [item for item in items if not item.startswith("entity:")]
    hidden_count = len(items) - len(visible)
    if visible:
        return visible, hidden_count
    return items[:3], max(0, len(items) - 3)
