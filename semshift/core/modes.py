"""Mode definitions for product-specific semantic drift analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModeConfig:
    """Configuration that nudges SemShift toward a review context."""

    name: str
    description: str
    focus_terms: tuple[str, ...]


MODES: dict[str, ModeConfig] = {
    "default": ModeConfig(
        name="default",
        description="General semantic comparison.",
        focus_terms=("claim", "meaning", "tone", "risk", "constraint"),
    ),
    "readme": ModeConfig(
        name="readme",
        description="README/docs review for install steps, features, limits, platforms, pricing, and positioning.",
        focus_terms=(
            "install",
            "requirement",
            "feature",
            "limitation",
            "platform",
            "pricing",
            "commercial",
            "scope",
            "guarantee",
        ),
    ),
    "policy": ModeConfig(
        name="policy",
        description="Policy/legal/product risk review for data sharing, consent, retention, liability, and obligations.",
        focus_terms=(
            "share",
            "third party",
            "retention",
            "consent",
            "tracking",
            "arbitration",
            "liability",
            "rights",
            "opt out",
        ),
    ),
    "research": ModeConfig(
        name="research",
        description="Research draft review for claims, metrics, baselines, datasets, limitations, and uncertainty.",
        focus_terms=(
            "metric",
            "accuracy",
            "baseline",
            "dataset",
            "limitation",
            "conclusion",
            "uncertainty",
            "ablation",
        ),
    ),
    "resume": ModeConfig(
        name="resume",
        description="Resume rewrite review for factual claims, titles, tools, numbers, and impact metrics.",
        focus_terms=(
            "title",
            "company",
            "metric",
            "impact",
            "revenue",
            "users",
            "latency",
            "tool",
        ),
    ),
    "prompt": ModeConfig(
        name="prompt",
        description="Prompt review for roles, constraints, safety, scope, output format, and hidden instructions.",
        focus_terms=(
            "role",
            "constraint",
            "safety",
            "format",
            "hidden",
            "scope",
            "instruction",
            "allowed",
        ),
    ),
}


def get_mode(name: str) -> ModeConfig:
    """Return a mode config or raise a clear validation error."""
    key = name.lower().strip()
    if key not in MODES:
        valid = ", ".join(sorted(MODES))
        raise ValueError(f"Unknown mode '{name}'. Expected one of: {valid}")
    return MODES[key]


def list_modes() -> list[str]:
    """List supported mode names."""
    return sorted(MODES)

