"""Tests for the file loader module."""

from __future__ import annotations

from pathlib import Path

import pytest

from semshift.core.loader import FileLoadError, load_text_file, load_text_file_with_warnings


def test_load_utf8_file(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text("Hello world.", encoding="utf-8")
    assert load_text_file(f) == "Hello world."


def test_load_utf8_bom_file(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_bytes(b"\xef\xbb\xbfHello BOM.")
    text = load_text_file(f)
    assert text == "Hello BOM."
    assert not text.startswith("\ufeff")


def test_load_cp1252_file(tmp_path: Path) -> None:
    f = tmp_path / "doc.txt"
    f.write_bytes("Caf\xe9".encode("cp1252"))
    text = load_text_file(f)
    assert "Caf" in text


def test_load_empty_file_returns_empty_string(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    assert load_text_file(f) == ""


def test_load_all_supported_extensions(tmp_path: Path) -> None:
    for ext in (".txt", ".md", ".rst", ".json", ".yaml", ".yml", ".py", ".js", ".ts"):
        f = tmp_path / f"file{ext}"
        f.write_text("content", encoding="utf-8")
        assert load_text_file(f) == "content"


def test_load_file_not_found_raises(tmp_path: Path) -> None:
    with pytest.raises(FileLoadError, match="File not found"):
        load_text_file(tmp_path / "missing.md")


def test_load_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileLoadError, match="Expected a file"):
        load_text_file(tmp_path)


def test_load_unsupported_extension_raises(tmp_path: Path) -> None:
    f = tmp_path / "file.pdf"
    f.write_bytes(b"data")
    with pytest.raises(FileLoadError, match="Unsupported file extension"):
        load_text_file(f)


def test_load_strips_bom_for_utf8_sig(tmp_path: Path) -> None:
    f = tmp_path / "bom.txt"
    content = "Privacy policy text."
    f.write_text(content, encoding="utf-8-sig")
    text = load_text_file(f)
    assert text == content
    assert "\ufeff" not in text


def test_load_oversized_file_truncates_with_warning(tmp_path: Path) -> None:
    f = tmp_path / "large.md"
    f.write_text("abcdefghij", encoding="utf-8")

    loaded = load_text_file_with_warnings(f, max_file_size=4)

    assert loaded.text == "abcd"
    assert loaded.warnings
    assert "truncated" in loaded.warnings[0]


def test_load_binary_file_rejected(tmp_path: Path) -> None:
    f = tmp_path / "binary.txt"
    f.write_bytes(b"hello\x00world")

    with pytest.raises(FileLoadError, match="Binary file rejected"):
        load_text_file(f)
