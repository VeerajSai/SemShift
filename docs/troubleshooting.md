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

Use `actions/checkout@v5` with `fetch-depth: 0`, confirm supported extensions, or pass `files`/`paths` explicitly. Use `exclude_paths: ".github/workflows/**"` if workflow YAML changes should not be reviewed.

## Report Too Long

PR comments are truncated. Open the linked workflow run and download the configured report artifact for the full Markdown report.

## PDF and DOCX Files

PDF and DOCX support is optional. Install the extractors with:

```bash
pip install "semshift[formats]"
```

Without them, comparing a `.pdf` or `.docx` raises a clear error pointing here. Notes:

- Extraction is **best-effort plain text** — layout, styling, and images are dropped.
- Scanned or image-only PDFs have no embedded text and will extract little or nothing.
- These formats are **not** truncated by `--max-file-size`; an oversized file errors instead. Raise `--max-file-size` to read it.
- HTML/`.htm` files need no extra dependency; tags are stripped to plain text using the standard library.
