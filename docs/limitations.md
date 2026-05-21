# Limitations

SemShift is a review assistant. It flags likely semantic drift and points reviewers toward risky changes.

It is not:

- legal advice
- a fact-checker
- scientific authority
- a replacement for human review
- proof that meaning did or did not change

Known limitations:

- The default TF-IDF backend is lexical, not a true semantic model.
- Heuristics may miss subtle context-dependent changes.
- Benign paraphrases may be flagged.
- Optional embedding models can download weights and add CPU cost.
- Starter benchmark results are self-evaluation only.
