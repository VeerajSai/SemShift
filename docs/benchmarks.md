# Benchmarks

> **This is self-evaluation, not independent validation.** The dataset was created inside this
> repository by the author. The numbers are useful for catching regressions between versions —
> they are **not** a scientific claim, and human-labeled outside evaluation is still needed.

## The dataset

`benchmarks/semshift_bench_v1.jsonl` is a JSONL set of `old → new` text pairs, each with a
human-assigned `expected_label` (`low` / `medium` / `high` / `critical`), the
`expected_risk_categories`, and a `notes` field explaining the label. It spans all modes
(policy, prompt, research, resume, readme, default) and includes:

- **Risky edits** — weakened privacy promises, removed safety rules, inflated metrics, dropped
  limitations, added arbitration, etc.
- **Benign paraphrases** (`benign-*`) — reworded text with no real meaning change, to measure
  over-firing.
- **A held-out slice** (`heldout-*`) — added later to check the rules generalize beyond the
  cases they were first tuned on.

## Reproduce

```bash
python scripts/evaluate_benchmark.py benchmarks/semshift_bench_v1.jsonl   # SemShift itself
python scripts/run_baselines.py benchmarks/semshift_bench_v1.jsonl        # naive baselines
```

The evaluator writes `benchmarks/starter_results.json` (stable, sorted) and prints the summary,
per-mode breakdown, and a confusion matrix.

## What the metrics mean

| Metric | Meaning | Why it matters |
| --- | --- | --- |
| **label accuracy** | Exact-match rate of predicted vs expected label | Strict; off-by-one counts as wrong |
| **tolerance accuracy** | Off-by-one labels score 0.5 credit | A `high` called `critical` is still useful |
| **high-risk recall** | Of truly high/critical pairs, the share flagged high/critical | **The safety metric** — misses are the real cost of a review gate |
| **high-risk precision** | Of pairs flagged high/critical, the share that truly are | High precision keeps the gate trustworthy (few false alarms) |
| **benign false-high-risk rate** | Share of `benign-*` pairs wrongly flagged high/critical | Over-firing on harmless edits erodes trust fastest |

For a CI gate, **recall and the benign false-high-risk rate matter most**: you want to catch the
dangerous changes without crying wolf on harmless ones.

## Confusion matrix

The evaluator prints an `expected × predicted` matrix. Read the diagonal for correct calls; the
upper triangle is over-calling (predicted more severe than expected), the lower triangle is
under-calling (missed severity). The most common error is benign/low paraphrases landing in
`medium` — they carry no risk flags, so the lexical TF-IDF drift alone nudges them up.

## Known failure modes

- **Benign paraphrase → `medium`.** With the default lexical backend, a heavy reword scores
  meaningful drift even when meaning is unchanged. These rarely reach `high`/`critical` (so they
  don't trip a `fail_on: high` gate), but they hurt exact label accuracy.
- **Subtle structural removals under-flagged.** Dropping a deprecation note or tightening a rate
  limit can score `low` (see the API-changelog example) — real risk the heuristics miss.
- **Resume/policy off-by-one.** Severity is sometimes one level off; `tolerance accuracy` reflects
  that these are still directionally useful.

## Baselines

`scripts/run_baselines.py` compares SemShift against naive baselines (raw lexical diff size,
TF-IDF cosine only, heuristics only) so you can see the contribution of the combined pipeline.
These baselines over-fire badly on benign text — a reminder that the modes and risk rules, not
raw similarity, are what make SemShift usable as a gate.

## A note on versions

Metrics shift as the rules improve. When comparing across versions, regenerate
`starter_results.json` on a clean checkout so the numbers reflect the current code.
