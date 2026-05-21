# Incomplete Work

The current pass completes the security, honesty, landing page, API consistency, tests, benchmark scaffold, CI/security workflow, README/docs, and OSS hygiene priorities. Remaining work:

- `semshift/cli.py`: add `semshift compare-git`.
- `semshift/cli.py`: add `semshift init`.
- `semshift/config.py`: add `.semshift.yml` loading and merge it into CLI/API defaults.
- `tests/conftest.py`: add a reusable temporary git repository fixture for future `compare-git` tests.
- `semshift/embedders/base.py`: promote the current embedding helpers into a formal `BaseEmbedder` protocol and implementation package.
- `semshift/modes/`: split mode metadata/rules into a registry package once the mode API stabilizes.
- `scripts/evaluate_benchmark.py`: add optional SentenceTransformer-only and NLI/deep baselines when optional dependencies are installed.
- `.github/workflows/ci.yml`: add macOS and Windows jobs after runtime cost is acceptable.
- `docs/github-action.md`: add screenshots or real PR examples after the owner validates the action in a public pull request.
