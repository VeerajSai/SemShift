"""Tests for text chunking."""

from semshift.core.chunker import TextChunk, chunk_text


def test_chunk_markdown_uses_headings_and_line_ranges() -> None:
    text = """# Title

Intro paragraph.

## Install

Run pip install semshift.

## Limits

This is experimental.
"""

    chunks = chunk_text(text, path="README.md")

    assert [chunk.heading for chunk in chunks] == ["Title", "Install", "Limits"]
    assert chunks[1].text == "Run pip install semshift."
    assert chunks[1].start_line == 7
    assert chunks[1].end_line == 7


def test_chunk_plain_text_splits_sentences() -> None:
    text = "First claim is here. Second claim changes the meaning.\n\nA final paragraph."

    chunks = chunk_text(text, path="note.txt")

    assert len(chunks) == 3
    assert chunks[0].text == "First claim is here."
    assert chunks[1].text == "Second claim changes the meaning."
    assert chunks[2].text == "A final paragraph."


def test_empty_text_returns_empty_list() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_source_path_stored_in_chunk() -> None:
    chunks = chunk_text("Some text here.", path="policy.md")
    assert all(chunk.source_path == "policy.md" for chunk in chunks)


def test_source_path_none_when_not_provided() -> None:
    chunks = chunk_text("Some text here.", path=None)
    assert all(chunk.source_path is None for chunk in chunks)


def test_chunk_ids_are_sequentially_numbered() -> None:
    text = "Para one.\n\nPara two.\n\nPara three."
    chunks = chunk_text(text, path="file.txt")
    assert [chunk.id for chunk in chunks] == ["chunk-001", "chunk-002", "chunk-003"]


def test_markdown_detected_by_file_extension() -> None:
    text = "No headings here just plain text."
    chunks_md = chunk_text(text, path="file.md")
    chunks_txt = chunk_text(text, path="file.txt")
    assert len(chunks_md) == 1
    assert len(chunks_txt) == 1


def test_markdown_detected_by_content_heading() -> None:
    text = "# Heading\n\nContent below."
    chunks = chunk_text(text, path=None)
    assert any(chunk.heading == "Heading" for chunk in chunks)


def test_chunk_without_heading_has_none_heading() -> None:
    text = "No headings in this file."
    chunks = chunk_text(text, path="file.txt")
    assert all(chunk.heading is None for chunk in chunks)


def test_long_markdown_block_is_split_into_multiple_chunks() -> None:
    long_text = "This is a sentence. " * 60
    heading = "# Section\n\n"
    chunks = chunk_text(heading + long_text, path="README.md")
    assert len(chunks) > 1


def test_single_sentence_not_split_further() -> None:
    text = "One sentence only."
    chunks = chunk_text(text, path="file.md")
    assert len(chunks) == 1
    assert chunks[0].text == "One sentence only."


def test_to_dict_has_all_required_keys() -> None:
    chunks = chunk_text("Hello world.", path="file.txt")
    d = chunks[0].to_dict()
    assert set(d.keys()) == {"id", "heading", "start_line", "end_line", "text", "source_path"}


def test_start_line_at_least_one() -> None:
    chunks = chunk_text("Some text.", path="file.txt")
    assert all(chunk.start_line >= 1 for chunk in chunks)


def test_end_line_gte_start_line() -> None:
    chunks = chunk_text("Para one.\n\nPara two.")
    assert all(chunk.end_line >= chunk.start_line for chunk in chunks)


def test_rst_extension_treated_as_markdown() -> None:
    text = "# Section\n\nContent here."
    chunks = chunk_text(text, path="doc.rst")
    assert any(chunk.heading == "Section" for chunk in chunks)


def test_yaml_file_not_treated_as_markdown() -> None:
    text = "key: value\nanother: thing"
    chunks = chunk_text(text, path="config.yml")
    assert chunks
    assert all(chunk.heading is None for chunk in chunks)


def test_multiple_heading_levels_all_captured() -> None:
    text = "# H1\n\nContent.\n\n## H2\n\nMore.\n\n### H3\n\nDeep."
    chunks = chunk_text(text, path="README.md")
    headings = [c.heading for c in chunks]
    assert "H1" in headings
    assert "H2" in headings
    assert "H3" in headings
