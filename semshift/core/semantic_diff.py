"""Semantic diff orchestration and scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from semshift.core.chunker import TextChunk, chunk_text
from semshift.core.claim_extractor import ClaimDiff, compare_claims
from semshift.core.embeddings import DEFAULT_MODEL, embed_texts
from semshift.core.loader import load_text_file
from semshift.core.modes import get_mode
from semshift.core.risk_analyzer import RiskFlag, analyze_risk, risk_score
from semshift.core.tone_analyzer import ToneShift, compare_tone
from semshift.utils.scoring import clamp, drift_label, weighted_sum
from semshift.utils.text import quote, token_set, truncate

UNCHANGED_THRESHOLD = 0.90
LIGHT_CHANGE_THRESHOLD = 0.72
MATCH_THRESHOLD = 0.34


@dataclass(frozen=True)
class ChunkMatch:
    """A matched, added, or removed semantic chunk."""

    status: str
    similarity: float
    drift_score: float
    old_chunk: TextChunk | None = None
    new_chunk: TextChunk | None = None
    why_it_matters: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize a chunk match."""
        return {
            "status": self.status,
            "similarity": round(self.similarity, 4),
            "drift_score": round(self.drift_score, 4),
            "old_chunk": self.old_chunk.to_dict() if self.old_chunk else None,
            "new_chunk": self.new_chunk.to_dict() if self.new_chunk else None,
            "why_it_matters": self.why_it_matters,
        }


@dataclass(frozen=True)
class DriftScores:
    """Score breakdown for a semantic diff."""

    overall_semantic_drift: float
    added_meaning: float
    removed_meaning: float
    claim_change: float
    tone_shift: float
    risk_shift: float

    def to_dict(self) -> dict[str, float]:
        """Serialize rounded scores."""
        return {
            "overall_semantic_drift": round(self.overall_semantic_drift, 4),
            "added_meaning": round(self.added_meaning, 4),
            "removed_meaning": round(self.removed_meaning, 4),
            "claim_change": round(self.claim_change, 4),
            "tone_shift": round(self.tone_shift, 4),
            "risk_shift": round(self.risk_shift, 4),
        }


