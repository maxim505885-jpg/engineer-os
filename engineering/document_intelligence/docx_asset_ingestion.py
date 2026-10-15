"""Extract immutable source-bound candidates from DOCX without accepting their meaning.

Only source ZIP assets/OMML are copied into candidate identities. This is an
ingestion boundary, not a visual validation or evidence persistence step.
"""
import hashlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from .asset_provenance import DocumentAssetEvidence, verify_payload

MATH_NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}


def source_assets(docx_path):
    path=Path(docx_path)
    with path.open('rb') as f:
        source_hash=hashlib.file_digest(f,'sha256').hexdigest()
    assets=[]
    with zipfile.ZipFile(path) as archive:
        invalid=archive.testzip()
        if invalid:
            raise ValueError('DOCX_CORRUPT_ZIP:'+invalid)
        root=ET.fromstring(archive.read('word/document.xml'))
        for index,formula in enumerate(root.findall('.//m:oMath',MATH_NS)):
            payload=ET.tostring(formula)
            item=DocumentAssetEvidence(source_sha256=source_hash,
                asset_sha256=hashlib.sha256(payload).hexdigest(),
                asset_kind='omml_formula',location=f'word/document.xml#oMath[{index}]')
            verify_payload(item,payload,source_hash)
            assets.append(item)
        for name in sorted(archive.namelist()):
            if not name.startswith('word/media/') or name.endswith('/'):
                continue
            data=archive.read(name)
            kind='emf_graphic' if name.lower().endswith('.emf') else 'embedded_image'
            item=DocumentAssetEvidence(source_sha256=source_hash,
                asset_sha256=hashlib.sha256(data).hexdigest(),
                asset_kind=kind,location=name)
            verify_payload(item,data,source_hash)
            assets.append(item)
    return tuple(assets)
