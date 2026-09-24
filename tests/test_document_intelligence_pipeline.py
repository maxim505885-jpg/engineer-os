from zipfile import ZipFile

from engineering.document_intelligence import DocumentChunker, DocumentIntelligence


def make_docx(path):
    body = "<w:p><w:r><w:t>ТЗ</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Расчет</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
    xml = f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>'
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def test_document_intelligence_binds_material_and_chunks(tmp_path):
    source = tmp_path / "report.docx"
    make_docx(source)
    result = DocumentIntelligence(DocumentChunker(max_chars=1000)).ingest(source)
    assert result.material.kind == "document"
    assert result.material.name == "report.docx"
    assert len(result.chunks) == 1
    assert result.chunks[0].evidence_ids == tuple(block.id for block in result.document.blocks)
    assert "Расчет" in result.chunks[0].text
