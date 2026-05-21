"""File loading for SemShift text inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024
ABSOLUTE_MAX_FILE_SIZE = 500 * 1024 * 1024
BINARY_CHECK_BYTES = 4096

SUPPORTED_EXTENSIONS = {
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
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise FileLoadError(
            f"Unsupported file extension '{file_path.suffix}'. Supported: {supported}"
        )

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
