# Contributing

Thanks for helping make SemShift sharper.

SemShift works best when its heuristics are transparent, testable, and grounded in real review workflows. A good contribution usually does one of these:

- adds a realistic example where word diff misses meaning drift
- improves chunking or matching while preserving explainability
- adds a mode-specific risk heuristic with tests
- improves CLI, markdown, or GitHub Action UX
- reduces noisy false positives

## Development Setup

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## Pull Request Guidelines

- Keep changes focused.
- Add or update tests for behavior changes.
- Prefer transparent heuristics over opaque magic.
- Avoid paid API requirements for default workflows.
- Include before/after examples when changing reports or CLI output.

## Heuristic Guidelines

Good SemShift flags should answer:

- What changed?
- Why might it matter?
- Which human reviewer should look at it?

Avoid adding broad keyword rules that create noisy output without a clear review action.

