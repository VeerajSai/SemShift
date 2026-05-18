"""Lightweight heuristic claim extraction and claim comparison."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from semshift.utils.text import normalize_whitespace, token_overlap

NUMBER_RE = re.compile(
    r"(?<!\w)(?:[$])?\d+(?:,\d{3})*(?:\.\d+)?\s*"
    r"(?:%|percent|percentage points|days?|weeks?|months?|years?|ms|milliseconds?"
    r"|seconds?|secs?|minutes?|hours?|users?|customers?|requests?|tokens?|x|times"
    r"|k|m|b|million|billion|gb|mb)?(?!\w)",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
ENTITY_RE = re.compile(r"\b(?:[A-Z][A-Za-z0-9&.+-]+(?:[ \t]+|$)){1,4}")

MODAL_STRENGTH: dict[str, int] = {
    "might": 1,
    "may": 1,
    "could": 1,
    "can": 2,
    "should": 3,
    "must": 4,
    "shall": 4,
    "will": 4,
    "cannot": 4,
    "can't": 4,
    "required": 4,
}
MODAL_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in MODAL_STRENGTH) + r")\b", re.I)

STRONG_PHRASES = (
    "guaranteed",
    "guarantee",
    "always",
    "never",
    "proven",
    "secure",
    "private",
    "anonymous",
    "free",
    "unlimited",
    "best",
    "safe",
    "reliable",
    "accurate",
)
METRIC_TERMS = (
    "accuracy",
    "f1",
    "precision",
    "recall",
    "rmse",
    "mae",
    "latency",
    "cost",
    "revenue",
    "users",
    "retention",
    "conversion",
    "throughput",
    "baseline",
)
QUANTIFIED_METRIC_TERMS = {
    "cost",
    "latency",
    "retention",
    "revenue",
    "throughput",
    "users",
}
POLICY_SECURITY_TERMS = (
    "personal data",
    "third party",
    "third parties",
    "selected partners",
    "consent",
    "opt out",
    "opt-out",
    "retention",
    "data sharing",
    "tracking",
    "liability",
    "arbitration",
    "encryption",
    "security",
    "privacy",
    "user rights",
    "license",
    "commercial use",
)
ROLE_TITLE_TERMS = (
    "intern",
    "junior engineer",
    "senior software engineer",
    "staff software engineer",
    "principal software engineer",
    "software engineer",
    "senior engineer",
    "staff engineer",
    "principal engineer",
    "lead engineer",
    "manager",
    "director",
    "research scientist",
    "data scientist",
    "ml engineer",
    "ai engineer",
    "architect",
)

COMMON_ENTITY_STARTS = {
    "A",
    "An",
    "And",
    "As",
    "For",
    "If",
    "In",
    "It",
    "No",
    "Our",
    "The",
    "This",
    "To",
    "We",
    "With",
    "You",
}
ENTITY_STOPWORDS = {
    "Account",
    "Analytics",
    "Consent",
    "Customer",
    "Customers",
    "Data",
    "Disputes",
    "Features",
    "Installation",
    "Liability",
    "Limitations",
    "Privacy",
    "Retention",
    "Risk",
    "Summary",
    "Users",
}


@dataclass(frozen=True)
class ClaimTerm:
    """A single extracted claim-like token or phrase."""

    value: str
    category: str
    context: str
    numeric_value: float | None = None

    def normalized(self) -> str:
        """Return a stable comparable value."""
        return normalize_whitespace(self.value).lower().strip(".,;:()[]{}")

    def to_dict(self) -> dict[str, object]:
        """Serialize this term."""
        return {
            "value": self.value,
            "category": self.category,
            "context": self.context,
            "numeric_value": self.numeric_value,
        }


@dataclass(frozen=True)
class ExtractedClaims:
    """Claims extracted from text by category."""

    numbers: list[ClaimTerm] = field(default_factory=list)
    dates: list[ClaimTerm] = field(default_factory=list)
    entities: list[ClaimTerm] = field(default_factory=list)
    modals: list[ClaimTerm] = field(default_factory=list)
    strong_phrases: list[ClaimTerm] = field(default_factory=list)
    metrics: list[ClaimTerm] = field(default_factory=list)
    policy_terms: list[ClaimTerm] = field(default_factory=list)
    role_titles: list[ClaimTerm] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[dict[str, object]]]:
        """Serialize extracted claims."""
        return {
            "numbers": [term.to_dict() for term in self.numbers],
            "dates": [term.to_dict() for term in self.dates],
            "entities": [term.to_dict() for term in self.entities],
            "modals": [term.to_dict() for term in self.modals],
            "strong_phrases": [term.to_dict() for term in self.strong_phrases],
            "metrics": [term.to_dict() for term in self.metrics],
            "policy_terms": [term.to_dict() for term in self.policy_terms],
            "role_titles": [term.to_dict() for term in self.role_titles],
        }


@dataclass(frozen=True)
class ClaimDiff:
    """Claim-level changes between two texts."""

    added_claims: list[str] = field(default_factory=list)
    removed_claims: list[str] = field(default_factory=list)
    modified_numbers: list[dict[str, object]] = field(default_factory=list)
    softened_claims: list[dict[str, str]] = field(default_factory=list)
    strengthened_claims: list[dict[str, str]] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        """Return total visible claim changes."""
        return (
            len(self.added_claims)
            + len(self.removed_claims)
            + len(self.modified_numbers)
            + len(self.softened_claims)
            + len(self.strengthened_claims)
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize this claim diff."""
        return {
            "added_claims": self.added_claims,
            "removed_claims": self.removed_claims,
            "modified_numbers": self.modified_numbers,
            "softened_claims": self.softened_claims,
            "strengthened_claims": self.strengthened_claims,
            "change_count": self.change_count,
        }


