"""Chunk text into reviewable semantic units."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from semshift.utils.text import normalize_whitespace, split_sentences

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".rst"}


@dataclass(frozen=True)
class TextChunk:
    """A meaningful chunk with source metadata."""

    id: str
    text: str
    heading: str | None
    start_line: int
    end_line: int
    source_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize this chunk for JSON output."""
        return {
            "id": self.id,
            "heading": self.heading,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
            "source_path": self.source_path,
        }


def chunk_text(text: str, path: str | None = None, max_chars: int = 900) -> list[TextChunk]:
    """Split text into markdown-aware or paragraph/sentence-aware chunks."""
    if not text.strip():
        return []

    if _looks_like_markdown(text, path):
        return _chunk_markdown(text, path=path, max_chars=max_chars)
    return _chunk_plain_text(text, path=path, max_chars=max_chars)


def _looks_like_markdown(text: str, path: str | None) -> bool:
    if path and Path(path).suffix.lower() in MARKDOWN_EXTENSIONS:
        return True
    return bool(re.search(r"(?m)^#{1,6}\s+\S", text))


def _chunk_markdown(text: str, path: str | None, max_chars: int) -> list[TextChunk]:
    lines = text.splitlines()
    chunks: list[TextChunk] = []
    heading: str | None = None
    block_lines: list[str] = []
    block_start = 1

    def flush(end_line: int) -> None:
        nonlocal block_lines, block_start
        raw = "\n".join(block_lines).strip()
        if raw:
            _append_block_chunks(
                chunks=chunks,
                raw=raw,
                heading=heading,
                start_line=block_start,
                end_line=end_line,
                path=path,
                max_chars=max_chars,
                split_long_only=True,
            )
        block_lines = []

    for index, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line.strip())
        if heading_match:
            flush(index - 1)
            heading = normalize_whitespace(heading_match.group(2))
            block_start = index + 1
            continue

        if not line.strip():
            flush(index - 1)
            block_start = index + 1
            continue

        if not block_lines:
            block_start = index
        block_lines.append(line)

    flush(len(lines))
    return _renumber(chunks)


def _chunk_plain_text(text: str, path: str | None, max_chars: int) -> list[TextChunk]:
    lines = text.splitlines()
    chunks: list[TextChunk] = []
    block_lines: list[str] = []
    block_start = 1

    def flush(end_line: int) -> None:
        nonlocal block_lines, block_start
        raw = "\n".join(block_lines).strip()
        if raw:
            _append_block_chunks(
                chunks=chunks,
                raw=raw,
                heading=None,
                start_line=block_start,
                end_line=end_line,
                path=path,
                max_chars=max_chars,
                split_long_only=False,
            )
        block_lines = []

    for index, line in enumerate(lines, start=1):
        if not line.strip():
            flush(index - 1)
            block_start = index + 1
            continue
        if not block_lines:
            block_start = index
        block_lines.append(line)

    flush(len(lines))
    return _renumber(chunks)


def _append_block_chunks(
    *,
    chunks: list[TextChunk],
    raw: str,
    heading: str | None,
    start_line: int,
    end_line: int,
    path: str | None,
    max_chars: int,
    split_long_only: bool,
) -> None:
    normalized = raw.strip()
    if split_long_only and len(normalized) <= max_chars:
        chunks.append(_make_chunk(len(chunks) + 1, normalized, heading, start_line, end_line, path))
        return

    sentences = split_sentences(normalized)
    if not split_long_only:
        for sentence in sentences:
            chunks.append(
                _make_chunk(len(chunks) + 1, sentence, heading, start_line, end_line, path)
            )
        return

    if split_long_only and len(sentences) <= 1:
        chunks.append(_make_chunk(len(chunks) + 1, normalized, heading, start_line, end_line, path))
        return

    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        next_len = current_len + len(sentence) + 1
        if current and next_len > max_chars:
            chunks.append(
                _make_chunk(
                    len(chunks) + 1,
                    " ".join(current),
                    heading,
                    start_line,
                    end_line,
                    path,
                )
            )
            current = []
            current_len = 0
        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunks.append(
            _make_chunk(len(chunks) + 1, " ".join(current), heading, start_line, end_line, path)
        )


def _make_chunk(
    index: int,
    text: str,
    heading: str | None,
    start_line: int,
    end_line: int,
    path: str | None,
) -> TextChunk:
    return TextChunk(
        id=f"chunk-{index:03d}",
        text=text.strip(),
        heading=heading,
        start_line=max(1, start_line),
        end_line=max(start_line, end_line),
        source_path=path,
    )


def _renumber(chunks: list[TextChunk]) -> list[TextChunk]:
    return [
        TextChunk(
            id=f"chunk-{index:03d}",
            text=chunk.text,
            heading=chunk.heading,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            source_path=chunk.source_path,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
