# Launch Checklist

Before a stable release:

- Metadata parses locally: `action.yml` and `pyproject.toml`.
- `python -m pip install -e ".[dev]"` succeeds.
- `ruff check .` and `ruff format --check .` pass.
- `pytest --cov=semshift` passes.
- `python -m build` succeeds.
- `twine check dist/*` passes.
- Starter benchmark results are clearly labeled as self-evaluation.
- README and landing page do not claim legal, factual, or scientific authority.
- GitHub Action examples use `fetch-depth: 0`, `fail_on`, and `pr_comment`.
- PyPI Trusted Publisher is configured by the repository owner before tag publishing.
