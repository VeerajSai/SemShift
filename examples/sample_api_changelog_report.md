# SemShift Report

**Files:** `examples\old_api_changelog.md` -> `examples\new_api_changelog.md`
**Mode:** `readme`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.23` **LOW**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 1 semantically changed chunks
- 3 changed claims
- Tone shifted from confident to neutral.

## Score Breakdown

- `overall_semantic_drift`: `0.23`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.38`
- `tone_shift`: `0.17`
- `risk_shift`: `0.00`

## Top Meaning Changes

### 1. Notes

- **Status:** semantically changed
- **Drift:** `0.54`
- **Old:** "- The `/v1/export` endpoint is **deprecated** and will be removed in v4. Migrate to `/v2/export`. - This release is backward compatible. Existing API keys and request formats continue to work. - Rate limits are unchanged at 1000 requests..."
- **New:** "- The `/v1/export` endpoint has been removed. - Rate limits are now 200 requests per minute."
- **Why it matters:** Meaning appears materially changed.

## Claim Signals

- **Modified number:** 2 -> 0
- **Modified number:** 1000 requests -> 200 requests
- **Removed:** entity: Existing API

## Recommended Next Steps

- Low semantic drift detected; spot-check important sections.
- Verify numeric changes against the source of truth.
