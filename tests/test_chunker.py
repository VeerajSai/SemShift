from semshift.core.chunker import chunk_text


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
