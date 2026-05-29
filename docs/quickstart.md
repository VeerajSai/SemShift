# Quickstart

SemShift reviews edited text for **risky meaning changes** — weakened privacy promises,
softened obligations, inflated metrics, dropped safety rules — before you merge, publish,
or submit. It runs locally and deterministically; no data leaves your machine.

## Install

```bash
pip install semshift
```

Optional extras:

```bash
pip install "semshift[models]"    # local SentenceTransformers embeddings
pip install "semshift[formats]"   # read .pdf and .docx files
```

## Compare two files

```bash
semshift compare examples/old_policy.md examples/new_policy.md --mode policy
```

You'll get a drift label (`low` / `medium` / `high` / `critical`), the changed claims and
tone, mode-specific risk flags, and a recommendation.

## Review your own uncommitted edits

`compare-git` diffs your working tree against a git ref (default `HEAD`):

```bash
semshift compare-git docs/privacy.md --mode policy
# or review every changed/untracked supported file:
semshift compare-git --mode policy
```

Add `--fail-on high` to exit non-zero when drift is high or critical — handy in a
pre-commit hook.

## Machine-readable output and reports

```bash
semshift compare old.md new.md --mode policy --json                 # stable JSON
semshift compare old.md new.md --mode policy --report report.md     # Markdown report
```

## Project config

Scaffold a `.semshift.yml` (and an optional GitHub Actions workflow):

```bash
semshift init
```

Config values become defaults for `compare` and `compare-git`; explicit flags always win.

```yaml
# .semshift.yml
mode: policy
model: tfidf
fail_on: high
```

## Gate pull requests (GitHub Action)

See [github-action.md](github-action.md). In short:

```yaml
- uses: VeerajSai/SemShift@v0.2.0
  with:
    mode: policy
    fail_on: high
    pr_comment: "true"
```

## Next steps

- [use-cases.md](use-cases.md) — a worked recipe per mode.
- [comparison.md](comparison.md) — how SemShift differs from git diff, LLM review, and more.
- [faq.md](faq.md) — honest answers about scope and limits.
