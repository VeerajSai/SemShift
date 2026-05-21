"""Evaluate SemShift on the starter self-evaluation benchmark."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from semshift import compare_text

LABELS = ("low", "medium", "high", "critical")
HIGH_RISK_LABELS = {"high", "critical"}
LABEL_ORDER_MAP = {"low": 0, "medium": 1, "high": 2, "critical": 3}
CONSOLE = Console()


@dataclass(frozen=True)
class BenchmarkExample:
    """One starter benchmark row."""

    id: str
    mode: str
    old: str
    new: str
    expected_label: str
    expected_risk_categories: tuple[str, ...]
    notes: str


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark evaluation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--model", default="tfidf")
    parser.add_argument("--output", type=Path, default=Path("benchmarks/starter_results.json"))
    args = parser.parse_args(argv)

    examples = load_examples(args.benchmark)
    results = evaluate_examples(examples, model=args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    render_results(results, args.output)
    return 0


def load_examples(path: Path) -> list[BenchmarkExample]:
    """Load benchmark examples from JSONL."""
    examples: list[BenchmarkExample] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        examples.append(
            BenchmarkExample(
                id=str(payload["id"]),
                mode=str(payload["mode"]),
                old=str(payload["old"]),
                new=str(payload["new"]),
                expected_label=str(payload["expected_label"]),
                expected_risk_categories=tuple(payload.get("expected_risk_categories", [])),
                notes=str(payload.get("notes", "")),
            )
        )
        if examples[-1].expected_label not in LABELS:
            raise ValueError(
                f"Invalid expected_label on line {line_number}: {examples[-1].expected_label}"
            )
    return examples


def evaluate_examples(examples: list[BenchmarkExample], *, model: str) -> dict[str, Any]:
    """Evaluate examples and return stable JSON metrics."""
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    latencies: list[float] = []

    for example in examples:
        item_start = time.perf_counter()
        result = compare_text(
            old=example.old,
            new=example.new,
            mode=example.mode,
            model=model,
            old_label=f"{example.id}:old",
            new_label=f"{example.id}:new",
        )
        latency_ms = (time.perf_counter() - item_start) * 1000
        latencies.append(latency_ms)
        rows.append(
            {
                "id": example.id,
                "mode": example.mode,
                "expected_label": example.expected_label,
                "predicted_label": result.drift_label,
                "expected_high_risk": example.expected_label in HIGH_RISK_LABELS,
                "predicted_high_risk": result.drift_label in HIGH_RISK_LABELS,
                "expected_risk_categories": list(example.expected_risk_categories),
                "predicted_risk_categories": [flag.category for flag in result.risk_flags],
                "latency_ms": round(latency_ms, 3),
            }
        )

    labels_expected = [row["expected_label"] for row in rows]
    labels_predicted = [row["predicted_label"] for row in rows]
    high_expected = [bool(row["expected_high_risk"]) for row in rows]
    high_predicted = [bool(row["predicted_high_risk"]) for row in rows]
    benign_rows = [row for row in rows if row["id"].startswith("benign-")]
    benign_critical = sum(1 for row in benign_rows if row["predicted_label"] == "critical")
    benign_high_or_critical = sum(
        1 for row in benign_rows if row["predicted_label"] in HIGH_RISK_LABELS
    )

    return {
        "metadata": {
            "benchmark": "semshift_bench_v1",
            "model": model,
            "example_count": len(rows),
            "created_inside_repository": True,
            "external_validation": False,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "mean_latency_ms": round(sum(latencies) / max(1, len(latencies)), 3),
        },
        "label_accuracy": round(_accuracy(labels_expected, labels_predicted), 4),
        "tolerance_accuracy": round(_tolerance_accuracy(labels_expected, labels_predicted), 4),
        "macro_f1": round(_macro_f1(labels_expected, labels_predicted), 4),
        "per_label_metrics": {
            label: _binary_metrics(
                [e == label for e in labels_expected],
                [p == label for p in labels_predicted],
            )
            for label in LABELS
        },
        "high_risk": _binary_metrics(high_expected, high_predicted),
        "benign_false_critical_rate": round(benign_critical / max(1, len(benign_rows)), 4),
        "benign_false_high_risk_rate": round(benign_high_or_critical / max(1, len(benign_rows)), 4),
        "mode_breakdown": _mode_breakdown(rows),
        "label_counts": {
            "expected": dict(Counter(labels_expected)),
            "predicted": dict(Counter(labels_predicted)),
        },
        "examples": rows,
    }


def render_results(results: dict[str, Any], output_path: Path) -> None:
    """Render a compact terminal summary with Rich."""
    table = Table(title="Starter Benchmark (self-evaluation, not external validation)")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("examples", str(results["metadata"]["example_count"]))
    table.add_row("label accuracy", f"{results['label_accuracy']:.3f}")
    table.add_row("tolerance accuracy", f"{results['tolerance_accuracy']:.3f}")
    table.add_row("macro F1", f"{results['macro_f1']:.3f}")
    table.add_row("high-risk F1", f"{results['high_risk']['f1']:.3f}")
    table.add_row("benign false critical rate", f"{results['benign_false_critical_rate']:.3f}")
    table.add_row("benign false high-risk rate", f"{results['benign_false_high_risk_rate']:.3f}")
    table.add_row("mean latency ms", f"{results['metadata']['mean_latency_ms']:.1f}")
    CONSOLE.print(table)

    mode_table = Table(title="Per-Mode Breakdown")
    mode_table.add_column("Mode")
    mode_table.add_column("Count", justify="right")
    mode_table.add_column("Label Accuracy", justify="right")
    for mode, stats in sorted(results["mode_breakdown"].items()):
        mode_table.add_row(mode, str(stats["count"]), f"{stats['label_accuracy']:.3f}")
    CONSOLE.print(mode_table)
    CONSOLE.print(f"Wrote starter self-evaluation results to {output_path}")


def _accuracy(expected: list[str], predicted: list[str]) -> float:
    return sum(1 for left, right in zip(expected, predicted, strict=True) if left == right) / max(
        1, len(expected)
    )


def _tolerance_accuracy(expected: list[str], predicted: list[str]) -> float:
    total = 0.0
    for e, p in zip(expected, predicted, strict=True):
        if e == p:
            total += 1.0
        elif abs(LABEL_ORDER_MAP[e] - LABEL_ORDER_MAP[p]) == 1:
            total += 0.5
    return round(total / max(1, len(expected)), 4)


def _macro_f1(expected: list[str], predicted: list[str]) -> float:
    return sum(_label_f1(expected, predicted, label) for label in LABELS) / len(LABELS)


def _label_f1(expected: list[str], predicted: list[str], label: str) -> float:
    expected_binary = [item == label for item in expected]
    predicted_binary = [item == label for item in predicted]
    return _binary_metrics(expected_binary, predicted_binary)["f1"]


def _binary_metrics(expected: list[bool], predicted: list[bool]) -> dict[str, float]:
    tp = sum(1 for left, right in zip(expected, predicted, strict=True) if left and right)
    fp = sum(1 for left, right in zip(expected, predicted, strict=True) if not left and right)
    fn = sum(1 for left, right in zip(expected, predicted, strict=True) if left and not right)
    tn = sum(1 for left, right in zip(expected, predicted, strict=True) if not left and not right)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
    }


def _mode_breakdown(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_mode[str(row["mode"])].append(row)
    return {
        mode: {
            "count": len(items),
            "label_accuracy": round(
                _accuracy(
                    [str(item["expected_label"]) for item in items],
                    [str(item["predicted_label"]) for item in items],
                ),
                4,
            ),
        }
        for mode, items in sorted(by_mode.items())
    }


if __name__ == "__main__":
    raise SystemExit(main())
