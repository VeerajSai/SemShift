# FAQ

## Is this "semantic" or just lexical?

By default, **lexical**. The default `tfidf` backend is a deterministic TF-IDF model — it is
not a true semantic model. SemShift's real strength is the combination of chunk alignment,
claim extraction, tone signals, and **mode-specific risk rules**. You can opt into local
SentenceTransformers embeddings with `pip install "semshift[models]"` and `--model
sentence-transformers/all-MiniLM-L6-v2`, but that still isn't a guarantee of understanding.

## Does my data leave my machine?

No. SemShift runs locally and makes no network calls to analyze your text. The only exception
is optional embedding models, which may **download model weights** from Hugging Face on first
use; your document text is still processed locally. The GitHub Action runs on your CI runner.

## Will it catch every risky change?

No. Expect both **false negatives** (subtle, context-dependent changes it misses) and
**false positives** (harmless paraphrases it flags). SemShift surfaces changes worth a human's
attention; the human decides. See [limitations.md](limitations.md).

## How is this different from an LLM reviewer?

An LLM judge gives broad qualitative review but is non-deterministic, costs money/latency, and
sends your text to a provider. SemShift is **deterministic, reproducible, free, and local** —
the same input always yields the same result, which is what you want for a CI gate. See
[comparison.md](comparison.md).

## Can I use it in CI?

Yes. Use the [GitHub Action](github-action.md) with `fail_on: high` to gate pull requests, or
`semshift compare-git --fail-on high` in a local pre-commit hook.

## What file formats are supported?

Out of the box: `.txt`, `.md`, `.rst`, `.json`, `.yaml`, `.yml`, `.py`, `.js`, `.ts`, and HTML.
With `pip install "semshift[formats]"`: `.pdf` and `.docx` (best-effort plain-text extraction).

## Is the benchmark validated?

No. The bundled benchmark is **self-evaluation created inside the repository** for regression
tracking — it is not independent validation. See [benchmarks.md](benchmarks.md).

## What do the drift labels mean?

`low` < `medium` < `high` < `critical`, derived from a weighted blend of semantic drift, claim
changes, tone shift, and mode-specific risk. Use `--fail-on <label>` to fail at or above a level.

## It flagged a harmless change. What now?

That's expected sometimes. Lower the sensitivity by switching to `--mode default`, raise your
`--fail-on` threshold, or open a [false-positive report](https://github.com/VeerajSai/SemShift/issues/new?template=false_positive.yml)
so the rules can improve.
