"""Tests for the starter benchmark and evaluation script."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_benchmark import evaluate_examples, load_examples, main

BENCHMARK_PATH = Path("benchmarks/semshift_bench_v1.jsonl")


def test_benchmark_file_parses() -> None:
    examples = load_examples(BENCHMARK_PATH)

    assert len(examples) >= 60
    assert sum(1 for example in examples if example.mode == "policy") >= 10
    assert sum(1 for example in examples if example.mode == "prompt") >= 10
    assert sum(1 for example in examples if example.id.startswith("benign-")) >= 10


def test_eval_metrics_keys_exist() -> None:
    examples = load_examples(BENCHMARK_PATH)[:6]

    results = evaluate_examples(examples, model="tfidf")

    assert "label_accuracy" in results
    assert "macro_f1" in results
    assert "high_risk" in results
    assert "mode_breakdown" in results
    assert "mean_latency_ms" in results["metadata"]


def test_eval_script_writes_starter_results(tmp_path: Path) -> None:
    output = tmp_path / "starter_results.json"

    exit_code = main([str(BENCHMARK_PATH), "--output", str(output)])

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["metadata"]["external_validation"] is False
    assert payload["metadata"]["created_inside_repository"] is True


def test_benign_examples_do_not_all_become_critical() -> None:
    examples = [
        example for example in load_examples(BENCHMARK_PATH) if example.id.startswith("benign-")
    ]

    results = evaluate_examples(examples, model="tfidf")
    predictions = [row["predicted_label"] for row in results["examples"]]

    assert predictions.count("critical") < len(predictions)


def test_known_critical_policy_example_detected() -> None:
    examples = [example for example in load_examples(BENCHMARK_PATH) if example.id == "policy-001"]

    results = evaluate_examples(examples, model="tfidf")

    assert results["examples"][0]["predicted_label"] in {"high", "critical"}


def test_label_accuracy_minimum_threshold() -> None:
    examples = load_examples(BENCHMARK_PATH)
    results = evaluate_examples(examples, model="tfidf")
    assert results["label_accuracy"] >= 0.55, (
        f"Label accuracy {results['label_accuracy']:.3f} fell below 0.55 regression threshold"
    )


def test_benign_examples_never_critical() -> None:
    examples = [
        example for example in load_examples(BENCHMARK_PATH) if example.id.startswith("benign-")
    ]
    results = evaluate_examples(examples, model="tfidf")
    critical = [row for row in results["examples"] if row["predicted_label"] == "critical"]
    assert not critical, f"Benign examples predicted critical: {[r['id'] for r in critical]}"


def test_policy_mode_examples_exist() -> None:
    examples = load_examples(BENCHMARK_PATH)
    assert sum(1 for e in examples if e.mode == "policy") >= 10


def test_prompt_mode_examples_exist() -> None:
    examples = load_examples(BENCHMARK_PATH)
    assert sum(1 for e in examples if e.mode == "prompt") >= 10
