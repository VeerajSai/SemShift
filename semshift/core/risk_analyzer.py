"""Mode-specific risk shift detection."""

from __future__ import annotations

import re
from dataclasses import dataclass

from semshift.core.claim_extractor import ClaimDiff
from semshift.utils.text import normalize_whitespace, token_set

_NEGATED_SALE_RE = re.compile(
    r"\b(?:do not|don't|will not|never|not)\s+(?:sell|monetize)\b", re.IGNORECASE
)
_HIDDEN_INSTR_RE = re.compile(
    r"\b(hidden instruction|ignore previous|system prompt|override (?:developer|previous|prior))\b",
    re.IGNORECASE,
)
_SECRECY_RE = re.compile(
    r"\b(do not reveal|don't reveal|must not reveal|keep secret)\b", re.IGNORECASE
)
_DISCLOSE_RE = re.compile(r"\b(reveal|include|share|expose|disclose|provide)\b", re.IGNORECASE)


@dataclass(frozen=True)
class RiskFlag:
    """A risk-relevant semantic change."""

    mode: str
    category: str
    severity: str
    why: str
    old_text: str = ""
    new_text: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize risk flag."""
        return {
            "mode": self.mode,
            "category": self.category,
            "severity": self.severity,
            "why": self.why,
            "old_text": self.old_text,
            "new_text": self.new_text,
        }


SEVERITY_SCORE = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0,
}


def analyze_risk(
    old_text: str,
    new_text: str,
    mode: str = "default",
    claim_diff: ClaimDiff | None = None,
) -> list[RiskFlag]:
    """Return mode-specific risk flags."""
    mode = mode.lower()
    if mode == "policy":
        return _policy_risks(old_text, new_text)
    if mode == "research":
        return _research_risks(old_text, new_text, claim_diff)
    if mode == "readme":
        return _readme_risks(old_text, new_text)
    if mode == "resume":
        return _resume_risks(old_text, new_text, claim_diff)
    if mode == "prompt":
        return _prompt_risks(old_text, new_text)
    return _default_risks(old_text, new_text, claim_diff)


def risk_score(flags: list[RiskFlag]) -> float:
    """Compute a 0..1 score from risk flags."""
    if not flags:
        return 0.0
    return min(1.0, max(SEVERITY_SCORE.get(flag.severity, 0.25) for flag in flags))


def _policy_risks(old_text: str, new_text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    old = old_text.lower()
    new = new_text.lower()

    if _has(old, r"\b(do not|don't|will not|never)\s+share\b") and (
        _has(
            new,
            r"\b(may|can|will)\s+share\b.*\b(partners?|third[- ]part(?:y|ies)|affiliates?|vendors?)\b",
        )
        or _has(new, r"\bthird[- ]part(?:y|ies)|selected partners?|affiliates?\b")
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="third-party sharing",
                severity="critical",
                why="Text changed from no sharing to possible sharing with partners or third parties.",
                old_text=_snippet(old_text, "share"),
                new_text=_snippet(new_text, "share"),
            )
        )

    old_retention = _retention_days(old)
    new_retention = _retention_days(new)
    if old_retention and new_retention and new_retention > old_retention:
        flags.append(
            RiskFlag(
                mode="policy",
                category="longer retention",
                severity="high",
                why=f"Retention appears longer ({old_retention:g} days -> {new_retention:g} days).",
                old_text=_snippet(old_text, "retain"),
                new_text=_snippet(new_text, "retain"),
            )
        )
    if _has(new, r"\b(indefinitely|as long as necessary|for as long as needed)\b") and not _has(
        old, r"\b(indefinitely|as long as necessary|for as long as needed)\b"
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="indefinite retention",
                severity="critical",
                why="New wording allows indefinite or open-ended retention.",
                new_text=_snippet(new_text, "retention"),
            )
        )

    if _has(old, r"\b(consent|opt out|opt-out|permission|choice|settings)\b") and _has(
        new,
        r"\bwithout (?:your )?consent|no opt[- ]out|required to (?:accept|use)|"
        r"tracking is required|must accept\b",
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="reduced consent",
                severity="high",
                why="Consent or opt-out protection appears reduced.",
                old_text=_snippet(old_text, "consent"),
                new_text=_snippet(new_text, "consent"),
            )
        )

    _sale_pattern = (
        r"\b(sell|sale of|monetize)\b[^.\n]{0,80}\b(data|personal information|profile)\b"
    )
    old_negates_sale = bool(_NEGATED_SALE_RE.search(old_text))
    new_negates_sale = bool(_NEGATED_SALE_RE.search(new_text))
    if (
        _has(new, _sale_pattern)
        and not new_negates_sale
        and (old_negates_sale or not _has(old, _sale_pattern))
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="data sale/monetization",
                severity="critical",
                why="New wording appears to allow selling or monetizing user data.",
                new_text=_snippet(new_text, "sell"),
            )
        )

    if _has(new, r"\b(location|biometric|contacts?|precise location|sensitive)\b") and not _has(
        old, r"\b(location|biometric|contacts?|precise location|sensitive)\b"
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="sensitive data expansion",
                severity="high",
                why="New wording appears to add sensitive data categories.",
                new_text=_snippet(new_text, "sensitive"),
            )
        )

    if _has(
        new, r"\b(track|tracking|monitor|location data|cookies?|analytics identifiers?)\b"
    ) and not _has(
        old, r"\b(track|tracking|monitor|location data|cookies?|analytics identifiers?)\b"
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="expanded tracking",
                severity="medium",
                why="New wording appears to expand tracking or analytics collection.",
                new_text=_snippet(new_text, "track"),
            )
        )

    if _has(new, r"\bmandatory arbitration|binding arbitration|class action waiver\b") and not _has(
        old, r"\bmandatory arbitration|binding arbitration|class action waiver\b"
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="mandatory arbitration",
                severity="high",
                why="New wording adds arbitration or class-action limits.",
                new_text=_snippet(new_text, "arbitration"),
            )
        )

    if _has(
        new, r"\b(limit(?:ed)? liability|not liable|no liability|disclaim(?:s|er|ed)?)\b"
    ) and not _has(
        old, r"\b(limit(?:ed)? liability|not liable|no liability|disclaim(?:s|er|ed)?)\b"
    ):
        flags.append(
            RiskFlag(
                mode="policy",
                category="liability limitation",
                severity="medium",
                why="New wording limits liability or adds a disclaimer.",
                new_text=_snippet(new_text, "liability"),
            )
        )

    old_rights = _has(old, r"\b(delete|access|correct|export|opt out|opt-out|appeal)\b")
    new_rights = _has(new, r"\b(delete|access|correct|export|opt out|opt-out|appeal)\b")
    if old_rights and not new_rights:
        flags.append(
            RiskFlag(
                mode="policy",
                category="user rights removal",
                severity="high",
                why="User access, deletion, opt-out, or appeal language appears removed.",
                old_text=_snippet(old_text, "delete"),
            )
        )
    return flags


def _research_risks(old_text: str, new_text: str, claim_diff: ClaimDiff | None) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    old = old_text.lower()
    new = new_text.lower()

    if _has(
        old, r"\b(limitations?|limited|may fail|might fail|not evaluate|future work)\b"
    ) and not _has(new, r"\b(limitations?|limited|may fail|might fail|not evaluate|future work)\b"):
        flags.append(
            RiskFlag(
                mode="research",
                category="removed limitation",
                severity="high",
                why="A limitation or caveat appears to have been removed.",
                old_text=_snippet(old_text, "limitation"),
            )
        )

    if _has(
        new, r"\b(proves?|demonstrates conclusively|state-of-the-art|sota|guaranteed)\b"
    ) and not _has(
        old, r"\b(proves?|demonstrates conclusively|state-of-the-art|sota|guaranteed)\b"
    ):
        flags.append(
            RiskFlag(
                mode="research",
                category="stronger conclusion",
                severity="medium",
                why="Conclusion language became stronger.",
                new_text=_snippet(new_text, "prove"),
            )
        )

    if _has(old, r"\b(may|might|could|uncertain|suggests|preliminary)\b") and not _has(
        new, r"\b(may|might|could|uncertain|suggests|preliminary)\b"
    ):
        flags.append(
            RiskFlag(
                mode="research",
                category="removed uncertainty",
                severity="medium",
                why="Uncertainty language appears reduced or removed.",
                old_text=_snippet(old_text, "may"),
            )
        )

    if claim_diff:
        for item in claim_diff.modified_numbers:
            old_value = float(item.get("old_value") or 0)
            new_value = float(item.get("new_value") or 0)
            context = str(item.get("context") or "").lower()
            if new_value > old_value and _has(
                context, r"\b(accuracy|f1|precision|recall|score|auc)\b"
            ):
                flags.append(
                    RiskFlag(
                        mode="research",
                        category="increased metric claim",
                        severity="high",
                        why=f"Metric claim increased ({item['old']} -> {item['new']}).",
                    )
                )

    if _dataset_or_baseline_changed(old_text, new_text):
        flags.append(
            RiskFlag(
                mode="research",
                category="changed dataset/baseline",
                severity="medium",
                why="Dataset or baseline wording appears changed.",
            )
        )
    return flags


def _readme_risks(old_text: str, new_text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    old = old_text.lower()
    new = new_text.lower()
    old_versions = _runtime_versions(old)
    new_versions = _runtime_versions(new)

    if old_versions - new_versions or (
        _has(old, r"\b(requires?|requirement|prerequisite|python\s+\d|node\s+\d)\b")
        and not _has(new, r"\b(requires?|requirement|prerequisite|python\s+\d|node\s+\d)\b")
    ):
        flags.append(
            RiskFlag(
                mode="readme",
                category="removed installation requirements",
                severity="medium",
                why="Runtime or prerequisite wording appears removed.",
                old_text=_snippet(old_text, "install"),
            )
        )

    new_restricts_commercial = _has(
        new,
        r"\b(commercial use requires|paid license|pricing|license required|"
        r"enterprise only|subscription|required paid)\b",
    )
    old_allowed_commercial = _has(old, r"\b(free .*commercial|commercial use .*free|mit)\b")
    if new_restricts_commercial and (
        old_allowed_commercial
        or not _has(old, r"\b(paid|pricing|license required|enterprise only|subscription)\b")
    ):
        flags.append(
            RiskFlag(
                mode="readme",
                category="commercial/pricing restriction",
                severity="high",
                why="New wording adds commercial, pricing, or license restrictions.",
                new_text=_snippet(new_text, "commercial"),
            )
        )

    if _has(
        old, r"\b(limitation|limited|does not support|not supported|experimental)\b"
    ) and not _has(new, r"\b(limitation|limited|does not support|not supported|experimental)\b"):
        flags.append(
            RiskFlag(
                mode="readme",
                category="removed limitation",
                severity="medium",
                why="A limitation or support caveat appears removed.",
                old_text=_snippet(old_text, "limitation"),
            )
        )

    if _scope_changed(old_text, new_text):
        flags.append(
            RiskFlag(
                mode="readme",
                category="changed project scope",
                severity="medium",
                why="Project positioning or scope terms changed substantially.",
            )
        )

    if _has(
        new,
        r"\b(guaranteed|always works|never fails|production ready for all|proves?\b[^.\n]{0,40}\b\w+-grade)\b",
    ) and not _has(
        old,
        r"\b(guaranteed|always works|never fails|production ready for all|proves?\b[^.\n]{0,40}\b\w+-grade)\b",
    ):
        flags.append(
            RiskFlag(
                mode="readme",
                category="unsupported guarantee",
                severity="high",
                why="New wording adds a broad guarantee.",
                new_text=_snippet(new_text, "guaranteed"),
            )
        )
    return flags


def _resume_risks(old_text: str, new_text: str, claim_diff: ClaimDiff | None) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if claim_diff and claim_diff.modified_numbers:
        flags.append(
            RiskFlag(
                mode="resume",
                category="changed numbers",
                severity="high",
                why="Resume rewrite changed numeric or impact metrics.",
            )
        )

    old_title = _title_terms(old_text)
    new_title = _title_terms(new_text)
    if old_title and new_title and old_title != new_title:
        flags.append(
            RiskFlag(
                mode="resume",
                category="changed titles",
                severity="high",
                why=f"Role title language changed ({', '.join(old_title)} -> {', '.join(new_title)}).",
            )
        )

    old_entities = _capitalized_entities(old_text)
    new_entities = _capitalized_entities(new_text)
    if old_entities and new_entities and old_entities != new_entities:
        flags.append(
            RiskFlag(
                mode="resume",
                category="changed company/project names",
                severity="medium",
                why="Capitalized organization or project names changed.",
            )
        )

    if (
        _has(new_text, r"\b(led|owned|drove|increased|reduced|scaled)\b")
        and claim_diff
        and claim_diff.modified_numbers
    ):
        flags.append(
            RiskFlag(
                mode="resume",
                category="inflated impact",
                severity="medium",
                why="Impact language and numbers changed together.",
            )
        )

    old_large = set(re.findall(r"\b\d{4,}\b", old_text))
    new_large = set(re.findall(r"\b\d{4,}\b", new_text))
    if new_large - old_large and not old_large:
        flags.append(
            RiskFlag(
                mode="resume",
                category="added impact metric",
                severity="high",
                why="Large quantitative claims added with no prior numbers.",
                new_text=_snippet(new_text, next(iter(new_large - old_large))),
            )
        )
    return flags


def _prompt_risks(old_text: str, new_text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    old = old_text.lower()
    new = new_text.lower()

    if bool(_HIDDEN_INSTR_RE.search(new_text)) and not bool(_HIDDEN_INSTR_RE.search(old_text)):
        flags.append(
            RiskFlag(
                mode="prompt",
                category="added hidden instruction",
                severity="critical",
                why="New prompt appears to add hidden or system-level instruction behavior.",
                new_text=_snippet(new_text, "instruction"),
            )
        )

    if (
        bool(_SECRECY_RE.search(old_text))
        and not bool(_SECRECY_RE.search(new_text))
        and bool(_DISCLOSE_RE.search(new_text))
    ):
        flags.append(
            RiskFlag(
                mode="prompt",
                category="removed secrecy obligation",
                severity="critical",
                why="Old prompt required secrecy; new prompt allows disclosure.",
                old_text=_snippet(old_text, "reveal"),
                new_text=_snippet(new_text, "reveal"),
            )
        )

    _safety_re = (
        r"\b(refuse|unsafe|safety|safe|policy|legal|financial|harmful|disclaimer|must not)\b"
    )
    old_safety = _has(old, _safety_re)
    new_safety = _has(new, _safety_re)
    if old_safety and not new_safety:
        flags.append(
            RiskFlag(
                mode="prompt",
                category="removed safety rule",
                severity="critical",
                why="Safety or refusal language appears removed.",
                old_text=_snippet(old_text, "safe"),
            )
        )

    if _has(
        old,
        r"\b(scope limited|limited to|only use|only answer|supplied document|provided context)\b",
    ) and _has(
        new, r"\b(any request|all requests|without limitation|unrestricted|ignore constraints)\b"
    ):
        flags.append(
            RiskFlag(
                mode="prompt",
                category="removed scope constraint",
                severity="high",
                why="A prompt scope constraint appears replaced by broader behavior.",
                old_text=_snippet(old_text, "limited"),
                new_text=_snippet(new_text, "any request"),
            )
        )

    old_format = _format_terms(old)
    new_format = _format_terms(new)
    if old_format and new_format and old_format != new_format:
        flags.append(
            RiskFlag(
                mode="prompt",
                category="changed output format",
                severity="medium",
                why=f"Output format changed ({', '.join(old_format)} -> {', '.join(new_format)}).",
            )
        )

    if _has(
        new, r"\b(any request|all requests|without limitation|unrestricted|ignore constraints)\b"
    ) and not _has(
        old, r"\b(any request|all requests|without limitation|unrestricted|ignore constraints)\b"
    ):
        flags.append(
            RiskFlag(
                mode="prompt",
                category="expanded allowed behavior",
                severity="high",
                why="New prompt appears to expand allowed behavior or scope.",
                new_text=_snippet(new_text, "any request"),
            )
        )

    old_role = _role_phrase(old)
    new_role = _role_phrase(new)
    if (
        old_role
        and new_role
        and old_role != new_role
        and not _mostly_same_phrase(old_role, new_role)
    ):
        flags.append(
            RiskFlag(
                mode="prompt",
                category="changed role/system instruction",
                severity="high",
                why=f"Role instruction changed ({old_role} -> {new_role}).",
            )
        )
    return flags


def _default_risks(old_text: str, new_text: str, claim_diff: ClaimDiff | None) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    old = old_text.lower()
    new = new_text.lower()
    if _has(old, r"\b(may|might|limited|experimental|not guaranteed)\b") and _has(
        new, r"\b(will|always|guaranteed|never fails)\b"
    ):
        flags.append(
            RiskFlag(
                mode="default",
                category="confidence increase",
                severity="medium",
                why="Cautious language appears replaced by stronger confidence.",
            )
        )
    if claim_diff and claim_diff.modified_numbers:
        flags.append(
            RiskFlag(
                mode="default",
                category="changed numeric claim",
                severity="medium",
                why="Numeric claim values changed.",
            )
        )
    return flags


def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL))


def _retention_days(text: str) -> float | None:
    match = re.search(r"\bretain\w*[^.\n]{0,80}?(\d+(?:\.\d+)?)\s*(day|week|month|year)s?\b", text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit == "week":
        return value * 7
    if unit == "month":
        return value * 30
    if unit == "year":
        return value * 365
    return value


def _snippet(text: str, keyword: str, radius: int = 120) -> str:
    lowered = text.lower()
    index = lowered.find(keyword.lower())
    if index < 0:
        return normalize_whitespace(text[: radius * 2])
    start = max(0, index - radius)
    end = min(len(text), index + len(keyword) + radius)
    return normalize_whitespace(text[start:end])


def _dataset_or_baseline_changed(old_text: str, new_text: str) -> bool:
    old_terms = _research_reference_terms(old_text)
    new_terms = _research_reference_terms(new_text)
    return bool(old_terms or new_terms) and old_terms != new_terms


def _research_reference_terms(text: str) -> set[str]:
    tokens = token_set(text)
    known = {"dataset", "baseline", "imagenet", "mmlu", "gsm8k", "mnli", "squad", "hellaswag"}
    named = {
        normalize_whitespace(match.group(1)).lower()
        for match in re.finditer(
            r"\b(?:dataset|baseline)\s*[:=]?\s*([A-Z][A-Za-z0-9_.-]+)",
            text,
        )
    }
    return {term for term in tokens if term in known} | named


def _runtime_versions(text: str) -> set[str]:
    return {
        f"{match.group(1).lower()} {match.group(2)}"
        for match in re.finditer(
            r"\b(python|node|npm|java|ruby|go)\s*(?:>=|>|=|v)?\s*(\d+(?:\.\d+)*)",
            text,
        )
    }


def _scope_changed(old_text: str, new_text: str) -> bool:
    old_terms = token_set(old_text)
    new_terms = token_set(new_text)
    scope_terms = {"framework", "library", "platform", "service", "enterprise", "local", "cloud"}
    return bool((old_terms ^ new_terms) & scope_terms)


def _title_terms(text: str) -> set[str]:
    return {
        match.group(0).lower()
        for match in re.finditer(
            r"\b(?:intern|junior|senior|staff|principal|lead|manager|director|engineer|scientist|"
            r"architect|analyst|developer|associate|specialist|consultant|researcher|coordinator)\b",
            text,
            flags=re.IGNORECASE,
        )
    }


def _capitalized_entities(text: str) -> set[str]:
    return {
        normalize_whitespace(match.group(0))
        for match in re.finditer(
            r"\b[A-Z][A-Za-z0-9&.+-]+(?:\s+[A-Z][A-Za-z0-9&.+-]+){0,2}\b", text
        )
    }


def _format_terms(text: str) -> set[str]:
    return {term for term in ("json", "markdown", "table", "yaml", "xml", "bullet") if term in text}


def _role_phrase(text: str) -> str:
    match = re.search(r"\byou are (?:an?|the)?\s*([^.\n]{2,80})", text)
    return normalize_whitespace(match.group(1)) if match else ""


def _mostly_same_phrase(old: str, new: str, *, threshold: float = 0.5) -> bool:
    """Return whether two phrases are largely the same (a reword, not a real change).

    A one-word synonym swap ("support" -> "success") is not a role change. Genuine role
    changes share few tokens and fall below the threshold, so they still flag.
    """
    old_tokens = set(old.lower().split())
    new_tokens = set(new.lower().split())
    if not old_tokens or not new_tokens:
        return False
    overlap = len(old_tokens & new_tokens) / len(old_tokens | new_tokens)
    return overlap >= threshold
