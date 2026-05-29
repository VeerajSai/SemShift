# SemShift Report

**Files:** `examples\old_readme.md` -> `examples\new_readme.md`
**Mode:** `readme`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.66` **HIGH**

## Summary

- 0 added meaning chunks
- 1 removed meaning chunks
- 3 semantically changed chunks
- 7 changed claims
- Tone shifted from cautious to confident.
- Risk increased: commercial/pricing restriction (high).

## Score Breakdown

- `overall_semantic_drift`: `0.66`
- `added_meaning`: `0.00`
- `removed_meaning`: `0.20`
- `claim_change`: `0.88`
- `tone_shift`: `0.42`
- `risk_shift`: `0.75`

## Top Meaning Changes

### 1. Installation

- **Status:** removed
- **Drift:** `0.75`
- **Old:** "Requires Python 3.10 or later."
- **New:** "[removed]"
- **Why it matters:** Existing meaning was removed.

### 2. Features

- **Status:** semantically changed
- **Drift:** `0.66`
- **Old:** "- Runs locally with open-source embeddings. - Supports Markdown and text files. - Experimental ranking may produce inaccurate matches."
- **New:** "- Delivers guaranteed accurate semantic search. - Supports Markdown, text files, and enterprise cloud connectors. - Commercial use requires a paid license."
- **Why it matters:** Commercial or licensing terms changed.

### 3. AcmeSearch

- **Status:** semantically changed
- **Drift:** `0.64`
- **Old:** "AcmeSearch is a local-first library for semantic search experiments."
- **New:** "AcmeSearch is an enterprise search platform for production knowledge systems."
- **Why it matters:** Meaning appears materially changed.

### 4. License

- **Status:** semantically changed
- **Drift:** `0.45`
- **Old:** "Free for personal and commercial use under MIT."
- **New:** "Free for personal projects."
- **Why it matters:** Meaning appears materially changed.

## Claim Signals

- **Strengthened:**  -> accurate
- **Strengthened:**  -> guaranteed
- **Added:** strong phrase: accurate
- **Added:** strong phrase: guaranteed
- **Added:** 1 lower-signal entity claim(s) hidden
- **Removed:** entity: Requires Python
- **Removed:** entity: Supports Markdown

## Risk Flags

- **MEDIUM removed installation requirements:** Runtime or prerequisite wording appears removed.
- **HIGH commercial/pricing restriction:** New wording adds commercial, pricing, or license restrictions.
- **MEDIUM removed limitation:** A limitation or support caveat appears removed.
- **MEDIUM changed project scope:** Project positioning or scope terms changed substantially.
- **HIGH unsupported guarantee:** New wording adds a broad guarantee.

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Ask a domain owner to review risk flags.
- Review modal and confidence changes carefully.
