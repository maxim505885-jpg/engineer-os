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
