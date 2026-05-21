# Benchmarks

## Starter Benchmark (self-evaluation, not independent validation)

SemShift includes `benchmarks/semshift_bench_v1.jsonl` as a starter self-evaluation set for regression tracking.

Important guardrails:

- This dataset was created inside the repository.
- These numbers are for regression tracking.
- These numbers are not independent validation.
- Human-labeled outside evaluation is still needed.
- Results should not be used as scientific claims.

Run:

```bash
python scripts/evaluate_benchmark.py benchmarks/semshift_bench_v1.jsonl
python scripts/run_baselines.py benchmarks/semshift_bench_v1.jsonl
```

The SemShift evaluator writes `benchmarks/starter_results.json`. Baselines write `benchmarks/baseline_results.json`.

## Baselines

The baseline script currently includes:

- `lexical_diff_size`: raw sequence distance.
- `tfidf_cosine_only`: TF-IDF cosine distance without claim, tone, or risk rules.
- `heuristic_only`: claim and mode-risk heuristics without chunk similarity.

Optional SentenceTransformers-only and NLI baselines are planned, but they are not defaults because they add model download and CPU costs.
