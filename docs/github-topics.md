# GitHub Repository Metadata

Discoverability checklist for the SemShift repo. These are GitHub **settings** (not files):
set them in the repo's "About" panel and Settings.

## Suggested "About" description

> Catch risky meaning changes Git diff misses. Local-first, deterministic semantic-drift
> review for policies, prompts, resumes, research, and docs — CLI, Python API, and a PR gate.

(Keep it under ~120 characters in the About box; the line above is a slightly longer variant.)

Set the website field to the docs/landing page: `https://semshift-landing.vercel.app/`.

## Suggested topics

| Topic | Why |
| --- | --- |
| `semantic-diff` | The category people search for. |
| `semantic-shift` | Matches the project name and the problem. |
| `policy-as-code` | Reaches the privacy/compliance audience using the `policy` mode. |
| `prompt-engineering` | The `prompt` mode targets system-prompt drift. |
| `ci` | It ships a PR-gate GitHub Action. |
| `pre-commit` | `compare-git` fits a local pre-commit workflow. |
| `llm` | "What did the LLM silently change?" is the core hook. |
| `documentation` | README/docs drift detection. |
| `nlp` | Claim/tone/risk text analysis. |
| `local-first` | Deterministic, no data egress — a key differentiator. |
| `developer-tools` | Broad reach for a dev CLI. |
| `python` | Language facet. |

## Other settings to enable

- **Discussions** — on (the issue chooser links to it).
- **Issues** — on (templates already exist: bug, feature, false-positive, missed-drift).
- **Sponsors** — optional; see `.github/FUNDING.yml`.
- **Social preview image** — upload `assets/demo.svg` rendered to PNG, or a branded card.
- **Releases** — tag releases so the PyPI version and the Action `@vX.Y.Z` ref line up.
