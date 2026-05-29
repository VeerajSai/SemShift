# Assets for SemShift

Visual assets used in the main README, the docs landing page, and launch material.

## Current assets

| File | What it is | Used by |
| --- | --- | --- |
| `demo.svg` | Hand-authored static terminal "screenshot" of `semshift compare … --mode policy` showing a CRITICAL policy-sharing flip. Renders reliably on GitHub. | README hero |
| `cli-output.svg` | Compact static report card for `semshift compare-git` (working tree vs HEAD). | docs / social |
| `pr-comment.svg` | Mock of the GitHub Action PR comment (summary table + honesty footer), matching `semshift/integrations/github_action.py`. | README GitHub Action section |
| `demo.cast` | asciinema v2 recording of the policy demo, for regenerating a real GIF. | `scripts/record_demo.sh` |

All depicted scores/labels match real SemShift output: the `examples/old_policy.md → examples/new_policy.md` comparison scores **0.70 CRITICAL** with a `third-party sharing` risk flag.

## Why SVG (and not a checked-in GIF)

GitHub renders committed SVGs referenced by relative path in Markdown, and a static SVG is crisp, tiny, and diff-friendly. GitHub's image proxy can strip SVG animation, so `demo.svg` is authored to look right as a *static* frame. For an animated GIF (social posts, Product Hunt, the landing page), regenerate one from the cast:

```bash
./scripts/record_demo.sh        # records demo.cast, then builds demo.gif (needs asciinema + agg)
```

## Adding new assets

- **Format:** SVG for diagrams/screenshots; PNG/GIF only when raster is required. Keep files small.
- **Accuracy:** depicted output must match real SemShift behavior — generate it with `semshift compare …` first.
- **Naming:** lowercase, hyphenated, descriptive (e.g. `resume-drift-example.svg`).
- **Alt text:** always include descriptive alt text when embedding in Markdown.
