# GitHub Action

Use SemShift in pull requests to flag likely risky meaning changes.

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0

  - uses: VeerajSai/SemShift@v0.2.0
    with:
      mode: policy
      fail_on: high
      pr_comment: "true"
      model: tfidf
      report: semshift-report.md
```

Inputs:

- `files`: comma-separated files or globs. Empty means auto-detect changed supported files.
- `mode`: `default`, `policy`, `prompt`, `readme`, `research`, or `resume`.
- `fail_on`: `low`, `medium`, `high`, or `critical`. Default: `high`.
- `model`: `tfidf`, `lexical`, or an explicit SentenceTransformers model name.
- `report`: Markdown artifact path.
- `base_ref`: base ref for comparison.
- `pr_comment`: whether to post or update a PR comment.
- `github_token`: token for comments.
- `max_file_size`: maximum bytes read per file.
- `max_chunks`: maximum chunks compared per side.

Fork PRs may not have permission to post comments. The report artifact is still generated.
