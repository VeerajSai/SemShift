# How SemShift Compares

SemShift occupies a specific niche: **deterministic, local-first review of *meaning* changes
in prose**, with domain-aware risk modes and a CI gate. Here's how it relates to the tools you
might otherwise reach for.

| Tool | What it catches | Why it misses prose drift | SemShift's edge |
| --- | --- | --- | --- |
| `git diff` / GitHub diff | Exact line/character edits | No notion of *meaning* or *risk*; a one-word flip ("not") looks like a tiny diff | Scores whether the meaning shifted and why it matters |
| diff-match-patch / text-similarity libs | Character/sequence similarity | No domain modes, no risk rules, no report, no CI gate | Claim/tone/risk analysis + modes + PR gate |
| LLM-as-judge (GPT/Claude review) | Broad qualitative review | Non-deterministic, costs latency/money, sends your text to a provider | Deterministic, reproducible, free, local by default |
| Grammar/style checkers (Grammarly, Vale) | Spelling, grammar, prose style | Blind to policy, prompt, factual, and obligation drift | Targets meaning/risk, not style |
| Policy-as-code (OPA, Conftest) | Rules over *structured* config/JSON | Doesn't reason about free-text prose | Works on prose (policies, prompts, resumes, docs) |

## Why "deterministic + local" matters for a gate

A CI gate must be **reproducible**: the same diff should always produce the same verdict, with
no per-run variance and no dependency on an external API's availability, pricing, or data
policy. That rules out an LLM judge as a hard gate for many teams. SemShift's default backend
is fully deterministic and runs on the CI runner, so `fail_on: high` means the same thing every
time.

## When *not* to use SemShift

- You need ground-truth fact-checking or legal sign-off — SemShift is not authoritative.
- You need to catch every subtle, context-dependent nuance — use it alongside human review.
- Your content is purely structured config — policy-as-code tools fit better.

## Honest positioning

SemShift flags **likely** risky drift and explains why. It is not legal advice, a fact-checker,
or a replacement for human review. See [limitations.md](limitations.md) and [faq.md](faq.md).