def extract_claims(text: str) -> ExtractedClaims:
    """Extract lightweight claims from text without paid APIs."""
    clean = text or ""
    return ExtractedClaims(
        numbers=_extract_numbers(clean),
        dates=_extract_regex_terms(clean, DATE_RE, "date"),
        entities=_extract_entities(clean),
        modals=_extract_regex_terms(clean, MODAL_RE, "modal"),
        strong_phrases=_extract_phrase_terms(clean, STRONG_PHRASES, "strong_phrase"),
        metrics=_extract_metric_terms(clean),
        policy_terms=_extract_phrase_terms(clean, POLICY_SECURITY_TERMS, "policy_term"),
        role_titles=_extract_role_title_terms(clean),
    )


def compare_claims(old_text: str, new_text: str) -> ClaimDiff:
    """Compare extracted claims and return meaningful claim deltas."""
    old = extract_claims(old_text)
    new = extract_claims(new_text)

    added_claims: list[str] = []
    removed_claims: list[str] = []
    modified_numbers = _compare_numbers(old.numbers, new.numbers)
    used_old_numbers = {item["old"] for item in modified_numbers}
    used_new_numbers = {item["new"] for item in modified_numbers}

    for category, old_terms, new_terms in (
        ("number", old.numbers, new.numbers),
        ("date", old.dates, new.dates),
        ("strong phrase", old.strong_phrases, new.strong_phrases),
        ("metric", old.metrics, new.metrics),
        ("policy/security term", old.policy_terms, new.policy_terms),
        ("role/title", old.role_titles, new.role_titles),
        ("entity", old.entities, new.entities),
    ):
        old_values = {term.normalized(): term.value for term in old_terms}
        new_values = {term.normalized(): term.value for term in new_terms}
        for value, raw in sorted(new_values.items()):
            if value not in old_values and raw not in used_new_numbers:
                added_claims.append(f"{category}: {raw}")
        for value, raw in sorted(old_values.items()):
            if value not in new_values and raw not in used_old_numbers:
                removed_claims.append(f"{category}: {raw}")

    softened_claims, strengthened_claims = _compare_modal_strength(old.modals, new.modals)

    old_strong = {term.normalized(): term.value for term in old.strong_phrases}
    new_strong = {term.normalized(): term.value for term in new.strong_phrases}
    for value in sorted(new_strong.keys() - old_strong.keys()):
        strengthened_claims.append(
            {"old": "", "new": new_strong[value], "reason": "Strong claim phrase added"}
        )
    for value in sorted(old_strong.keys() - new_strong.keys()):
        softened_claims.append(
            {"old": old_strong[value], "new": "", "reason": "Strong claim phrase removed"}
        )

    return ClaimDiff(
        added_claims=_dedupe(added_claims),
        removed_claims=_dedupe(removed_claims),
        modified_numbers=modified_numbers,
        softened_claims=softened_claims,
        strengthened_claims=strengthened_claims,
    )


