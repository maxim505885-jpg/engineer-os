"""Identify original CAD bytes without pretending DWG is DXF."""
import hashlib
from pathlib import Path
MAX_BYTES=20*1024*1024

def inspect_cad(path, expected_sha256=None):
    path=Path(path)
    if not path.is_file() or not 0<path.stat().st_size<=MAX_BYTES:
        raise ValueError('CAD file must contain 1 byte–20 MiB')
    data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and sha!=expected_sha256:raise ValueError('CAD source identity changed')
    dwg=data[:6].decode('ascii',errors='replace')
    detected='DWG' if dwg.startswith('AC10') else 'DXF' if b'SECTION' in data[:4096] or data.startswith(b'AutoCAD Binary DXF') else 'UNKNOWN'
    reasons=[]
    if detected.lower()!=path.suffix.lower().lstrip('.'):reasons.append('FORMAT_SIGNATURE_MISMATCH')
    if detected=='DWG':reasons.append('DWG_CONVERTER_UNAVAILABLE')
    if detected=='UNKNOWN':reasons.append('CAD_FORMAT_UNKNOWN')
    return dict(status='BLOCK' if reasons else 'RECORDED',format=detected,version=dwg if detected=='DWG' else None,source_sha256=sha,size=len(data),reasons=reasons)
