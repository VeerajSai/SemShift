# SemShift Report

**Files:** `examples\old_grant.md` -> `examples\new_grant.md`
**Mode:** `research`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.66` **HIGH**

## Summary

- 1 added meaning chunks
- 1 removed meaning chunks
- 1 semantically changed chunks
- 2 changed claims
- Tone shifted from cautious to technical.
- Risk increased: removed limitation (high).

## Score Breakdown

- `overall_semantic_drift`: `0.66`
- `added_meaning`: `0.50`
- `removed_meaning`: `0.50`
- `claim_change`: `0.25`
- `tone_shift`: `0.17`
- `risk_shift`: `0.75`

## Top Meaning Changes

### 1. Limitations

- **Status:** removed
- **Drift:** `0.75`
- **Old:** "These results are preliminary and based on a single dataset. Further validation on independent benchmarks is needed before drawing conclusions."
- **New:** "[removed]"
- **Why it matters:** Existing meaning was removed.

### 2. Impact

- **Status:** added
- **Drift:** `0.75`
- **Old:** "[added]"
- **New:** "The approach is ready for immediate deployment at scale."
- **Why it matters:** New meaning was added.

### 3. Summary

- **Status:** semantically changed
- **Drift:** `0.67`
- **Old:** "Our preliminary experiments suggest the method may improve detection accuracy. On a small internal sample, accuracy rose from 71% to 78%."
- **New:** "Our method proves state-of-the-art detection accuracy. Accuracy reached 95%, a decisive improvement that establishes the approach as production-ready."
- **Why it matters:** Research metric, dataset, or baseline claim changed.

## Claim Signals

- **Modified number:** 71% -> 95%
- **Removed:** number: 78%

## Risk Flags

- **HIGH removed limitation:** A limitation or caveat appears to have been removed.
- **MEDIUM stronger conclusion:** Conclusion language became stronger.
- **MEDIUM removed uncertainty:** Uncertainty language appears reduced or removed.
- **HIGH increased metric claim:** Metric claim increased (71% -&gt; 95%).
- **MEDIUM changed dataset/baseline:** Dataset or baseline wording appears changed.

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Verify changed metrics, datasets, baselines, and conclusions before publication.
- Verify numeric changes against the source of truth.
