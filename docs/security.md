# Security

SemShift is local-first by default. It does not call external APIs during normal `tfidf` comparisons.

Security-relevant behavior:

- GitHub Action inputs are passed through environment variables before shell execution.
- Git and subprocess calls use list arguments with `shell=False`.
- GitHub Action paths are normalized to the repository root.
- Absolute paths and parent traversal are rejected in the action integration.
- Symlinks are allowed only when their resolved target remains inside the repository root.
- Oversized files are truncated with warnings.
- Binary files are rejected.
- PR comments are escaped and truncated, with the full report kept as an artifact.
- Optional embedding models use `trust_remote_code=False`.

SemShift is not a sandbox. Review file globs, model allow-lists, and CI permissions for your repository.
