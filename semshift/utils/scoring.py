"""Shared scoring helpers."""

from __future__ import annotations

LABEL_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp a score to a bounded interval."""
    return max(minimum, min(maximum, value))


def drift_label(score: float) -> str:
    """Map a 0..1 drift score to SemShift labels."""
    score = clamp(score)
    if score < 0.20:
        return "low"
    if score < 0.45:
        return "medium"
    if score < 0.70:
        return "high"
    return "critical"


def label_meets(label: str, threshold: str) -> bool:
    """Return whether a drift label meets or exceeds a threshold."""
    try:
        return LABEL_ORDER[label.lower()] >= LABEL_ORDER[threshold.lower()]
    except KeyError:
        valid = ", ".join(LABEL_ORDER)
        raise ValueError(f"Unknown drift threshold. Expected one of: {valid}") from None


def weighted_sum(parts: list[tuple[float, float]]) -> float:
    """Compute a normalized weighted sum from (score, weight) pairs."""
    total_weight = sum(weight for _, weight in parts)
    if total_weight <= 0:
        return 0.0
    return clamp(sum(score * weight for score, weight in parts) / total_weight)

