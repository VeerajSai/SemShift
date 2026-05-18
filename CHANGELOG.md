# Changelog

All notable changes to SemShift will be documented in this file.

The format follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning once public releases begin.

## [0.1.0] - 2026-05-14

### Added

- Initial SemShift CLI with `compare`, `compare-text`, JSON output, markdown reports, and fail thresholds.
- Local semantic matching with SentenceTransformers and deterministic TF-IDF fallback.
- Review modes for default, README, policy, research, resume, and prompt workflows.
- Claim extraction for numbers, dates, metrics, modal language, strong phrases, policy/security terms, role/title terms, and meaningful entities.
- Rich terminal reports and PR-ready markdown reports.
- GitHub Action with changed-file detection, glob support, job summaries, artifacts, outputs, and optional PR comments.
- Realistic examples for policy, terms, prompts, resumes, research drafts, and README changes.
- Pytest and Ruff coverage for core diffing, claim extraction, CLI behavior, reports, risk modes, and GitHub Action helpers.

