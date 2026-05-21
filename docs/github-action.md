# GitHub Action

Use SemShift in pull requests to flag likely risky meaning changes.

```yaml
steps:
  - uses: actions/checkout@v5
    with:
      fetch-depth: 0

  - uses: VeerajSai/SemShift@v0.2.0
    with:
      mode: policy
      fail_on: high
      pr_comment: "true"
      paths: "docs/**,prompts/**,**/*.md,**/*.txt"
      exclude_paths: ".github/workflows/**"
      model: tfidf
      report: semshift-report.md
      artifact_name: semshift-policy-report
```

Inputs:

- `files`: comma-separated files or globs. Empty means auto-detect changed supported files.
- `paths`: comma-separated include globs applied to changed or explicit files.
- `exclude_paths`: comma-separated exclude globs. Defaults to `.github/workflows/**`.
- `mode`: `default`, `policy`, `prompt`, `readme`, `research`, or `resume`.
- `fail_on`: `low`, `medium`, `high`, `critical`, or `none` for warn-only mode. Default: `high`.
- `model`: `tfidf`, `lexical`, or an explicit SentenceTransformers model name.
- `report`: Markdown artifact path.
- `artifact_name`: uploaded report artifact name. Default: `semshift-report`.
- `base_ref`: base ref for comparison.
- `pr_comment`: whether to post or update a PR comment.
- `github_token`: token for comments.
- `max_file_size`: maximum bytes read per file.
- `max_chunks`: maximum chunks compared per side.

Fork PRs may not have permission to post comments. The report artifact is still generated, and PR comments link to the workflow run artifacts when available.
