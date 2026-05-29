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
    f = tmp_path / "file.exe"
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


# --- Optional rich-text formats (PDF / DOCX / HTML) ---


def test_supported_extensions_include_rich_formats() -> None:
    from semshift.core.loader import SUPPORTED_EXTENSIONS

    for ext in (".pdf", ".docx", ".html", ".htm"):
        assert ext in SUPPORTED_EXTENSIONS


def test_missing_format_dependency_gives_install_hint() -> None:
    from semshift.core.loader import _load_optional

    with pytest.raises(FileLoadError, match=r"semshift\[formats\]"):
        _load_optional("semshift_no_such_optional_pkg")


def test_html_tags_are_stripped(tmp_path: Path) -> None:
    f = tmp_path / "page.html"
    f.write_text(
        "<html><head><style>body{color:red}</style>"
        "<script>alert(1)</script></head>"
        "<body><h1>Privacy</h1><p>We do not share data.</p></body></html>",
        encoding="utf-8",
    )
    text = load_text_file(f)
    assert "Privacy" in text
    assert "We do not share data." in text
    assert "alert" not in text
    assert "<" not in text


def test_docx_text_is_extracted(tmp_path: Path) -> None:
    docx = pytest.importorskip("docx")
    path = tmp_path / "doc.docx"
    document = docx.Document()
    document.add_paragraph("We do not share personal data with third parties.")
    document.save(str(path))

    loaded = load_text_file_with_warnings(path)
    assert "share personal data" in loaded.text
    assert any("best-effort" in w for w in loaded.warnings)


def test_pdf_text_is_extracted(tmp_path: Path) -> None:
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    path = tmp_path / "doc.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, "We do not share personal data.")
    pdf.save()

    text = load_text_file(path)
    assert "share personal data" in text


def test_oversized_pdf_errors_instead_of_truncating(tmp_path: Path) -> None:
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    path = tmp_path / "doc.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, "content")
    pdf.save()

    with pytest.raises(FileLoadError, match="exceeds --max-file-size"):
        load_text_file(path, max_file_size=10)
