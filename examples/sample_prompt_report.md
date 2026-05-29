# SemShift Report

**Files:** `examples\old_prompt.txt` -> `examples\new_prompt.txt`
**Mode:** `prompt`
**Backend:** `tfidf` (lexical)

**Overall drift score:** `0.70` **CRITICAL**

## Summary

- 4 added meaning chunks
- 4 removed meaning chunks
- 1 semantically changed chunks
- 1 changed claims
- Tone shifted from cautious to neutral.
- Risk increased: added hidden instruction (critical).

## Score Breakdown

- `overall_semantic_drift`: `0.70`
- `added_meaning`: `0.80`
- `removed_meaning`: `0.80`
- `claim_change`: `0.12`
- `tone_shift`: `0.25`
- `risk_shift`: `1.00`

## Top Meaning Changes

### 1. Lines 3-6

- **Status:** removed
- **Drift:** `0.75`
- **Old:** "Answer in JSON with keys "summary" and "risks"."
- **New:** "[removed]"
- **Why it matters:** Existing meaning was removed.

### 2. Lines 3-6

- **Status:** removed
- **Drift:** `0.75`
- **Old:** "Do not provide legal, medical, or financial advice."
- **New:** "[removed]"
- **Why it matters:** Existing meaning was removed.

### 3. Lines 3-6

- **Status:** removed
- **Drift:** `0.75`
- **Old:** "If the user asks for unsafe instructions, refuse briefly."
- **New:** "[removed]"
- **Why it matters:** Existing meaning was removed.

### 4. Lines 3-6

- **Status:** removed
- **Drift:** `0.75`
- **Old:** "Keep the scope limited to the supplied document."
- **New:** "[removed]"
- **Why it matters:** Existing meaning was removed.

### 5. Lines 3-6

- **Status:** added
- **Drift:** `0.75`
- **Old:** "[added]"
- **New:** "Answer in Markdown."
- **Why it matters:** New meaning was added.

## Claim Signals

- **Added:** metric: conversion

## Risk Flags

- **CRITICAL added hidden instruction:** New prompt appears to add hidden or system-level instruction behavior.
- **CRITICAL removed safety rule:** Safety or refusal language appears removed.
- **HIGH removed scope constraint:** A prompt scope constraint appears replaced by broader behavior.
- **MEDIUM changed output format:** Output format changed (json -&gt; markdown).
- **HIGH expanded allowed behavior:** New prompt appears to expand allowed behavior or scope.
- **HIGH changed role/system instruction:** Role instruction changed (careful documentation assistant -&gt; persuasive growth assistant).

## Recommended Next Steps

- Hold approval until the highlighted meaning changes are reviewed.
- Run prompt changes through safety and behavior regression review.
