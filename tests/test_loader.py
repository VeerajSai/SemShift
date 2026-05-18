"""Tests for the file loader module."""

import pytest

from semshift.core.loader import FileLoadError, load_text_file


def test_load_utf8_file(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("Hello world.", encoding="utf-8")
    assert load_text_file(f) == "Hello world."


def test_load_utf8_bom_file(tmp_path):
    f = tmp_path / "doc.md"
    f.write_bytes(b"\xef\xbb\xbfHello BOM.")
    text = load_text_file(f)
    assert text == "Hello BOM."
    assert not text.startswith("﻿")


def test_load_cp1252_file(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_bytes("Caf\xe9".encode("cp1252"))
    text = load_text_file(f)
    assert "Caf" in text


def test_load_empty_file_returns_empty_string(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    assert load_text_file(f) == ""


def test_load_all_supported_extensions(tmp_path):
    for ext in (".txt", ".md", ".rst", ".json", ".yaml", ".yml", ".py", ".js", ".ts"):
        f = tmp_path / f"file{ext}"
        f.write_text("content", encoding="utf-8")
        assert load_text_file(f) == "content"


def test_load_file_not_found_raises(tmp_path):
    with pytest.raises(FileLoadError, match="File not found"):
        load_text_file(tmp_path / "missing.md")


def test_load_directory_raises(tmp_path):
    with pytest.raises(FileLoadError, match="Expected a file"):
        load_text_file(tmp_path)


def test_load_unsupported_extension_raises(tmp_path):
    f = tmp_path / "file.pdf"
    f.write_bytes(b"data")
    with pytest.raises(FileLoadError, match="Unsupported file extension"):
        load_text_file(f)


def test_load_strips_bom_for_utf8_sig(tmp_path):
    f = tmp_path / "bom.txt"
    content = "Privacy policy text."
    f.write_text(content, encoding="utf-8-sig")
    text = load_text_file(f)
    assert text == content
    assert "﻿" not in text
