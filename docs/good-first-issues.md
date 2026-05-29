# Good First Issues

Well-scoped starting points for new contributors. Each is small, has a clear "done", and
touches a contained part of the codebase. See [CONTRIBUTING.md](../CONTRIBUTING.md) first.

> Maintainers: open these as issues and label them `good first issue` to surface them on GitHub.

## 1. Add an example pair for a new domain
- **Files:** `examples/` (new `old_*.md` / `new_*.md` pair).
- **Why it's good:** no internals needed; teaches the before/after format.
- **Done when:** a realistic risky edit (e.g. an SLA that drops an uptime guarantee) is added and
  `semshift compare examples/old_X.md examples/new_X.md --mode default` flags it.

## 2. Add a focus term to an existing mode
- **Files:** `semshift/core/modes.py` (the relevant `ModeConfig.focus_terms`).
- **Why it's good:** a one-line, well-contained change with an obvious test.
- **Done when:** the new term is added and a test in `tests/test_modes.py` covers it.

## 3. Improve an error message
- **Files:** `semshift/core/loader.py` or `semshift/cli.py`.
- **Why it's good:** small, user-facing polish; reinforces the friendly-error pattern.
- **Done when:** the message is clearer and an existing/added test still asserts the behavior.

## 4. Add a troubleshooting entry
- **Files:** `docs/troubleshooting.md`.
- **Why it's good:** docs-only; great first PR.
- **Done when:** a real gotcha (with the fix) is documented and links resolve.

## 5. Add a loader edge-case test
- **Files:** `tests/test_loader.py`.
- **Why it's good:** learn the test suite without touching production code.
- **Done when:** a new case (e.g. mixed-encoding file, empty HTML) passes.

## 6. Add a chunker edge-case test
- **Files:** `tests/test_chunker.py`.
- **Why it's good:** isolated, high-value coverage on heading/code-block handling.
- **Done when:** a new case (e.g. nested fenced code blocks) passes.

## 7. Document a real-world use case
- **Files:** `docs/use-cases.md`.
- **Why it's good:** docs-only; helps adoption.
- **Done when:** a worked before/after recipe for one mode is added with accurate output.

## 8. Add a benchmark example with notes
- **Files:** `benchmarks/semshift_bench_v1.jsonl`.
- **Why it's good:** grows the regression set; teaches the labeling rubric.
- **Done when:** a new line with `expected_label`, `expected_risk_categories`, and `notes` is added
  and `python scripts/evaluate_benchmark.py benchmarks/semshift_bench_v1.jsonl` still runs.
