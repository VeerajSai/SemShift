# SemShift Report

**Files:** `examples\old_resume.md` -> `examples\new_resume.md`
**Mode:** `resume`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.66` **HIGH**

## Summary

- 0 added meaning chunks
- 0 removed meaning chunks
- 1 semantically changed chunks
- 7 changed claims
- Risk increased: changed numbers (high).

## Score Breakdown

- `overall_semantic_drift`: `0.66`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.00`
- `claim_change`: `0.88`
- `tone_shift`: `0.00`
- `risk_shift`: `0.75`

## Top Meaning Changes

### 1. Experience

- **Status:** semantically changed
- **Drift:** `0.45`
- **Old:** "- Reduced API latency by 18% for a patient scheduling service used by 20,000 monthly users. - Built dashboards in Python and SQL to monitor appointment drop-off. - Collaborated with a senior engineer on model evaluation and release checks."
- **New:** "- Reduced API latency by 45% for a patient scheduling platform used by 200,000 monthly users. - Owned executive dashboards in Python and SQL that increased retention by 12%. - Led model evaluation and release checks."
- **Why it matters:** Resume impact metric or factual numeric claim changed.

### 2. Experience

- **Status:** lightly changed
- **Drift:** `0.24`
- **Old:** "Software Engineer, Acme Health"
- **New:** "Senior Software Engineer, Acme Health"
- **Why it matters:** Wording changed with similar overall meaning.

### 3. Skills

- **Status:** lightly changed
- **Drift:** `0.24`
- **Old:** "Python, SQL, FastAPI, PostgreSQL, scikit-learn"
- **New:** "Python, SQL, FastAPI, PostgreSQL, scikit-learn, Kubernetes"
- **Why it matters:** Wording changed with similar overall meaning.

## Claim Signals

- **Modified number:** 18% -> 45%
- **Modified number:** 20,000 -> 200,000
- **Added:** number: 12%
- **Added:** metric: retention
- **Added:** policy/security term: retention
- **Added:** role/title: Senior Software Engineer
- **Added:** 1 lower-signal entity claim(s) hidden

## Risk Flags

- **HIGH changed numbers:** Resume rewrite changed numeric or impact metrics.
- **MEDIUM changed company/project names:** Capitalized organization or project names changed.
- **MEDIUM inflated impact:** Impact language and numbers changed together.

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Verify resume facts against the source of truth before using this rewrite.
- Verify numeric changes against the source of truth.
