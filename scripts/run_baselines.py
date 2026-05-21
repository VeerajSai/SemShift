"""Run simple starter baselines for SemShift benchmark comparisons."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from semshift.core.claim_extractor import compare_claims
from semshift.core.risk_analyzer import analyze_risk, risk_score

try:
    from scripts.evaluate_benchmark import HIGH_RISK_LABELS, BenchmarkExample, load_examples
except ModuleNotFoundError:  # pragma: no cover - used when executed as a file
    from evaluate_benchmark import HIGH_RISK_LABELS, BenchmarkExample, load_examples

CONSOLE = Console()
Baseline = Callable[[BenchmarkExample], str]


def main(argv: list[str] | None = None) -> int:
    """Run baseline labelers against the starter benchmark."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/baseline_results.json"))
    args = parser.parse_args(argv)

    examples = load_examples(args.benchmark)
    baselines: dict[str, Baseline] = {
        "lexical_diff_size": lexical_diff_size_baseline,
        "tfidf_cosine_only": tfidf_cosine_only_baseline,
        "heuristic_only": heuristic_only_baseline,
    }
    results = {name: evaluate_baseline(examples, labeler) for name, labeler in baselines.items()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    render_results(results, args.output)
    return 0


def evaluate_baseline(examples: list[BenchmarkExample], labeler: Baseline) -> dict[str, Any]:
    """Evaluate a baseline labeler."""
    rows = []
    for example in examples:
        predicted = labeler(example)
        rows.append(
            {
                "id": example.id,
                "mode": example.mode,
                "expected_label": example.expected_label,
                "predicted_label": predicted,
            }
        )
    high_expected = [row["expected_label"] in HIGH_RISK_LABELS for row in rows]
    high_predicted = [row["predicted_label"] in HIGH_RISK_LABELS for row in rows]
    tp = sum(
        1
        for expected, predicted in zip(high_expected, high_predicted, strict=True)
        if expected and predicted
    )
    fp = sum(
        1
        for expected, predicted in zip(high_expected, high_predicted, strict=True)
        if not expected and predicted
    )
    fn = sum(
        1
        for expected, predicted in zip(high_expected, high_predicted, strict=True)
        if expected and not predicted
    )
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "accuracy": round(
            sum(1 for row in rows if row["expected_label"] == row["predicted_label"])
            / max(1, len(rows)),
            4,
        ),
        "high_risk": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
        "examples": rows,
    }


def lexical_diff_size_baseline(example: BenchmarkExample) -> str:
    """Label by raw sequence distance only."""
    ratio = SequenceMatcher(a=example.old, b=example.new).ratio()
    return _score_to_label(1.0 - ratio)


def tfidf_cosine_only_baseline(example: BenchmarkExample) -> str:
    """Label by TF-IDF cosine distance without claim/tone/risk rules."""
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    matrix = vectorizer.fit_transform([example.old, example.new])
    similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    return _score_to_label(1.0 - similarity)


def heuristic_only_baseline(example: BenchmarkExample) -> str:
    """Label by claim and mode-risk heuristics without chunk similarity."""
    claims = compare_claims(example.old, example.new)
    flags = analyze_risk(example.old, example.new, example.mode, claims)
    score = max(risk_score(flags), min(1.0, claims.change_count / 8.0))
    return _score_to_label(score)


def render_results(results: dict[str, Any], output_path: Path) -> None:
    """Render baseline results."""
    table = Table(title="Starter Baselines")
    table.add_column("Baseline")
    table.add_column("Accuracy", justify="right")
    table.add_column("High-risk F1", justify="right")
    for name, payload in results.items():
        table.add_row(name, f"{payload['accuracy']:.3f}", f"{payload['high_risk']['f1']:.3f}")
    CONSOLE.print(table)
    CONSOLE.print(f"Wrote baseline results to {output_path}")


def _score_to_label(score: float) -> str:
    if score < 0.20:
        return "low"
    if score < 0.45:
        return "medium"
    if score < 0.70:
        return "high"
    return "critical"


if __name__ == "__main__":
    raise SystemExit(main())