@dataclass(frozen=True)
class SemanticDiffResult:
    """Top-level SemShift result object."""

    old_label: str
    new_label: str
    mode: str
    scores: DriftScores
    drift_label: str
    summary: list[str]
    chunk_matches: list[ChunkMatch]
    claim_changes: ClaimDiff
    tone_shift: ToneShift
    risk_flags: list[RiskFlag] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    embedding_backend: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Return the overall semantic drift score."""
        return self.scores.overall_semantic_drift

    def to_dict(self) -> dict[str, object]:
        """Return structured JSON-compatible output."""
        return {
            "files": {"old": self.old_label, "new": self.new_label},
            "mode": self.mode,
            "scores": self.scores.to_dict(),
            "drift_label": self.drift_label,
            "summary": self.summary,
            "chunk_matches": [match.to_dict() for match in self.chunk_matches],
            "claim_changes": self.claim_changes.to_dict(),
            "tone_shift": self.tone_shift.to_dict(),
            "risk_flags": [flag.to_dict() for flag in self.risk_flags],
            "recommendations": self.recommendations,
            "embedding_backend": self.embedding_backend,
            "warnings": self.warnings,
        }


def compare_files(
    old_path: str | Path,
    new_path: str | Path,
    *,
    mode: str = "default",
    model: str = DEFAULT_MODEL,
) -> SemanticDiffResult:
    """Compare two supported text files."""
    old_text = load_text_file(old_path)
    new_text = load_text_file(new_path)
    return compare_text(
        old=old_text,
        new=new_text,
        mode=mode,
        model=model,
        old_label=str(old_path),
        new_label=str(new_path),
    )


def compare_text(
    old: str,
    new: str,
    *,
    mode: str = "default",
    model: str = DEFAULT_MODEL,
    old_label: str = "old text",
    new_label: str = "new text",
) -> SemanticDiffResult:
    """Compare two strings and return a semantic diff result."""
    mode_config = get_mode(mode)
    old_chunks = chunk_text(old, path=old_label)
    new_chunks = chunk_text(new, path=new_label)
    matches, backend, warnings = _match_chunks(old_chunks, new_chunks, model)
    result_warnings = list(warnings)
    if not old.strip():
        result_warnings.append(f"Old input is empty: {old_label}")
    if not new.strip():
        result_warnings.append(f"New input is empty: {new_label}")

    claim_changes = compare_claims(old, new)
    tone_shift = compare_tone(old, new)
    risk_flags = analyze_risk(old, new, mode_config.name, claim_changes)
    scores = _score_result(matches, claim_changes, tone_shift, risk_flags, old_chunks, new_chunks)
    label = drift_label(scores.overall_semantic_drift)
    summary = _build_summary(matches, claim_changes, tone_shift, risk_flags)
    recommendations = _recommendations(label, risk_flags, claim_changes)

    return SemanticDiffResult(
        old_label=old_label,
        new_label=new_label,
        mode=mode_config.name,
        scores=scores,
        drift_label=label,
        summary=summary,
        chunk_matches=matches,
        claim_changes=claim_changes,
        tone_shift=tone_shift,
        risk_flags=risk_flags,
        recommendations=recommendations,
        embedding_backend=backend,
        warnings=result_warnings,
    )


def _match_chunks(
    old_chunks: list[TextChunk],
    new_chunks: list[TextChunk],
    model: str,
) -> tuple[list[ChunkMatch], str, tuple[str, ...]]:
    if not old_chunks and not new_chunks:
        return [], "none", ()
    if not old_chunks:
        return [
            ChunkMatch(
                status="added",
                similarity=0.0,
                drift_score=0.75,
                new_chunk=chunk,
                why_it_matters="New meaning was added.",
            )
            for chunk in new_chunks
        ], "none", ()
    if not new_chunks:
        return [
            ChunkMatch(
                status="removed",
                similarity=0.0,
                drift_score=0.75,
                old_chunk=chunk,
                why_it_matters="Existing meaning was removed.",
            )
            for chunk in old_chunks
        ], "none", ()

    all_texts = [chunk.text for chunk in old_chunks] + [chunk.text for chunk in new_chunks]
    embeddings = embed_texts(all_texts, model_name=model)
    old_vectors = embeddings.vectors[: len(old_chunks)]
    new_vectors = embeddings.vectors[len(old_chunks) :]
    similarity_matrix = cosine_similarity(old_vectors, new_vectors)

    assigned_old: set[int] = set()
    assigned_new: set[int] = set()
    matched_pairs: dict[int, tuple[int, float]] = {}

    _assign_same_heading_pairs(
        old_chunks,
        new_chunks,
        similarity_matrix,
        assigned_old,
        assigned_new,
        matched_pairs,
    )

    pairs: list[tuple[float, int, int]] = []
    for old_index in range(similarity_matrix.shape[0]):
        for new_index in range(similarity_matrix.shape[1]):
            if old_index in assigned_old or new_index in assigned_new:
                continue
            adjusted_similarity = _adjusted_similarity(
                float(similarity_matrix[old_index, new_index]),
                old_chunks[old_index],
                new_chunks[new_index],
            )
            pairs.append((adjusted_similarity, old_index, new_index))
    pairs.sort(reverse=True)

    for similarity, old_index, new_index in pairs:
        if similarity < MATCH_THRESHOLD:
            break
        if old_index in assigned_old or new_index in assigned_new:
            continue
        assigned_old.add(old_index)
        assigned_new.add(new_index)
        matched_pairs[old_index] = (new_index, similarity)

    matches: list[ChunkMatch] = []
    for old_index, old_chunk in enumerate(old_chunks):
        if old_index in matched_pairs:
            new_index, similarity = matched_pairs[old_index]
            new_chunk = new_chunks[new_index]
            status = _status_for_similarity(similarity)
            drift = _drift_for_status(status, similarity)
            matches.append(
                ChunkMatch(
                    status=status,
                    similarity=similarity,
                    drift_score=drift,
                    old_chunk=old_chunk,
                    new_chunk=new_chunk,
                    why_it_matters=_explain_chunk_change(old_chunk.text, new_chunk.text, status),
                )
            )
        else:
            matches.append(
                ChunkMatch(
                    status="removed",
                    similarity=0.0,
                    drift_score=0.75,
                    old_chunk=old_chunk,
                    why_it_matters="Existing meaning was removed.",
                )
            )

    for new_index, new_chunk in enumerate(new_chunks):
        if new_index not in assigned_new:
            matches.append(
                ChunkMatch(
                    status="added",
                    similarity=0.0,
                    drift_score=0.75,
                    new_chunk=new_chunk,
                    why_it_matters="New meaning was added.",
                )
            )

    return matches, embeddings.backend, embeddings.warnings


def _status_for_similarity(similarity: float) -> str:
    if similarity >= UNCHANGED_THRESHOLD:
        return "unchanged"
    if similarity >= LIGHT_CHANGE_THRESHOLD:
        return "lightly changed"
    return "semantically changed"


def _adjusted_similarity(similarity: float, old_chunk: TextChunk, new_chunk: TextChunk) -> float:
    """Use headings as a light alignment hint without hiding text drift."""
    old_heading = (old_chunk.heading or "").strip().lower()
    new_heading = (new_chunk.heading or "").strip().lower()
    if old_heading and old_heading == new_heading:
        adjusted = clamp(similarity + 0.18)
        if token_set(old_chunk.text) != token_set(new_chunk.text):
            return min(adjusted, UNCHANGED_THRESHOLD - 0.01)
        return adjusted
    return similarity


def _assign_same_heading_pairs(
    old_chunks: list[TextChunk],
    new_chunks: list[TextChunk],
    similarity_matrix: np.ndarray,
    assigned_old: set[int],
    assigned_new: set[int],
    matched_pairs: dict[int, tuple[int, float]],
) -> None:
    """Pre-align unique identical headings; section identity matters in reviews."""
    old_by_heading = _unique_heading_indexes(old_chunks)
    new_by_heading = _unique_heading_indexes(new_chunks)
    for heading, old_index in old_by_heading.items():
        if heading not in new_by_heading:
            continue
        new_index = new_by_heading[heading]
        similarity = _adjusted_similarity(
            float(similarity_matrix[old_index, new_index]),
            old_chunks[old_index],
            new_chunks[new_index],
        )
        if similarity >= 0.18:
            assigned_old.add(old_index)
            assigned_new.add(new_index)
            matched_pairs[old_index] = (new_index, similarity)


def _unique_heading_indexes(chunks: list[TextChunk]) -> dict[str, int]:
    seen: dict[str, list[int]] = {}
    for index, chunk in enumerate(chunks):
        heading = (chunk.heading or "").strip().lower()
        if heading:
            seen.setdefault(heading, []).append(index)
    return {heading: indexes[0] for heading, indexes in seen.items() if len(indexes) == 1}


def _drift_for_status(status: str, similarity: float) -> float:
    if status == "unchanged":
        return clamp((1.0 - similarity) * 0.35)
    if status == "lightly changed":
        return clamp(0.2 + (1.0 - similarity) * 0.35)
    if status == "semantically changed":
        return clamp(max(0.45, 1.0 - similarity))
    return 0.75


def _score_result(
    matches: list[ChunkMatch],
    claim_changes: ClaimDiff,
    tone_shift: ToneShift,
    risk_flags: list[RiskFlag],
    old_chunks: list[TextChunk],
    new_chunks: list[TextChunk],
) -> DriftScores:
    semantic_score = float(np.mean([match.drift_score for match in matches])) if matches else 0.0
    added_score = _chunk_ratio(matches, "added", max(1, len(new_chunks)))
    removed_score = _chunk_ratio(matches, "removed", max(1, len(old_chunks)))
    claim_score = clamp(claim_changes.change_count / 8.0)
    tone_score = clamp(tone_shift.score)
    mode_risk_score = risk_score(risk_flags)

    overall = weighted_sum(
        [
            (semantic_score, 0.50),
            (claim_score, 0.20),
            (tone_score, 0.10),
            (mode_risk_score, 0.20),
        ]
    )
    if mode_risk_score >= 0.75:
        overall = max(overall, 0.52 + 0.18 * mode_risk_score)
    return DriftScores(
        overall_semantic_drift=clamp(overall),
        added_meaning=added_score,
        removed_meaning=removed_score,
        claim_change=claim_score,
        tone_shift=tone_score,
        risk_shift=mode_risk_score,
    )


def _chunk_ratio(matches: list[ChunkMatch], status: str, denominator: int) -> float:
    return clamp(sum(1 for match in matches if match.status == status) / denominator)


def _build_summary(
    matches: list[ChunkMatch],
    claim_changes: ClaimDiff,
    tone_shift: ToneShift,
    risk_flags: list[RiskFlag],
) -> list[str]:
    counts = {status: sum(1 for match in matches if match.status == status) for status in _statuses()}
    summary = [
        f"{counts['added']} added meaning chunks",
        f"{counts['removed']} removed meaning chunks",
        f"{counts['semantically changed']} semantically changed chunks",
        f"{claim_changes.change_count} changed claims",
    ]
    if tone_shift.shift != "unchanged":
        summary.append(tone_shift.explanation)
    if risk_flags:
        worst = max(risk_flags, key=lambda flag: {"low": 0, "medium": 1, "high": 2, "critical": 3}[flag.severity])
        summary.append(f"Risk increased: {worst.category} ({worst.severity}).")
    return summary


def _recommendations(
    label: str,
    risk_flags: list[RiskFlag],
    claim_changes: ClaimDiff,
) -> list[str]:
    recommendations: list[str] = []
    if label in {"high", "critical"}:
        recommendations.append("Hold approval until the highlighted meaning changes are reviewed.")
    elif label == "medium":
        recommendations.append("Review highlighted changes before approving.")
    else:
        recommendations.append("Low semantic drift detected; spot-check important sections.")

    if risk_flags:
        modes = {flag.mode for flag in risk_flags}
        if "policy" in modes:
            recommendations.append("Route policy/privacy risk flags to the responsible legal or trust owner.")
        elif "prompt" in modes:
            recommendations.append("Run prompt changes through safety and behavior regression review.")
        elif "resume" in modes:
            recommendations.append("Verify resume facts against the source of truth before using this rewrite.")
        elif "research" in modes:
            recommendations.append("Verify changed metrics, datasets, baselines, and conclusions before publication.")
        else:
            recommendations.append("Ask a domain owner to review risk flags.")
    if claim_changes.modified_numbers:
        recommendations.append("Verify numeric changes against the source of truth.")
    if claim_changes.strengthened_claims or claim_changes.softened_claims:
        recommendations.append("Review modal and confidence changes carefully.")
    return recommendations


def _statuses() -> tuple[str, ...]:
    return ("unchanged", "lightly changed", "semantically changed", "removed", "added")


def _explain_chunk_change(old_text: str, new_text: str, status: str) -> str:
    if status == "unchanged":
        return "Meaning appears unchanged."
    old_lower = old_text.lower()
    new_lower = new_text.lower()
    if "do not share" in old_lower and "may share" in new_lower:
        return "Data-sharing policy changed."
    if _number_near(old_lower, "retain") and _number_near(new_lower, "retain"):
        return "Retention period or retention conditions changed."
    if "opt out" in old_lower and any(term in new_lower for term in ("required", "must accept", "no opt")):
        return "User choice or consent language became more restrictive."
    if "arbitration" in new_lower and "arbitration" not in old_lower:
        return "Dispute resolution rights changed."
    if any(term in new_lower for term in ("paid license", "commercial use requires", "subscription")):
        return "Commercial or licensing terms changed."
    if any(term in old_lower for term in ("accuracy", "f1", "baseline", "dataset")) and any(
        term in new_lower for term in ("accuracy", "f1", "baseline", "dataset")
    ):
        return "Research metric, dataset, or baseline claim changed."
    if any(term in old_lower for term in ("preliminary", "may not", "do not evaluate", "limitation")) and any(
        term in new_lower for term in ("production-ready", "state-of-the-art", "proves", "delivers")
    ):
        return "Research caveat or limitation was replaced with stronger language."
    if any(term in old_lower for term in ("suggests", "may", "can improve")) and any(
        term in new_lower for term in ("proves", "state-of-the-art", "delivers")
    ):
        return "Conclusion language became stronger."
    if any(term in old_lower + new_lower for term in ("latency", "users", "revenue", "retention")) and re.search(
        r"\d", old_lower + new_lower
    ):
        return "Resume impact metric or factual numeric claim changed."
    if any(term in old_lower for term in ("may", "might", "limited", "experimental")) and any(
        term in new_lower for term in ("will", "always", "guaranteed", "reliable")
    ):
        return "Uncertainty was reduced or confidence increased."
    if any(term in old_lower for term in ("must", "shall", "will")) and any(
        term in new_lower for term in ("may", "might", "could")
    ):
        return "Obligation may have been softened."
    if status == "lightly changed":
        return "Wording changed with similar overall meaning."
    if status == "semantically changed":
        return "Meaning appears materially changed."
    return "Meaning changed."


def _number_near(text: str, keyword: str) -> bool:
    return bool(re.search(rf"\b{keyword}\w*\b[^.\n]{{0,80}}\d+", text))


def top_meaning_changes(result: SemanticDiffResult, limit: int = 5) -> list[ChunkMatch]:
    """Return the highest drift chunk matches for reports."""
    interesting = [match for match in result.chunk_matches if match.status != "unchanged"]
    return sorted(interesting, key=lambda match: match.drift_score, reverse=True)[:limit]


def chunk_section(match: ChunkMatch) -> str:
    """Return the best section label for a chunk match."""
    chunk = match.new_chunk or match.old_chunk
    if not chunk:
        return "Unknown"
    if chunk.heading:
        return chunk.heading
    return f"Lines {chunk.start_line}-{chunk.end_line}"


def chunk_old_text(match: ChunkMatch) -> str:
    """Return old chunk text or a placeholder."""
    return quote(match.old_chunk.text if match.old_chunk else "[added]", max_chars=240)


def chunk_new_text(match: ChunkMatch) -> str:
    """Return new chunk text or a placeholder."""
    return quote(match.new_chunk.text if match.new_chunk else "[removed]", max_chars=240)


def compact_change_title(match: ChunkMatch) -> str:
    """Return a short report title for a match."""
    section = chunk_section(match)
    label = match.status.upper()
    return f"{section} - {label} ({match.drift_score:.2f})"


def compact_warning(warning: str) -> str:
    """Shorten backend warnings for CLI display."""
    return truncate(warning, max_chars=180)
