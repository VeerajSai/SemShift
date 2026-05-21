# Troubleshooting

## Command Not Found

Confirm that the active shell uses the environment where SemShift is installed.

```bash
python -m pip install semshift
python -m semshift --help
```

## Model Import Error

Use the default lexical backend:

```bash
semshift compare old.md new.md --model tfidf
```

Or install optional local embedding dependencies:

```bash
pip install "semshift[models]"
```

## Slow First Run

SentenceTransformers models may download weights and initialize on first use. The default `tfidf` backend avoids that.

## GitHub Action Finds No Files

Use `actions/checkout@v4` with `fetch-depth: 0`, confirm supported extensions, or pass the `files` input explicitly.

## Report Too Long

PR comments are truncated. Open the `semshift-report` artifact for the full Markdown report.
