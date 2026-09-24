from __future__ import annotations

from zipfile import ZipFile

from engineering.document_intelligence import DocumentIntelligence


DOC_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Paragraph one</w:t></w:r></w:p>
    <w:tbl>
      <w:tr><w:tc><w:p><w:r><w:t>Cell A</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Cell B</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
    <w:p><w:r><w:t>Paragraph two</w:t></w:r></w:p>
  </w:body>
</w:document>
"""


def _write_docx(path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'/>")
        archive.writestr("word/document.xml", DOC_XML)


def test_document_intelligence_preserves_block_order_and_evidence(tmp_path) -> None:
    path = tmp_path / "sample.docx"
    _write_docx(path)

    result = DocumentIntelligence().ingest(path, material_id="material-1")

    assert result.material.id == "material-1"
    assert [block.kind for block in result.document.blocks] == ["paragraph", "table", "paragraph"]
    assert result.document.blocks[1].text == "Cell A\tCell B"
    assert [chunk.block_kinds for chunk in result.chunks] == [("paragraph", "table", "paragraph")]
    assert result.chunks[0].evidence_ids == tuple(block.id for block in result.document.blocks)


def test_document_intelligence_assigns_stable_ids_for_same_source(tmp_path) -> None:
    path = tmp_path / "sample.docx"
    _write_docx(path)

    first = DocumentIntelligence().ingest(path)
    second = DocumentIntelligence().ingest(path)

    assert first.material.id == second.material.id
    assert first.chunks[0].id == second.chunks[0].id
    assert first.chunks[0].evidence_ids == second.chunks[0].evidence_ids
