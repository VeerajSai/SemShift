# SemShift v0.2.0 alpha — Security, Benchmark, and Trust Update

## 1. Summary

SemShift v0.2.0 alpha is a trust, security, benchmark, and documentation hardening release. It keeps SemShift positioned as a local-first review assistant for likely risky meaning changes, not a legal, factual, or scientific authority.

The included benchmark is a starter self-evaluation set for regression tracking. It is not external scientific validation. SemShift remains an alpha-stage review assistant, not a legal, factual, or scientific authority.

## 2. Security hardening

- Hardened GitHub Action input handling and report path validation.
- Kept Action shell input handling behind environment variables and quoted CLI arguments.
- Confirmed integration subprocess calls use list arguments without `shell=True`.
- Added or retained safeguards for path traversal, oversized files, large PR comments, and Markdown/HTML escaping in generated comments.

## 3. CLI/API changes

- Canonical severity field is `drift_label`.
- Python examples should use `result.drift_label`, `result.summary`, `result.risk_flags`, and `result.to_markdown()`.
- GitHub Action inputs use `fail_on` and `pr_comment`.
- `compare-git`, `semshift init`, config loading, NLI/deep mode, and mode registry splitting remain future work.

## 4. Benchmark updates

- Benchmark accuracy: 71.4% on 84 examples.
- Tolerance accuracy: 83.9%.
- High-risk F1: 88.9%.
- Benign false-critical: 0%.
- Benchmark results are for regression tracking only and are not external validation.

## 5. Test coverage

- Tests: 284 passing.
- Coverage: 84% verified locally with `pytest --cov=semshift`.

## 6. Documentation and landing page updates

- README and landing page now describe SemShift as a v0.2.0 alpha local-first review assistant.
- Documentation clarifies that TF-IDF is a lexical/local deterministic backend.
- Documentation clarifies that SentenceTransformers is an optional local semantic embedding backend that may download model weights on first use.
- Benchmark documentation labels the starter benchmark as self-evaluation, not external validation.

## 7. Known limitations

- SemShift is not legal advice, not a fact-checker, and not a replacement for human review.
- The default TF-IDF backend is lexical and deterministic, not a deep semantic model.
- Optional embedding models add model downloads, CPU cost, and different behavior.
- Starter benchmark data is created inside this repository and still needs external human-labeled validation.
- GitHub Action behavior should be validated in a real public pull request before broad Marketplace promotion.

## 8. Upgrade notes

- Use Python 3.10+.
- Prefer `fail_on` over any older threshold input names.
- Prefer `pr_comment` for pull request comment behavior.
- Update Python callers to use `result.drift_label` for severity.
- Package metadata remains `0.2.0`; do not treat this alpha as a stable v1 release.

## 9. GitHub Action usage

```yaml
name: SemShift

on:
  pull_request:

jobs:
  semshift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: VeerajSai/SemShift@v0.2.0
        with:
          mode: policy
          fail_on: high
          pr_comment: "true"
          model: tfidf
          report: semshift-report.md
```

## 10. PyPI publishing checklist

- Confirm local tests and packaging checks pass.
- Remove generated packaging artifacts before rebuilding: `rm -rf dist build *.egg-info`.
- Run `python -m build`.
- Run `twine check dist/*`.
- Owner publishes with `twine upload dist/*`.

## 11. GitHub release checklist

- Review the full diff manually.
- Wait for GitHub Actions to pass on `main`.
- Tag `v0.2.0` only after CI is green.
- Draft the GitHub release using these notes.
- Verify the public landing page shows `v0.2.0 alpha` and no stale stable-version, old-Python, or old Action input references.

## 12. Old v1.0.1 release repair note

The old v1.0.1 release should be edited in GitHub with a deprecation note:

> Deprecated early release line. Please use v0.2.0 alpha or main. v1.0.1 was an early packaging attempt and is not the recommended release.

Do not create v1.0.2 unless GitHub Marketplace compatibility requires it. If used, v1.0.2 should be described only as a GitHub Action compatibility repair tag; Python package metadata must remain `0.2.0`.
