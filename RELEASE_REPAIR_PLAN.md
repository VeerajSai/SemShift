# SemShift v0.2.0 Alpha Release Repair Plan

## 1. Commit and push

```bash
git add .
git commit -m "Release SemShift v0.2.0 alpha trust and benchmark update"
git push origin main
```

## 2. Wait for GitHub Actions

Wait for GitHub Actions to pass on `main` before tagging or publishing.

## 3. Create tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

## 4. Publish PyPI

```bash
rm -rf dist build *.egg-info
python -m build
twine check dist/*
twine upload dist/*
```

## 5. Verify

```bash
pip install --upgrade semshift
semshift --version
semshift --help
```

## 6. GitHub old v1.0.1 repair

Recommended:

- Edit old v1.0.1 release body.
- Add deprecation note:
  “Deprecated early release line. Please use v0.2.0 alpha or main. v1.0.1 was an early packaging attempt and is not the recommended release.”
- Do not create v1.0.2 unless GitHub Marketplace compatibility requires it.

## 7. If v1 compatibility is required

- v1.0.2 should be described only as a GitHub Action compatibility repair tag.
- Python package metadata must remain 0.2.0.
- Owner must manually move/update v1 tag only after real PR Action validation.

## 8. Real PR Action test

Use this workflow snippet in a test repository or throwaway pull request:

```yaml
name: SemShift PR Test

on:
  pull_request:

jobs:
  semshift:
    runs-on: ubuntu-latest
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

Test text:

Before:

> We do not sell user data.

After:

> We may monetize selected user data with partners.

Expected:

Action installs, finds changed file, generates report, posts clean PR comment, and fails/passes according to `fail_on`.

## 9. Landing deployment checklist

- Deploy `docs/index.html` update.
- Verify public landing has v0.2.0 alpha.
- Verify no stale stable-version, pre-3.10 Python, or old threshold/comment input references.
