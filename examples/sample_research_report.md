# SemShift Report

**Files:** `examples\old_research.md` -> `examples\new_research.md`
**Mode:** `research`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.66` **HIGH**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 2 semantically changed chunks
- 4 changed claims
- Tone shifted from cautious to technical.
- Risk increased: increased metric claim (high).

## Score Breakdown

- `overall_semantic_drift`: `0.66`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.50`
- `tone_shift`: `0.08`
- `risk_shift`: `0.75`

## Top Meaning Changes

### 1. Limitations

- **Status:** semantically changed
- **Drift:** `0.62`
- **Old:** "The study is preliminary. We do not evaluate multilingual datasets, and results may not generalize to long-context tasks."
- **New:** "The method is production-ready for long-context tasks."
- **Why it matters:** Research caveat or limitation was replaced with stronger language.

### 2. Conclusion

- **Status:** semantically changed
- **Drift:** `0.47`
- **Old:** "LensRank suggests that lightweight reranking can improve retrieval quality in narrow documentation domains."
- **New:** "LensRank proves that lightweight reranking delivers state-of-the-art retrieval quality across documentation domains."
- **Why it matters:** Conclusion language became stronger.

### 3. Draft Abstract

- **Status:** lightly changed
- **Drift:** `0.24`
- **Old:** "We evaluate LensRank on the MMLU benchmark and compare against a BM25 baseline. The method improves accuracy from 71.2% to 73.4% on our validation split."
- **New:** "We evaluate LensRank on the GSM8K benchmark and compare against a dense retriever baseline. The method improves accuracy from 71.2% to 79.8% on our validation split."
- **Why it matters:** Research metric, dataset, or baseline claim changed.

## Claim Signals

- **Modified number:** 73.4% -> 79.8%
- **Added:** entity: GSM8K
- **Removed:** entity: BM25
- **Removed:** entity: MMLU

## Risk Flags

- **MEDIUM stronger conclusion:** Conclusion language became stronger.
- **MEDIUM removed uncertainty:** Uncertainty language appears reduced or removed.
- **HIGH increased metric claim:** Metric claim increased (73.4% -&gt; 79.8%).
- **MEDIUM changed dataset/baseline:** Dataset or baseline wording appears changed.

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Verify changed metrics, datasets, baselines, and conclusions before publication.
- Verify numeric changes against the source of truth.
