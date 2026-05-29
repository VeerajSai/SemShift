# SemShift Report

**Files:** `examples\old_handbook.md` -> `examples\new_handbook.md`
**Mode:** `policy`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.44` **MEDIUM**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 2 semantically changed chunks
- 6 changed claims
- Tone shifted from cautious to neutral.

## Score Breakdown

- `overall_semantic_drift`: `0.44`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.75`
- `tone_shift`: `0.08`
- `risk_shift`: `0.00`

## Top Meaning Changes

### 1. Remote Work

- **Status:** semantically changed
- **Drift:** `0.79`
- **Old:** "Employees may work remotely up to three days per week with manager approval."
- **New:** "Remote work is no longer guaranteed and is granted only in exceptional cases."
- **Why it matters:** Uncertainty was reduced or confidence increased.

### 2. Parental Leave

- **Status:** semantically changed
- **Drift:** `0.65`
- **Old:** "Employees are entitled to 12 weeks of paid parental leave."
- **New:** "Employees may request unpaid parental leave subject to business needs."
- **Why it matters:** Meaning appears materially changed.

### 3. Paid Time Off

- **Status:** lightly changed
- **Drift:** `0.28`
- **Old:** "Full-time employees accrue 20 days of paid time off per year. Unused days carry over to the following year."
- **New:** "Full-time employees accrue 15 days of paid time off per year. Unused days are forfeited at year end."
- **Why it matters:** Wording changed with similar overall meaning.

## Claim Signals

- **Modified number:** 20 days -> 15 days
- **Strengthened:**  -> guaranteed
- **Added:** strong phrase: guaranteed
- **Added:** 1 lower-signal entity claim(s) hidden
- **Removed:** number: 12 weeks
- **Removed:** 1 lower-signal entity claim(s) hidden

## Recommended Next Steps

- Review highlighted changes before approving.
- Verify numeric changes against the source of truth.
- Review modal and confidence changes carefully.
