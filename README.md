# SemShift

[![CI](https://github.com/VeerajSai/SemShift/actions/workflows/ci.yml/badge.svg)](https://github.com/VeerajSai/SemShift/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-semshift-orange)](https://pypi.org/project/semshift/)

> **Git diff for meaning.** Detect semantic shifts, claim changes, tone drift, and risk changes in text — local-first, no paid API required.

---

Git tells you *what words changed*. SemShift tells you *what meaning changed*.

When a privacy policy quietly switches from "We **do not** share data" to "We **may** share data with selected partners," git diff shows one line changed. SemShift flags it as **CRITICAL** and explains exactly why.

```
$ semshift compare old_policy.md new_policy.md --mode policy

╭──────────────────────────── SemShift Report ──────────────────────────────╮
│  old_policy.md → new_policy.md                                            │
│  Mode: policy | Backend: tfidf                                            │
╰───────────────────────────────────────────────────────────────────────────╯

Overall semantic drift: 0.71  CRITICAL

Review Summary
- 4 semantically changed chunks
- 5 changed claims
- Risk increased: third-party sharing (critical).

Meaning Changes To Review
 1. Data Sharing — SEMANTICALLY CHANGED (drift: 0.89)
    Old: "We do not share personal data with third parties."
    New: "We may share personal data with selected partners."
    Why: Data-sharing policy changed.

 2. Liability — SEMANTICALLY CHANGED (drift: 0.80)
    Old: "We make reasonable efforts to protect user data."
    New: "We disclaim liability for indirect damages."
    Why: Liability shifted to users.

Risk Flags
- CRITICAL  third-party sharing — changed from no sharing to conditional sharing
- HIGH      longer retention    — 30 days → 180 days
- HIGH      reduced consent     — opt-out language appears removed

Recommended Next Steps
- Hold approval until highlighted meaning changes are reviewed.
- Route policy/privacy risk flags to the responsible legal or trust owner.
- Verify numeric changes (30 → 180 days) against the source of truth.
```

---

## Why SemShift?

Most review tools are literal. They show a sentence changed — not whether the *promise, obligation, or risk* changed. That gap matters in:

| Document | What git diff misses |
|---|---|
| **Privacy policy** | `We do not share` → `We may share with partners` |
| **Research paper** | Accuracy metric quietly inflated from 78% → 95% |
| **System prompt** | Safety rule removed, hidden instruction added |
| **Resume** | `18% latency reduction` → `45% latency reduction` |
| **README** | `experimental` dropped, `guaranteed` added |
| **Terms of service** | Arbitration clause silently inserted |

SemShift gives reviewers a fast local signal for **the parts worth reading carefully** — before approving a PR or signing off on a document.

---

## Features

- **Semantic matching** — aligns chunks by meaning, not line number
- **Claim extraction** — numbers, dates, metrics, modal verbs, strong phrases, policy terms, role/title terms
- **Tone analysis** — cautious → confident, neutral → restrictive, technical → promotional
- **Risk heuristics** — mode-specific flags with severity levels (low / medium / high / critical)
- **6 domain modes** — policy, research, resume, prompt, readme, default
- **Two embedding backends** — TF-IDF (fast, offline, default) or SentenceTransformers (optional, deeper)
- **Multiple output formats** — Rich terminal, JSON, markdown reports
- **GitHub Action** — drop-in CI check with PR comments and artifacts
- **Local-first** — no external API calls, no data leaves your machine

---

## Installation

### Basic — TF-IDF backend (fast, works fully offline)

```bash
pip install semshift
```

### With SentenceTransformers — deeper semantic embeddings (optional)

```bash
pip install "semshift[models]"
```

Then pass a model name:

```bash
semshift compare old.md new.md --model sentence-transformers/all-MiniLM-L6-v2
```

### Development

```bash
git clone https://github.com/VeerajSai/SemShift.git
cd SemShift
pip install -e ".[dev]"
pytest
```

---

## Quick Start

**Compare two files:**

```bash
semshift compare old_policy.md new_policy.md --mode policy
```

**Compare raw text:**

```bash
semshift compare-text \
  "We do not share personal data with third parties." \
  "We may share personal data with selected partners." \
  --mode policy
```

**JSON output (for scripting or CI):**

```bash
semshift compare old.md new.md --json
```

**Generate a markdown report:**

```bash
semshift compare old.md new.md --report report.md --top 10
```

**Fail CI when drift is critical:**

```bash
semshift compare old.md new.md --fail-on critical
```

**List all available modes:**

```bash
semshift modes
```

---

## CLI Reference

```
semshift compare <old> <new> [OPTIONS]
semshift compare-text <old_text> <new_text> [OPTIONS]
semshift modes
```

| Option | Default | Description |
|---|---|---|
| `--mode` | `default` | Review mode: `default`, `policy`, `readme`, `research`, `resume`, `prompt` |
| `--model` | `tfidf` | Embedding backend: `tfidf` (fast, offline) or a SentenceTransformers model name |
| `--json` | off | Machine-readable JSON output |
| `--report <path>` | — | Write a markdown report to disk |
| `--top <n>` | `5` | Number of top meaning changes to show (1–25) |
| `--fail-on <label>` | — | Exit code `1` when drift ≥ label: `low`, `medium`, `high`, `critical` |

---

## Modes

| Mode | Best for | What it watches |
|---|---|---|
| `default` | General text | Generic meaning drift |
| `policy` | Privacy policies, ToS | Data sharing, consent, retention, tracking, liability, arbitration |
| `readme` | README, install docs | Features, limitations, platforms, requirements, pricing, guarantees |
| `research` | Papers, reports | Metrics, datasets, baselines, limitations, conclusions, uncertainty |
| `resume` | Resumes, CVs | Role titles, impact metrics, company names, inflated claims |
| `prompt` | System prompts, instructions | Safety rules, hidden instructions, scope constraints, output format |

---

## Python API

### `compare_files()`

```python
from semshift import compare_files

result = compare_files(
    "old_policy.md",
    "new_policy.md",
    mode="policy",   # optional, default "default"
    model="tfidf",   # optional, default "tfidf"
)

print(result.drift_label)        # "critical"
print(result.overall_score)      # 0.71
print(result.summary)            # list of plain-English bullets

for flag in result.risk_flags:
    print(f"[{flag.severity.upper()}] {flag.category}: {flag.why}")
```

### `compare_text()`

```python
from semshift import compare_text

result = compare_text(
    old="We do not share personal data.",
    new="We may share personal data with partners.",
    mode="policy",
)

for item in result.claim_changes.modified_numbers:
    print(f"Number changed: {item['old']} → {item['new']}")
```

### Result object reference

```python
result.overall_score       # float 0.0–1.0 — magnitude of semantic drift
result.drift_label         # str  — "low", "medium", "high", or "critical"
result.summary             # list[str] — plain-English review bullets
result.chunk_matches       # list[ChunkMatch] — matched, added, removed chunks
result.claim_changes       # ClaimDiff — numbers, modals, phrases, policy terms
result.tone_shift          # ToneShift — from/to label, score, explanation
result.risk_flags          # list[RiskFlag] — severity, category, why
result.recommendations     # list[str] — actionable next steps
result.embedding_backend   # str — "tfidf", "tfidf-fallback", or model name
result.warnings            # list[str] — any warnings (e.g., fallback used)
```

---

## JSON Output

Use `--json` for machine-readable output suitable for CI pipelines or downstream tooling:

```bash
semshift compare old.md new.md --json
```

```json
{
  "files": { "old": "old.md", "new": "new.md" },
  "mode": "policy",
  "overall_score": 0.71,
  "drift_label": "critical",
  "summary": ["4 semantically changed chunks", "5 changed claims"],
  "risk_flags": [
    { "severity": "critical", "category": "third-party sharing", "why": "..." }
  ],
  "recommendations": ["Hold approval until changes are reviewed."],
  "embedding_backend": "tfidf",
  "warnings": []
}
```

---

## GitHub Action

Drop SemShift into any pull request workflow to catch semantic drift automatically.

### Basic setup

```yaml
name: SemShift Check

on:
  pull_request:
    paths:
      - "**/*.md"
      - "**/*.txt"
      - "**/*.yml"

permissions:
  contents: read
  pull-requests: write

jobs:
  semshift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: VeerajSai/SemShift@v1
        with:
          mode: "policy"
          fail_on: "critical"
          pr_comment: "true"
```

### Advanced — specific files

```yaml
- uses: VeerajSai/SemShift@v1
  with:
    files: "docs/PRIVACY.md,README.md,system_prompts/*.txt"
    mode: "policy"
    fail_on: "high"
    pr_comment: "true"
    report: "semshift-analysis.md"
```

### Action inputs

| Input | Default | Description |
|---|---|---|
| `files` | *auto-detect* | Comma-separated files or globs. Empty = auto-detect changed files in the PR. |
| `mode` | `default` | Review mode |
| `fail_on` | `high` | Fail when drift reaches: `low`, `medium`, `high`, `critical` |
| `model` | `tfidf` | Embedding backend |
| `report` | `semshift-report.md` | Path for the markdown report artifact |
| `pr_comment` | `false` | Post or update a PR comment with the drift summary |
| `github_token` | `github.token` | Token for PR comments |

### Action outputs

| Output | Description |
|---|---|
| `report_path` | Path to the generated markdown report |
| `worst_label` | Worst drift label found: `low`, `medium`, `high`, or `critical` |

The action uploads a markdown report as a workflow artifact and can post a summary comment directly on the pull request.

---

## How It Works

SemShift runs a fully local, explainable pipeline — no LLM calls, no black boxes:

```
Input files / text
      │
      ▼
 ┌──────────┐    ┌───────────┐    ┌───────────────────────────┐
 │  Loader  │───▶│  Chunker  │───▶│    Embedding Backend      │
 └──────────┘    └───────────┘    │  TF-IDF (default, fast)   │
                                  │  SentenceTransformers      │
                                  └──────────┬────────────────┘
                                             │  cosine similarity
                                             ▼
                                  ┌──────────────────────────┐
                                  │    Semantic Matcher      │
                                  │    (heading-aware)       │
                                  └──────────┬───────────────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          ▼                  ▼                   ▼
                   ┌────────────┐   ┌──────────────┐   ┌──────────────┐
                   │   Claim    │   │     Risk     │   │    Tone      │
                   │ Extractor  │   │   Analyzer   │   │   Analyzer   │
                   └────────────┘   └──────────────┘   └──────────────┘
                          │                  │                   │
                          └──────────────────┴───────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────────┐
                                  │     Report Generator     │
                                  │  Rich / JSON / Markdown  │
                                  │     GitHub Action        │
                                  └──────────────────────────┘
```

1. **Load** — read supported text files with encoding fallback (UTF-8, UTF-8-sig, CP1252)
2. **Chunk** — split into reviewable units, preserving headings and line ranges
3. **Embed** — vectorize with TF-IDF (no download needed) or SentenceTransformers
4. **Align** — match old chunks to new chunks via cosine similarity; heading-aware pre-alignment for structured documents
5. **Classify** — label each chunk: `unchanged`, `lightly changed`, `semantically changed`, `removed`, or `added`
6. **Extract** — pull out high-signal claims: numbers, dates, modals, strong phrases, policy terms, metrics
7. **Analyze** — apply mode-specific risk heuristics and tone shift detection
8. **Report** — produce Rich terminal output, JSON, markdown report, or GitHub Action summary

---

## Supported File Types

| Extension | Format |
|---|---|
| `.md`, `.rst` | Markdown / reStructuredText |
| `.txt` | Plain text |
| `.yml`, `.yaml` | YAML |
| `.json` | JSON |
| `.py`, `.js`, `.ts` | Source code |

---

## Examples

The `examples/` directory has realistic paired documents for every mode:

```bash
# Policy drift (data sharing, retention, consent)
semshift compare examples/old_policy.md examples/new_policy.md --mode policy

# Terms of service
semshift compare examples/old_terms.md examples/new_terms.md --mode policy

# Research paper (metrics, baselines, limitations)
semshift compare examples/old_research.md examples/new_research.md --mode research

# Resume rewrite (inflated claims, changed titles)
semshift compare examples/old_resume.md examples/new_resume.md --mode resume

# System prompt (safety rules, hidden instructions)
semshift compare examples/old_prompt.txt examples/new_prompt.txt --mode prompt

# README changes (feature claims, requirements, pricing)
semshift compare examples/old_readme.md examples/new_readme.md --mode readme
```

See [`examples/sample_policy_report.md`](examples/sample_policy_report.md) for a full markdown report example.

---

## What SemShift Is Not

- Not a legal opinion or compliance tool
- Not a fact-checker or plagiarism detector
- Not a replacement for human review
- Not dependent on any paid LLM API

**SemShift is a review assistant.** It identifies likely semantic drift and explains why a human should look closely.

---

## Contributing

Contributions are welcome. Most useful:

- Real-world examples where word diff missed a meaningful semantic change
- Improved chunking or matching that stays explainable
- Mode-specific risk heuristics backed by tests
- CLI, markdown, or GitHub Action UX improvements
- Bug reports and edge case fixes

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide — including how to add a new mode and the pull request checklist.

### Development setup

```bash
git clone https://github.com/VeerajSai/SemShift.git
cd SemShift
pip install -e ".[dev]"
```

### Run tests

```bash
pytest          # all tests
pytest -v       # verbose
pytest tests/test_cli.py  # specific file
```

### Lint and format

```bash
ruff check .    # lint
ruff format .   # format
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for what changed in each release.

---

## Security

Report vulnerabilities privately via [GitHub Security Advisories](https://github.com/VeerajSai/SemShift/security/advisories/new).

See [SECURITY.md](SECURITY.md) for the full security policy.

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.

---

## Community

- [Issues](https://github.com/VeerajSai/SemShift/issues) — bug reports and feature requests
- [Discussions](https://github.com/VeerajSai/SemShift/discussions) — questions and ideas
- [Changelog](CHANGELOG.md) — release notes

---

*Built for reviewers, maintainers, and teams that care about meaning — not just words.*
