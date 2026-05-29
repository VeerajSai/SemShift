"""File loading for SemShift text inputs."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024
ABSOLUTE_MAX_FILE_SIZE = 500 * 1024 * 1024
BINARY_CHECK_BYTES = 4096

# Plain-text formats decoded directly.
PLAIN_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
}

# Formats whose text is extracted (PDF/DOCX need `semshift[formats]`; HTML uses stdlib).
RICH_TEXT_EXTENSIONS = {".pdf", ".docx", ".html", ".htm"}

SUPPORTED_EXTENSIONS = PLAIN_TEXT_EXTENSIONS | RICH_TEXT_EXTENSIONS


class FileLoadError(RuntimeError):
    """Raised when SemShift cannot load a requested text file."""


@dataclass(frozen=True)
class LoadedText:
    """Loaded text plus safety warnings produced while reading it."""

    text: str
    warnings: tuple[str, ...] = ()


def load_text_file(
    path: str | Path,
    *,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
) -> str:
    """Load a supported text file with graceful encoding fallback."""
    return load_text_file_with_warnings(path, max_file_size=max_file_size).text


def load_text_file_with_warnings(
    path: str | Path,
    *,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
) -> LoadedText:
    """Load a supported text file, truncating oversized inputs with a warning."""
    if max_file_size <= 0:
        raise FileLoadError("--max-file-size must be greater than zero")
    if max_file_size > ABSOLUTE_MAX_FILE_SIZE:
        raise FileLoadError(
            f"--max-file-size cannot exceed {ABSOLUTE_MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    file_path = Path(path)
    if not file_path.exists():
        raise FileLoadError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise FileLoadError(f"Expected a file, got: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise FileLoadError(
            f"Unsupported file extension '{file_path.suffix}'. Supported: {supported}"
        )

    if suffix in RICH_TEXT_EXTENSIONS:
        return _load_rich_text(file_path, suffix, max_file_size=max_file_size)

    try:
        size = file_path.stat().st_size
        warnings: list[str] = []
        if size > max_file_size:
            with file_path.open("rb") as handle:
                data = handle.read(max_file_size)
            warnings.append(
                f"File exceeded max size and was truncated: {file_path} "
                f"({size} bytes > {max_file_size} bytes)"
            )
        else:
            data = file_path.read_bytes()
    except OSError as exc:
        raise FileLoadError(f"Could not read {file_path}: {exc}") from exc

    if not data:
        return LoadedText(text="", warnings=())

    if _looks_binary(data):
        raise FileLoadError(f"Binary file rejected: {file_path}")

    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return LoadedText(text=data.decode(encoding).lstrip("\ufeff"), warnings=tuple(warnings))
        except UnicodeDecodeError:
            continue

    return LoadedText(
        text=data.decode("utf-8", errors="replace").lstrip("\ufeff"), warnings=tuple(warnings)
    )


def _looks_binary(data: bytes) -> bool:
    """Return whether bytes look like a binary payload rather than text."""
    return b"\x00" in data[:BINARY_CHECK_BYTES]


def _load_optional(module_name: str, extra: str = "formats") -> object:
    """Import an optional dependency or raise a friendly install hint."""
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise FileLoadError(
            f"Reading this file type requires extra dependencies (missing '{module_name}'). "
            f'Install with: pip install "semshift[{extra}]"'
        ) from exc


def _load_rich_text(path: Path, suffix: str, *, max_file_size: int) -> LoadedText:
    """Extract plain text from a PDF, DOCX, or HTML file (best effort)."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise FileLoadError(f"Could not read {path}: {exc}") from exc

    if suffix in {".pdf", ".docx"} and size > max_file_size:
        raise FileLoadError(
            f"{suffix} file exceeds --max-file-size ({size} > {max_file_size} bytes). "
            "Increase --max-file-size to read it (these formats are not safely truncated)."
        )

    if suffix == ".pdf":
        text = _extract_pdf(path)
        note = "PDF text extraction is best-effort plain text; layout and images are dropped."
    elif suffix == ".docx":
        text = _extract_docx(path)
        note = "DOCX text extraction is best-effort plain text; styling and images are dropped."
    else:  # .html / .htm
        text, truncated = _extract_html(path, max_file_size=max_file_size)
        note = "HTML tags were stripped to plain text."
        if truncated:
            return LoadedText(text=text, warnings=(note, f"File exceeded max size: {path}"))

    warnings: tuple[str, ...] = (note,) if text.strip() else (note, f"No text extracted: {path}")
    return LoadedText(text=text, warnings=warnings)


def _extract_pdf(path: Path) -> str:
    pypdf = _load_optional("pypdf")
    try:
        reader = pypdf.PdfReader(str(path))  # type: ignore[attr-defined]
        parts = [page.extract_text() or "" for page in reader.pages]
    except FileLoadError:
        raise
    except Exception as exc:  # pypdf raises a range of parsing errors
        raise FileLoadError(f"Could not read PDF {path}: {exc}") from exc
    return "\n\n".join(part.strip() for part in parts if part.strip()).strip()


def _extract_docx(path: Path) -> str:
    docx = _load_optional("docx")
    try:
        document = docx.Document(str(path))  # type: ignore[attr-defined]
    except Exception as exc:  # python-docx raises package/zip errors for bad files
        raise FileLoadError(f"Could not read DOCX {path}: {exc}") from exc
    blocks = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            blocks.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(block for block in blocks if block.strip()).strip()


class _TextExtractingParser(HTMLParser):
    """Collect visible text, skipping script/style content."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip == 0 and data.strip():
            self._chunks.append(data)

    @property
    def text(self) -> str:
        return "\n".join(chunk.strip() for chunk in self._chunks).strip()


def _extract_html(path: Path, *, max_file_size: int) -> tuple[str, bool]:
    try:
        size = path.stat().st_size
        truncated = size > max_file_size
        with path.open("rb") as handle:
            data = handle.read(max_file_size) if truncated else handle.read()
    except OSError as exc:
        raise FileLoadError(f"Could not read {path}: {exc}") from exc
    text = data.decode("utf-8", errors="replace").lstrip("﻿")
    parser = _TextExtractingParser()
    parser.feed(text)
    return parser.text, truncated
