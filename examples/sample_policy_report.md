# SemShift Report

**Files:** `examples\old_policy.md` -> `examples\new_policy.md`
**Mode:** `policy`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.70` **CRITICAL**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 4 semantically changed chunks
- 5 changed claims
- Tone shifted from risky to restrictive.
- Risk increased: third-party sharing (critical).

## Score Breakdown

- `overall_semantic_drift`: `0.70`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.62`
- `tone_shift`: `0.50`
- `risk_shift`: `1.00`

## Top Meaning Changes

### 1. Liability

- **Status:** semantically changed
- **Drift:** `0.80`
- **Old:** "We make reasonable efforts to protect user data and will notify users of material incidents."
- **New:** "We disclaim liability for indirect damages. Disputes are subject to mandatory arbitration."
- **Why it matters:** Dispute resolution rights changed.

### 2. Consent

- **Status:** semantically changed
- **Drift:** `0.69`
- **Old:** "Users may opt out of analytics tracking at any time from account settings."
- **New:** "Analytics tracking is required to use the service."
- **Why it matters:** User choice or consent language became more restrictive.

### 3. Data Sharing

- **Status:** semantically changed
- **Drift:** `0.52`
- **Old:** "We do not share personal data with third parties. Customer data is used only to provide the service."
- **New:** "We may share personal data with selected partners and vendors to improve the service."
- **Why it matters:** Data-sharing policy changed.

## Claim Signals

- **Modified number:** 30 days -> 180 days
- **Added:** policy/security term: arbitration
- **Added:** policy/security term: selected partners
- **Removed:** policy/security term: opt out
- **Removed:** policy/security term: third parties

## Risk Flags

- **CRITICAL third-party sharing:** Text changed from no sharing to possible sharing with partners or third parties.
- **HIGH longer retention:** Retention appears longer (30 days -&gt; 180 days).
- **CRITICAL indefinite retention:** New wording allows indefinite or open-ended retention.
- **HIGH reduced consent:** Consent or opt-out protection appears reduced.
- **HIGH mandatory arbitration:** New wording adds arbitration or class-action limits.
- **MEDIUM liability limitation:** New wording limits liability or adds a disclaimer.
- **HIGH user rights removal:** User access, deletion, opt-out, or appeal language appears removed.

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Route policy/privacy risk flags to the responsible legal or trust owner.
- Verify numeric changes against the source of truth.
