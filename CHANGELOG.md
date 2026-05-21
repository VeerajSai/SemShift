# Changelog

All notable changes to SemShift will be documented in this file.

The format follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning once public releases begin.

## [Unreleased]

### Added

- GitHub Action `paths`, `exclude_paths`, `artifact_name`, and `fail_on: none` inputs.
- PR comments and step summaries now include workflow run artifact links when GitHub run metadata is available.

### Changed

- GitHub Action internals and repo workflows now use Node 24-compatible action versions where available.
- Action failure output now emits a clear SemShift drift-detected message before exiting with code 1.

## [0.2.0] - 2026-05-21

### Added

- File-size and chunk limits for CLI, Python API, and GitHub Action paths.
- `SemanticDiffResult.to_json()` and `SemanticDiffResult.to_markdown()`.
- Starter self-evaluation benchmark and baseline scripts.
- Security, CI, release, Dependabot, and pre-commit workflow files.
- Open-source hygiene files including citation metadata, issue templates, and roadmap.
- Documentation for architecture, security, benchmarks, limitations, GitHub Action usage, troubleshooting, and launch readiness.
- Expanded benchmark to 84 examples covering everyday scenarios: API changelogs, contracts, grant proposals, employee handbooks, and benign-but-superficially-different paraphrases.
- `tolerance_accuracy` metric (off-by-one = 0.5 credit) and `benign_false_high_risk_rate` in benchmark evaluation output.
- Per-mode breakdown table in benchmark terminal output.
- Integration test suite (`tests/test_integration.py`) with 8 full-pipeline test cases.
- `latin-1` encoding fallback in file loader for broader compatibility.
- 500 MB upper bound on `--max-file-size` to prevent accidental memory exhaustion.
- Code-block-aware heading detection in markdown chunker.
- Negation context filtering for strong phrases in claim extractor (e.g., "do not guarantee" no longer extracted).
- `"would"` added to modal strength vocabulary at level 2.
- Version number filter in claim extractor (e.g., `Python 3.10` no longer treated as a numeric claim).

### Changed

- Positioned SemShift as a local-first review assistant that flags likely semantic drift.
- Clarified that TF-IDF is the default lexical backend, not a true semantic model.
- Reworked README and docs landing page around v0.2.0 alpha, Python 3.10+, and canonical `drift_label` API examples.
- GitHub Action input interpolation now flows through environment variables before shell execution.
- **Recalibrated drift thresholds**: `low < 0.25` (was 0.20), `medium < 0.515` (was 0.45). Fixes 9 medium-overcall cases and absorbs benign TF-IDF paraphrases.
- Tone analyzer normalization improved for short texts (`max(6, word_count/20)` divisor).
- Removed `"guarantee"` and `"unlimited"` from `RISKY` tone keywords (overlap with `CONFIDENT`); added `"transfer"`, `"disclose"`, `"monetize"`.
- Removed `"best"` from `CONFIDENT` tone keywords (duplicate with `PROMOTIONAL`).
- Added `"disclaimer"` and `"refuse"` to `RESTRICTIVE` tone keywords.
- Number-matching threshold raised from 0.18 to 0.25 to reduce spurious numeric claim matches.
- `fail_on` input description in `action.yml` now explicitly states the default of `"high"`.
- docs/index.html version string updated to `v0.2.0 alpha`.

### Fixed

- Hardened action path handling, model validation, markdown escaping, PR comment truncation, oversized file handling, and binary file rejection.
- **Policy mode (policy-007)**: Data sale detection now recognizes when old text negates the sale (`"do not sell"`) and new text introduces monetization language.
- **Prompt mode (prompt-005)**: Hidden instruction detection restructured to correctly fire when old text had a secrecy obligation that new text removes.
- **Prompt mode (prompt-006)**: Removed `"medical"` from safety keyword pattern; added `"disclaimer"` and `"must not"` so safety removal is reliably detected.
- **Research mode (research-006)**: Pattern updated to `limitations?` so plural `"Limitations"` triggers removed-limitation flag.
- **Resume mode**: Added `analyst`, `developer`, `associate`, `specialist`, `consultant`, `researcher`, `coordinator` to title detection. Added detection for newly-added large quantitative claims.
- **README mode**: Unsupported guarantee pattern extended to catch `"proves X-grade"` style overclaims.
- NaN guard added to semantic score averaging (`np.nanmean` + explicit `isnan` check).
- Markdown chunker no longer fires heading detection inside fenced code blocks.
- Sub-chunk line numbers now distributed proportionally by character position.

## [0.1.0] - 2026-05-14

### Added

- Initial SemShift CLI with `compare`, `compare-text`, JSON output, markdown reports, and fail thresholds.
- Local lexical matching with deterministic TF-IDF and optional SentenceTransformers embeddings.
- Review modes for default, README, policy, research, resume, and prompt workflows.
- Claim extraction for numbers, dates, metrics, modal language, strong phrases, policy/security terms, role/title terms, and meaningful entities.
- Rich terminal reports and PR-ready markdown reports.
- GitHub Action with changed-file detection, glob support, job summaries, artifacts, outputs, and optional PR comments.
- Realistic examples for policy, terms, prompts, resumes, research drafts, and README changes.
- Pytest and Ruff coverage for core diffing, claim extraction, CLI behavior, reports, risk modes, and GitHub Action helpers.