def _extract_numbers(text: str) -> list[ClaimTerm]:
    terms = []
    for match in NUMBER_RE.finditer(text):
        raw = normalize_whitespace(match.group(0))
        value = _number_value(raw)
        terms.append(
            ClaimTerm(
                value=raw,
                category="number",
                context=_context_window(text, match.start(), match.end()),
                numeric_value=value,
            )
        )
    return terms


def _extract_regex_terms(text: str, pattern: re.Pattern[str], category: str) -> list[ClaimTerm]:
    terms = []
    for match in pattern.finditer(text):
        terms.append(
            ClaimTerm(
                value=normalize_whitespace(match.group(0)),
                category=category,
                context=_context_window(text, match.start(), match.end()),
            )
        )
    return _unique_terms(terms)


def _extract_phrase_terms(text: str, phrases: tuple[str, ...], category: str) -> list[ClaimTerm]:
    terms: list[ClaimTerm] = []
    for phrase in phrases:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            terms.append(
                ClaimTerm(
                    value=normalize_whitespace(match.group(0)),
                    category=category,
                    context=_context_window(text, match.start(), match.end()),
                )
            )
    return _unique_terms(terms)


def _extract_metric_terms(text: str) -> list[ClaimTerm]:
    terms: list[ClaimTerm] = []
    for phrase in METRIC_TERMS:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            raw = normalize_whitespace(match.group(0))
            if raw.lower() in QUANTIFIED_METRIC_TERMS and not _has_nearby_number(
                text,
                match.start(),
                match.end(),
            ):
                continue
            terms.append(
                ClaimTerm(
                    value=raw,
                    category="metric",
                    context=_context_window(text, match.start(), match.end()),
                )
            )
    return _unique_terms(terms)


def _extract_role_title_terms(text: str) -> list[ClaimTerm]:
    terms: list[ClaimTerm] = []
    for phrase in ROLE_TITLE_TERMS:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            prefix = text[max(0, match.start() - 32) : match.start()].lower()
            if re.search(r"(?:with|by|from)\s+(?:a|an|the)?\s*$", prefix):
                continue
            terms.append(
                ClaimTerm(
                    value=normalize_whitespace(match.group(0)),
                    category="role_title",
                    context=_context_window(text, match.start(), match.end()),
                )
            )
    return _unique_terms(terms)


def _extract_entities(text: str) -> list[ClaimTerm]:
    candidates: list[tuple[str, int, int]] = []
    for match in ENTITY_RE.finditer(text):
        raw = normalize_whitespace(match.group(0))
        if len(raw) < 3:
            continue
        raw = raw.strip(".,:;()[]{}")
        words = raw.split()
        first = raw.split()[0]
        if first in COMMON_ENTITY_STARTS and len(raw.split()) == 1:
            continue
        if raw in ENTITY_STOPWORDS or raw.lower() in {"api", "json", "yaml", "readme"}:
            continue
        if len(words) == 1 and not _is_meaningful_single_entity(raw, text):
            continue
        if len(words) > 1 and any(word in ENTITY_STOPWORDS for word in words):
            continue
        candidates.append((raw, match.start(), match.end()))

    terms: list[ClaimTerm] = []
    for raw, start, end in candidates:
        terms.append(
            ClaimTerm(
                value=raw,
                category="entity",
                context=_context_window(text, start, end),
            )
        )
    return _unique_terms(terms)


