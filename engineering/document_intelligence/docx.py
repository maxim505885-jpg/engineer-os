from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


class DocumentExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractedTable:
    id: str
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ExtractedBlock:
    id: str
    kind: str
    text: str = ""
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ExtractedDocument:
    source_path: str
    media_type: str
    text: str
    paragraphs: tuple[str, ...]
    paragraph_ids: tuple[str, ...] = ()
    tables: tuple[ExtractedTable, ...] = ()
    image_ids: tuple[str, ...] = ()
    blocks: tuple[ExtractedBlock, ...] = ()

    @property
    def image_count(self) -> int:
        return len(self.image_ids)


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

        document_id = sha256(str(source.resolve()).encode("utf-8")).hexdigest()[:12]
        body = root.find(self._NS + "body")
        if body is None:
            raise DocumentExtractionError("DOCX has no document body")

        paragraphs: list[str] = []
        paragraph_ids: list[str] = []
        tables: list[ExtractedTable] = []
        blocks: list[ExtractedBlock] = []

        def paragraph_text(paragraph: ET.Element) -> str:
            parts: list[str] = []
            for node in paragraph.iter():
                if node.tag == self._NS + "t" and node.text:
                    parts.append(node.text)
                elif node.tag == self._NS + "tab":
                    parts.append("\t")
                elif node.tag in {self._NS + "br", self._NS + "cr"}:
                    parts.append("\n")
            return "".join(parts).strip()

        def table_rows(table: ET.Element) -> tuple[tuple[str, ...], ...]:
            rows: list[tuple[str, ...]] = []
            for row in table.findall(self._NS + "tr"):
                cells: list[str] = []
                for cell in row.findall(self._NS + "tc"):
                    cells.append(paragraph_text(cell))
                rows.append(tuple(cells))
            return tuple(rows)

        paragraph_index = 0
        table_index = 0
        for child in list(body):
            if child.tag == self._NS + "p":
                value = paragraph_text(child)
                if not value:
                    continue
                paragraph_index += 1
                paragraph_id = f"{document_id}:paragraph:{paragraph_index:04d}"
                paragraphs.append(value)
                paragraph_ids.append(paragraph_id)
                blocks.append(ExtractedBlock(paragraph_id, "paragraph", value))
            elif child.tag == self._NS + "tbl":
                table_index += 1
                table_id = f"{document_id}:table:{table_index:04d}"
                rows = table_rows(child)
                tables.append(ExtractedTable(table_id, rows))
                table_text = "\n".join("\t".join(row) for row in rows)
                blocks.append(ExtractedBlock(table_id, "table", table_text))

        image_ids = tuple(
            f"{document_id}:image:{index:04d}"
            for index, node in enumerate(
                (node for node in root.iter() if node.tag.endswith("}blip") or node.tag.endswith("}imagedata")),
                start=1,
            )
        )

        return ExtractedDocument(
            source_path=str(source),
            media_type=self.media_type,
            text="\n\n".join(paragraphs),
            paragraphs=tuple(paragraphs),
            paragraph_ids=tuple(paragraph_ids),
            tables=tuple(tables),
            image_ids=image_ids,
            blocks=tuple(blocks),
        )
