# SemShift Report

**Files:** `examples\old_terms.md` -> `examples\new_terms.md`
**Mode:** `default`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.47` **MEDIUM**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 4 semantically changed chunks
- 5 changed claims
- Tone shifted from cautious to cautious.

## Score Breakdown

- `overall_semantic_drift`: `0.47`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.62`
- `tone_shift`: `0.17`
- `risk_shift`: `0.00`

## Top Meaning Changes

### 1. Disputes

- **Status:** semantically changed
- **Drift:** `0.82`
- **Old:** "Users may bring claims in their local court where permitted by law."
- **New:** "All disputes are subject to mandatory arbitration and a class action waiver."
- **Why it matters:** Dispute resolution rights changed.

### 2. Account Rights

- **Status:** semantically changed
- **Drift:** `0.74`
- **Old:** "Users can export workspace data and request deletion at any time."
- **New:** "Workspace export is available for enterprise plans."
- **Why it matters:** Meaning appears materially changed.

### 3. Data Use

- **Status:** semantically changed
- **Drift:** `0.62`
- **Old:** "We do not sell personal data. We share account data only with subprocessors required to provide the service."
- **New:** "We may monetize profile data and share personal data with selected partners for product analytics."
- **Why it matters:** Meaning appears materially changed.

### 4. Retention

- **Status:** semantically changed
- **Drift:** `0.45`
- **Old:** "We retain deleted workspace backups for 30 days."
- **New:** "We retain deleted workspace backups as long as necessary for business purposes."
- **Why it matters:** Meaning appears materially changed.

## Claim Signals

- **Softened:** required -> may
- **Added:** policy/security term: arbitration
- **Added:** policy/security term: selected partners
- **Removed:** number: 30 days
- **Removed:** metric: Users

## Recommended Next Steps

- Review highlighted changes before approving.
- Review modal and confidence changes carefully.