def _is_meaningful_single_entity(raw: str, text: str) -> bool:
    if raw.isupper() and len(raw) >= 2:
        return True
    if len(re.findall(rf"\b{re.escape(raw)}\b", text)) >= 2:
        return True
    return bool(
        re.search(
            rf"\b(?:at|from|for|by|inside|within)\s+{re.escape(raw)}\b"
            rf"|\b{re.escape(raw)}\s+"
            r"(?:retains?|uses?|provides?|ships?|builds?|supports?|owns?|operates?)\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def _has_nearby_number(text: str, start: int, end: int, radius: int = 36) -> bool:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return bool(re.search(r"\d", text[left:right]))


def _compare_numbers(
    old_numbers: list[ClaimTerm], new_numbers: list[ClaimTerm]
) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []
    used_new: set[int] = set()
    unchanged_old, unchanged_new = _exact_number_matches(old_numbers, new_numbers)
    for old_index, old_term in enumerate(old_numbers):
        if old_index in unchanged_old:
            continue
        if old_term.numeric_value is None:
            continue
        best_index = -1
        best_score = 0.0
        for index, new_term in enumerate(new_numbers):
            if index in unchanged_new or index in used_new or new_term.numeric_value is None:
                continue
            if old_term.numeric_value == new_term.numeric_value:
                continue
            unit_bonus = 0.2 if _unit(old_term.value) == _unit(new_term.value) else 0.0
            overlap = token_overlap(old_term.context, new_term.context) + unit_bonus
            if overlap > best_score:
                best_score = overlap
                best_index = index
        if best_index >= 0 and best_score >= 0.18:
            new_term = new_numbers[best_index]
            used_new.add(best_index)
            changes.append(
                {
                    "old": old_term.value,
                    "new": new_term.value,
                    "old_value": old_term.numeric_value,
                    "new_value": new_term.numeric_value,
                    "context": normalize_whitespace(old_term.context or new_term.context),
                }
            )
    return changes


def _exact_number_matches(
    old_numbers: list[ClaimTerm],
    new_numbers: list[ClaimTerm],
) -> tuple[set[int], set[int]]:
    unchanged_old: set[int] = set()
    unchanged_new: set[int] = set()
    for old_index, old_term in enumerate(old_numbers):
        if old_term.numeric_value is None:
            continue
        for new_index, new_term in enumerate(new_numbers):
            if new_index in unchanged_new or new_term.numeric_value is None:
                continue
            if old_term.numeric_value == new_term.numeric_value and _unit(old_term.value) == _unit(
                new_term.value
            ):
                unchanged_old.add(old_index)
                unchanged_new.add(new_index)
                break
    return unchanged_old, unchanged_new


def _compare_modal_strength(
    old_modals: list[ClaimTerm], new_modals: list[ClaimTerm]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if not old_modals or not new_modals:
        return [], []

    old_best = max(old_modals, key=lambda term: MODAL_STRENGTH[term.normalized()])
    new_best = max(new_modals, key=lambda term: MODAL_STRENGTH[term.normalized()])
    old_score = MODAL_STRENGTH[old_best.normalized()]
    new_score = MODAL_STRENGTH[new_best.normalized()]
    if new_score > old_score:
        return [], [
            {
                "old": old_best.value,
                "new": new_best.value,
                "reason": "Modal language became stronger",
            }
        ]
    if new_score < old_score:
        return [
            {
                "old": old_best.value,
                "new": new_best.value,
                "reason": "Modal language became softer",
            }
        ], []
    return [], []


def _context_window(text: str, start: int, end: int, radius: int = 90) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return normalize_whitespace(text[left:right])


def _number_value(raw: str) -> float | None:
    match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", raw)
    if not match:
        return None
    value = float(match.group(0).replace(",", ""))
    suffix = raw[match.end() :].strip().lower()
    if suffix in {"k"}:
        return value * 1_000
    if suffix in {"m", "million"}:
        return value * 1_000_000
    if suffix in {"b", "billion"}:
        return value * 1_000_000_000
    return value


def _unit(raw: str) -> str:
    parts = raw.lower().replace("%", " percent").split()
    return parts[-1] if len(parts) > 1 else ""


def _unique_terms(terms: list[ClaimTerm]) -> list[ClaimTerm]:
    seen: set[tuple[str, str]] = set()
    unique: list[ClaimTerm] = []
    for term in terms:
        key = (term.category, term.normalized())
        if key not in seen:
            seen.add(key)
            unique.append(term)
    return unique


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
