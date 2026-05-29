# SemShift Report

**Files:** `examples\old_contract.md` -> `examples\new_contract.md`
**Mode:** `policy`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.66` **HIGH**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 3 semantically changed chunks
- 3 changed claims
- Tone shifted from cautious to cautious.
- Risk increased: mandatory arbitration (high).

## Score Breakdown

- `overall_semantic_drift`: `0.66`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.38`
- `tone_shift`: `0.42`
- `risk_shift`: `0.75`

## Top Meaning Changes

### 1. Termination

- **Status:** semantically changed
- **Drift:** `0.56`
- **Old:** "Either party may terminate with thirty days' written notice. Prepaid fees are refunded on a pro-rata basis."
- **New:** "The provider may terminate at any time without notice. Prepaid fees are non-refundable."
- **Why it matters:** Meaning appears materially changed.

### 2. Disputes

- **Status:** semantically changed
- **Drift:** `0.54`
- **Old:** "Any dispute arising under this agreement may be brought in the courts of the customer's home jurisdiction. Either party may pursue claims individually or as part of a class action."
- **New:** "Any dispute arising under this agreement is subject to mandatory binding arbitration. The customer waives the right to participate in any class action."
- **Why it matters:** Dispute resolution rights changed.

### 3. Liability

- **Status:** semantically changed
- **Drift:** `0.53`
- **Old:** "The provider is responsible for direct damages caused by its negligence, up to the fees paid in the prior twelve months."
- **New:** "The provider disclaims all liability for indirect, incidental, or consequential damages, and is not liable beyond the fees paid in the prior month."
- **Why it matters:** Meaning appears materially changed.

## Claim Signals

- **Added:** policy/security term: arbitration
- **Added:** 1 lower-signal entity claim(s) hidden
- **Removed:** entity: Either

## Risk Flags

- **HIGH mandatory arbitration:** New wording adds arbitration or class-action limits.
- **MEDIUM liability limitation:** New wording limits liability or adds a disclaimer.

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Route policy/privacy risk flags to the responsible legal or trust owner.
