"""Separate durable asset-candidate ledger.

Validated text-evidence RPC refuses doc-asset identifiers. Never route UNCERTAINTY
assets through that validated-evidence RPC. This ledger is file-backed and
readback-verified; it does not claim a live database insert.
"""
import hashlib
import json
import os
from pathlib import Path

from .asset_provenance import verify_payload


def write_candidate_ledger(candidates, payloads, source_sha256, output_path):
    """Write verified-byte / unverified-meaning asset manifest atomically.

    payloads maps candidate_id to original bytes. The ledger stores hashes,
    not raw source data. Every requested payload must be present and match.
    """
    candidates=tuple(candidates)
    if len(set(x.candidate_id for x in candidates))!=len(candidates):
        raise ValueError('DUPLICATE_ASSET_CANDIDATE')
    records=[]
    for item in candidates:
        if item.candidate_id not in payloads:
            raise ValueError('MISSING_ASSET_PAYLOAD')
        verify_payload(item,payloads[item.candidate_id],source_sha256)
        if item.verified:
            raise ValueError('UNVERIFIED_ASSET_REQUIRED')
        records.append({
            'candidate_id':item.candidate_id,
            'source_sha256':item.source_sha256,
            'asset_sha256':item.asset_sha256,
            'asset_kind':item.asset_kind,
            'location':item.location,
            'page_number':item.page_number,
            'status':'UNCERTAINTY',
            'visual_semantics_verified':False,
        })
    manifest={
        'schema':'ENGINEER_OS_UNVERIFIED_ASSET_LEDGER_V1',
        'source_sha256':source_sha256,
        'count':len(records),
        'records':records,
        'production_evidence_rpc_persisted':False,
    }
    dest=Path(output_path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_name(dest.name+'.tmp')
    body=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    try:
        with temp.open('w',encoding='utf-8') as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,dest)
    finally:
        temp.unlink(missing_ok=True)
    replay=json.loads(dest.read_text(encoding='utf-8'))
    if replay!=manifest:
        raise ValueError('LEDGER_READBACK_MISMATCH')
    return replay
