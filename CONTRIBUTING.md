# Contributing

Thanks for helping SemShift become a trustworthy open-source review tool.

## Setup

```bash
python -m pip install -e ".[dev]"
```

Optional local embedding models:

```bash
python -m pip install -e ".[dev-models]"
```

## Tests And Quality

```bash
ruff check .
ruff format --check .
pytest
```

Run coverage when changing shared behavior:

```bash
pytest --cov=semshift
```

## Benchmark Eval

The starter benchmark is self-evaluation only.

```bash
python scripts/evaluate_benchmark.py benchmarks/semshift_bench_v1.jsonl
python scripts/run_baselines.py benchmarks/semshift_bench_v1.jsonl
```

Do not market starter benchmark numbers as independent validation.

## Adding Or Updating A Mode

1. Update `semshift/core/modes.py`.
2. Add conservative risk rules in `semshift/core/risk_analyzer.py`.
3. Add tests for true positives and benign paraphrases.
4. Add benchmark examples with notes.
5. Document mode maturity as stable or experimental.

See `docs/adding-a-mode.md`.

## Coding Standards

- Keep new Python code fully typed.
- Prefer existing project patterns over new abstractions.
- Use Rich console output in CLI-facing code.
- Do not add bare `print()` calls to CLI paths.
- Keep TF-IDF wording honest: lexical backend, not a true semantic model.
- Use `drift_label` as the canonical severity field.

## Security-Sensitive Changes

For path handling, shell execution, model loading, PR comments, or report rendering:

- avoid `shell=True`
- treat file names as data
- constrain action paths to the repo root
- escape untrusted Markdown/HTML
- add tests for unusual paths and long output
- document any remaining risk
