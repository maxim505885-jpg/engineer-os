from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree as ET


class DocumentExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractedTable:
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ExtractedDocument:
    source_path: str
    media_type: str
    text: str
    paragraphs: tuple[str, ...]
    tables: tuple[ExtractedTable, ...] = ()
    image_count: int = 0


class DocxTextExtractor:
    """Dependency-free DOCX extraction; it does not infer engineering facts."""

    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    _NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    def extract(self, path: str | Path) -> ExtractedDocument:
        source = Path(path)
        if not source.is_file():
            raise DocumentExtractionError(f"Document not found: {source}")
        try:
            with ZipFile(source) as archive:
                try:
                    xml = archive.read("word/document.xml")
                except KeyError as exc:
                    raise DocumentExtractionError("DOCX has no word/document.xml") from exc
        except (BadZipFile, OSError) as exc:
            raise DocumentExtractionError(f"Cannot read DOCX: {source}") from exc

        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            raise DocumentExtractionError("Invalid DOCX XML") from exc

        paragraphs: list[str] = []
        for paragraph in root.iter(self._NS + "p"):
            parts: list[str] = []
            for node in paragraph.iter():
                if node.tag == self._NS + "t" and node.text:
                    parts.append(node.text)
                elif node.tag == self._NS + "tab":
                    parts.append("\\t")
                elif node.tag in {self._NS + "br", self._NS + "cr"}:
                    parts.append("\\n")
            value = "".join(parts).strip()
            if value:
                paragraphs.append(value)

        tables: list[ExtractedTable] = []
        for table in root.iter(self._NS + "tbl"):
            rows: list[tuple[str, ...]] = []
            for row in table.findall(self._NS + "tr"):
                cells: list[str] = []
                for cell in row.findall(self._NS + "tc"):
                    parts: list[str] = []
                    for node in cell.iter():
                        if node.tag == self._NS + "t" and node.text:
                            parts.append(node.text)
                        elif node.tag == self._NS + "tab":
                            parts.append("\\t")
                    cells.append("".join(parts).strip())
                rows.append(tuple(cells))
            tables.append(ExtractedTable(tuple(rows)))

        image_count = sum(
            1 for node in root.iter()
            if node.tag.endswith("}blip") or node.tag.endswith("}imagedata")
        )

        return ExtractedDocument(
            source_path=str(source),
            media_type=self.media_type,
            text="\\n\\n".join(paragraphs),
            paragraphs=tuple(paragraphs),
            tables=tuple(tables),
            image_count=image_count,
        )
