from zipfile import ZipFile

from engineering.document_intelligence import DocxTextExtractor, DocumentChunker


def make_docx(path, children):
    body = "".join(children)
    xml = f"""<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def test_chunker_preserves_paragraph_table_order_and_evidence(tmp_path):
    source = tmp_path / "report.docx"
    make_docx(
        source,
        [
            "<w:p><w:r><w:t>Before table</w:t></w:r></w:p>",
            "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cell A</w:t></w:r></w:p></w:tc></w:tr></w:tbl>",
            "<w:p><w:r><w:t>After table</w:t></w:r></w:p>",
        ],
    )

    document = DocxTextExtractor().extract(source)
    chunks = DocumentChunker(max_chars=1000).chunk(document)

    assert [block.kind for block in document.blocks] == ["paragraph", "table", "paragraph"]
    assert len(chunks) == 1
    assert chunks[0].text == "Before table\n\nCell A\n\nAfter table"
    assert chunks[0].evidence_ids == tuple(block.id for block in document.blocks)
    assert chunks[0].id.endswith(":chunk:0001")


def test_chunker_splits_without_losing_evidence(tmp_path):
    source = tmp_path / "report.docx"
    make_docx(
        source,
        [
            "<w:p><w:r><w:t>AAAA</w:t></w:r></w:p>",
            "<w:p><w:r><w:t>BBBB</w:t></w:r></w:p>",
            "<w:p><w:r><w:t>CCCC</w:t></w:r></w:p>",
        ],
    )

    document = DocxTextExtractor().extract(source)
    chunks = DocumentChunker(max_chars=6).chunk(document)

    assert len(chunks) == 3
    assert [chunk.sequence for chunk in chunks] == [1, 2, 3]
    assert [chunk.evidence_ids[0] for chunk in chunks] == list(document.paragraph_ids)
