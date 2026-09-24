from zipfile import ZipFile

from engineering.document_intelligence import DocxTextExtractor


def make_docx(path, paragraphs):
    body = "".join(
        f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs
    )
    xml = f"""<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body>{body}</w:body></w:document>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def test_docx_extractor_preserves_paragraph_order(tmp_path):
    source = tmp_path / "report.docx"
    make_docx(source, ["Титульный лист", "Раздел 1", "Фактические данные"])

    result = DocxTextExtractor().extract(source)

    assert result.paragraphs == ("Титульный лист", "Раздел 1", "Фактические данные")
    assert result.text == "Титульный лист\\n\\nРаздел 1\\n\\nФактические данные"


def test_docx_extractor_does_not_invent_empty_content(tmp_path):
    source = tmp_path / "empty.docx"
    make_docx(source, [])

    result = DocxTextExtractor().extract(source)

    assert result.text == ""
    assert result.paragraphs == ()


def test_docx_extractor_extracts_tables_and_image_references(tmp_path):
    source = tmp_path / "rich.docx"
    body = """
    <w:p><w:r><w:t>Report</w:t></w:r></w:p>
    <w:tbl>
      <w:tr><w:tc><w:p><w:r><w:t>Section</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc></w:tr>
      <w:tr><w:tc><w:p><w:r><w:t>Roof</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Steel</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
    <w:p><w:r><w:drawing><wp:inline><a:graphic><a:graphicData><pic:pic><pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
    """
    xml = f"""<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
        xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">{body}</w:document>"""
    with ZipFile(source, "w") as archive:
        archive.writestr("word/document.xml", xml)

    result = DocxTextExtractor().extract(source)

    assert result.tables[0].rows == (("Section", "Value"), ("Roof", "Steel"))
    assert result.image_count == 1


def test_docx_extractor_assigns_stable_evidence_ids(tmp_path):
    source = tmp_path / "report.docx"
    make_docx(source, ["First", "Second"])
    result = DocxTextExtractor().extract(source)
    assert result.paragraph_ids[0].endswith(":paragraph:0001")
    assert result.paragraph_ids[1].endswith(":paragraph:0002")
