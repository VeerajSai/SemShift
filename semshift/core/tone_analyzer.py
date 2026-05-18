"""Heuristic tone shift detection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from semshift.utils.scoring import clamp

CAUTIOUS = (
    "may",
    "might",
    "could",
    "possibly",
    "potentially",
    "usually",
    "generally",
    "experimental",
    "limited",
    "uncertain",
    "approximate",
)
CONFIDENT = (
    "will",
    "must",
    "always",
    "never",
    "guaranteed",
    "proven",
    "reliable",
    "accurate",
    "secure",
    "best",
)
PROMOTIONAL = (
    "effortless",
    "powerful",
    "world-class",
    "best",
    "delight",
    "transform",
    "revolutionary",
    "seamless",
    "premium",
)
RESTRICTIVE = (
    "must not",
    "prohibited",
    "forbidden",
    "required",
    "mandatory",
    "cannot",
    "shall not",
    "restricted",
)
TECHNICAL = (
    "api",
    "dataset",
    "model",
    "latency",
    "accuracy",
    "baseline",
    "json",
    "python",
    "cli",
    "embedding",
)
RISKY = (
    "share",
    "track",
    "retain",
    "liability",
    "arbitration",
    "guarantee",
    "unlimited",
    "without consent",
)


@dataclass(frozen=True)
class ToneProfile:
    """Tone classification for one side of a comparison."""

    label: str
    scores: dict[str, float] = field(default_factory=dict)
    features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize profile."""
        return {"label": self.label, "scores": self.scores, "features": self.features}


@dataclass(frozen=True)
class ToneShift:
    """Tone transition between old and new text."""

    from_label: str
    to_label: str
    shift: str
    score: float
    explanation: str

    def to_dict(self) -> dict[str, object]:
        """Serialize shift."""
        return {
            "from": self.from_label,
            "to": self.to_label,
            "shift": self.shift,
            "score": self.score,
            "explanation": self.explanation,
        }


def analyze_tone(text: str) -> ToneProfile:
    """Classify tone using transparent keyword heuristics."""
    lowered = text.lower()
    word_count = max(1, len(re.findall(r"\w+", lowered)))
    raw_scores = {
        "cautious": _keyword_count(lowered, CAUTIOUS),
        "confident": _keyword_count(lowered, CONFIDENT),
        "promotional": _keyword_count(lowered, PROMOTIONAL),
        "restrictive": _keyword_count(lowered, RESTRICTIVE),
        "technical": _keyword_count(lowered, TECHNICAL),
        "risky": _keyword_count(lowered, RISKY),
    }
    scores = {key: clamp(value / max(4, word_count / 30)) for key, value in raw_scores.items()}
    label = _label_for_scores(raw_scores)
    features = [key for key, value in raw_scores.items() if value > 0]
    return ToneProfile(label=label, scores=scores, features=features)


def compare_tone(old_text: str, new_text: str) -> ToneShift:
    """Detect a tone shift between old and new text."""
    old = analyze_tone(old_text)
    new = analyze_tone(new_text)
    diff_score = sum(abs(new.scores[key] - old.scores.get(key, 0.0)) for key in new.scores)
    score = clamp(diff_score / 2.5)

    shift = _named_shift(old.label, new.label, old.scores, new.scores)
    if shift == "unchanged":
        explanation = "Tone appears broadly similar."
    else:
        explanation = f"Tone shifted from {old.label} to {new.label}."
    return ToneShift(
        from_label=old.label,
        to_label=new.label,
        shift=shift,
        score=score,
        explanation=explanation,
    )


def _keyword_count(text: str, keywords: tuple[str, ...]) -> int:
    count = 0
    for keyword in keywords:
        count += len(re.findall(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE))
    return count


def _label_for_scores(raw_scores: dict[str, int]) -> str:
    if raw_scores["promotional"] >= 2 and raw_scores["promotional"] >= raw_scores["technical"]:
        return "promotional"
    if raw_scores["restrictive"] >= 2:
        return "restrictive"
    if raw_scores["confident"] > raw_scores["cautious"] and raw_scores["confident"] >= 1:
        return "confident"
    if raw_scores["cautious"] > raw_scores["confident"] and raw_scores["cautious"] >= 1:
        return "cautious"
    if raw_scores["technical"] >= 2 and raw_scores["promotional"] == 0:
        return "technical"
    if raw_scores["risky"] >= 2:
        return "risky"
    return "neutral"


def _named_shift(
    old_label: str,
    new_label: str,
    old_scores: dict[str, float],
    new_scores: dict[str, float],
) -> str:
    if old_label == new_label:
        if new_scores.get("risky", 0.0) > old_scores.get("risky", 0.0) + 0.2:
            return "safe_to_risky"
        return "unchanged"
    if old_label == "cautious" and new_label == "confident":
        return "cautious_to_confident"
    if old_label == "confident" and new_label == "cautious":
        return "confident_to_cautious"
    if old_label == "neutral" and new_label == "promotional":
        return "neutral_to_promotional"
    if old_label == "neutral" and new_label == "restrictive":
        return "neutral_to_restrictive"
    if old_label == "technical" and new_label in {"promotional", "confident"}:
        return "technical_to_marketing"
    if new_scores.get("risky", 0.0) > old_scores.get("risky", 0.0) + 0.2:
        return "safe_to_risky"
    return f"{old_label}_to_{new_label}"

