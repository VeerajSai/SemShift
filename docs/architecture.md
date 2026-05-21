# Architecture

SemShift is a local-first review pipeline for likely semantic drift.

The default flow is:

1. Load supported text files with size and binary safeguards.
2. Split text into reviewable chunks using headings and spacing.
3. Align chunks with lexical TF-IDF similarity by default.
4. Optionally use local SentenceTransformers embeddings when `semshift[models]` is installed.
5. Extract claim-like signals such as numbers, dates, modals, policy terms, and role titles.
6. Analyze tone shifts and mode-specific risk rules.
7. Render Rich terminal output, JSON, Markdown reports, and GitHub Action summaries.

TF-IDF is the default lexical backend, not a true semantic model. Optional embedding models are local semantic embedding backends and may download weights on first use.
