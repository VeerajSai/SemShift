# Use Cases

A worked recipe for each review mode. Every example ships in [`examples/`](../examples), and
the quoted drift labels are the **real** output of running SemShift on those pairs (see the
matching `examples/sample_*_report.md`).

Pick a mode with `--mode`. Modes tune the risk rules — the core drift/claim/tone signals run
in every mode.

## `policy` — privacy policies, terms, contracts

**When:** a privacy policy, ToS, or contract was edited (often by an LLM "cleanup").
**Watches:** third-party sharing, retention, consent/opt-out, data sale, arbitration,
liability, removed user rights.

```bash
semshift compare examples/old_policy.md examples/new_policy.md --mode policy
```

Result: **CRITICAL** — flags the flip from "we do not share" to "we may share with partners",
plus consent and liability changes. The contract example (`examples/*_contract.md`) is **HIGH**
— it adds mandatory arbitration and a liability disclaimer.

## `prompt` — system prompts and instruction files

**When:** a system/agent prompt changed.
**Watches:** added hidden/system instructions, removed safety rules, removed secrecy, widened
scope ("any request"), changed role or output format.

```bash
semshift compare examples/old_prompt.txt examples/new_prompt.txt --mode prompt
```

Result: **CRITICAL** — a safety/secrecy constraint was removed and scope widened.

## `research` — research drafts and reports

**When:** a paper, report, or grant proposal was edited.
**Watches:** removed limitations, stronger conclusions ("proves", "state-of-the-art"), reduced
uncertainty, increased metric claims, changed datasets/baselines.

```bash
semshift compare examples/old_grant.md examples/new_grant.md --mode research
```

Result: **HIGH** — "preliminary, may improve" became "proves state-of-the-art, production-ready",
and the limitations section was dropped.

## `resume` — resumes and bios

**When:** a resume/bio was rewritten (e.g. by an AI tool).
**Watches:** changed numbers/impact metrics, changed titles, changed company/project names,
newly added large quantitative claims.

```bash
semshift compare examples/old_resume.md examples/new_resume.md --mode resume
```

Result: **HIGH** — inflated metrics and title changes worth verifying against the source of truth.

## `readme` — READMEs and support docs

**When:** a README, changelog, or support doc changed.
**Watches:** removed install requirements, new commercial/pricing restrictions, removed
limitations, changed scope, unsupported guarantees.

```bash
semshift compare examples/old_readme.md examples/new_readme.md --mode readme
```

Result: **HIGH**. Note the API-changelog example (`examples/*_api_changelog.md`) scores **LOW** —
a reminder that subtle removals (a deprecation note, a tightened rate limit) can slip under the
threshold. SemShift surfaces likely risk; it does not replace a human reviewer.

## `default` — any text

**When:** you're not sure which mode fits, or the document is general prose.
**Watches:** drift score, claim changes, tone shift, and generic confidence/numeric risk.

```bash
semshift compare examples/old_terms.md examples/new_terms.md --mode default
```

Result: **MEDIUM**.

## Tips

- Use `compare-git` to review your own uncommitted edits before you push.
- Use `--fail-on high` in CI or a pre-commit hook to block risky changes.
- Use `--json` to pipe results into other tools; `--report` to save a Markdown summary.
