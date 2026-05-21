"""Text normalization and lightweight parsing helpers."""

from __future__ import annotations

import html
import re

SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'`(])")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*")


def normalize_whitespace(text: str) -> str:
    """Collapse internal whitespace while preserving readable text."""
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split text into sentence-like units with conservative heuristics."""
    text = normalize_whitespace(text)
    if not text:
        return []

    pieces = SENTENCE_BOUNDARY_RE.split(text)
    sentences: list[str] = []
    for piece in pieces:
        piece = piece.strip()
        if piece:
            sentences.append(piece)
    return sentences or [text]


def token_set(text: str) -> set[str]:
    """Return lowercase lexical tokens useful for fuzzy overlap checks."""
    return {token.lower() for token in TOKEN_RE.findall(text)}


def token_overlap(left: str, right: str) -> float:
    """Compute a small Jaccard-style token overlap score."""
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def truncate(text: str, max_chars: int = 220) -> str:
    """Trim long text for terminal and markdown reports."""
    clean = normalize_whitespace(text)
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def quote(text: str, max_chars: int = 220) -> str:
    """Return a typographic quote-like snippet without relying on Unicode."""
    return f'"{truncate(text, max_chars=max_chars)}"'


def escape_markdown_text(text: str, *, max_chars: int | None = None) -> str:
    """Escape untrusted text before placing it into Markdown/HTML renderers."""
    clean = normalize_whitespace(text)
    if max_chars is not None:
        clean = truncate(clean, max_chars=max_chars)
    return html.escape(clean, quote=False)


def markdown_code(text: str, *, max_chars: int = 220) -> str:
    """Return a safe inline Markdown code span for untrusted text."""
    clean = escape_markdown_text(text, max_chars=max_chars).replace("`", "'")
    return f"`{clean}`"
