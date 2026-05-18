"""File loading for SemShift text inputs."""

from __future__ import annotations

from pathlib import Path

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


def load_text_file(path: str | Path) -> str:
    """Load a supported text file with graceful encoding fallback."""
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
        data = file_path.read_bytes()
    except OSError as exc:
        raise FileLoadError(f"Could not read {file_path}: {exc}") from exc
    if not data:
        return ""

    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding).lstrip("\ufeff")
        except UnicodeDecodeError:
            continue

    return data.decode("utf-8", errors="replace").lstrip("\ufeff")
