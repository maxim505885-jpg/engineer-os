"""Source-verifying application path for uncertain PDF/DOCX asset storage.

Only an explicitly selected candidate may be written. The RPC stores source
identity and UNCERTAINTY, never an engineering-verified conclusion.
"""
import hashlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .asset_provenance import verify_payload
from .asset_evidence_validation import prepare_docx_asset_candidates
from .pdf_table_asset_ingestion import pdf_table_candidates


def _docx_payload(source_path, candidate):
    with zipfile.ZipFile(source_path) as archive:
        if candidate.asset_kind=='omml_formula':
            prefix='word/document.xml#oMath['
            if not candidate.location.startswith(prefix) or not candidate.location.endswith(']'):
                raise ValueError('INVALID_FORMULA_LOCATION')
            index=int(candidate.location[len(prefix):-1])
            root=ET.fromstring(archive.read('word/document.xml'))
            formulas=root.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')
            return ET.tostring(formulas[index])
        if candidate.location.startswith('word/media/'):
            return archive.read(candidate.location)
        raise ValueError('INVALID_ASSET_LOCATION')


def persist_selected_docx_asset(source_path, source_sha256, candidate_id,
                                project_id, document_id, transport):
    candidates=prepare_docx_asset_candidates(source_path,source_sha256)
    found=tuple(item for item in candidates if item.candidate_id==candidate_id)
    if len(found)!=1:
        raise ValueError('ASSET_CANDIDATE_NOT_FOUND_OR_DUPLICATE')
    candidate=found[0]
    verify_payload(candidate,_docx_payload(source_path,candidate),source_sha256)
    return transport(candidate,project_id,document_id)


def persist_selected_pdf_table(source_path, source_sha256, page_number, candidate_id,
                               project_id, document_id, transport):
    source_path=Path(source_path)
    with source_path.open('rb') as f:
        actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=source_sha256:
        raise ValueError('SOURCE_IDENTITY_MISMATCH')
    pairs=pdf_table_candidates(source_path,(page_number,))
    found=tuple((item,payload) for item,payload in pairs if item.candidate_id==candidate_id)
    if len(found)!=1:
        raise ValueError('TABLE_CANDIDATE_NOT_FOUND_OR_DUPLICATE')
    candidate,payload=found[0]
    verify_payload(candidate,payload,source_sha256)
    return transport(candidate,project_id,document_id)
