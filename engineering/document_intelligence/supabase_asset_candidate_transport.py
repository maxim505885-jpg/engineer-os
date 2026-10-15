"""Backend-only Supabase RPC transport for UNVERIFIED document assets.

NEVER use the validated text-evidence RPC for doc-asset candidates.
Source/asset bytes must be checked by the caller before this transport.
"""
from __future__ import annotations

import json
import os
from urllib import error,request
from uuid import UUID

from .asset_provenance import DocumentAssetEvidence


class SupabaseAssetCandidateTransportError(RuntimeError):
    pass


class SupabaseAssetCandidateTransport:
    def __init__(self, base_url: str, service_role_key: str, opener=None):
        self._base_url=base_url.rstrip('/')
        self._key=service_role_key
        self._opener=opener or request.urlopen
        if not self._base_url.startswith('https://'):
            raise ValueError('Supabase URL must use https')
        if not self._key.strip():
            raise ValueError('Backend service key is required')

    def __call__(self, candidate: DocumentAssetEvidence, project_id: str, document_id: str):
        if not isinstance(candidate,DocumentAssetEvidence) or candidate.verified:
            raise ValueError('Only unverified document assets are permitted')
        for value in (project_id,document_id):
            UUID(value)
        payload={
            'p_project_id':project_id,
            'p_document_id':document_id,
            'p_source_sha256':candidate.source_sha256,
            'p_candidate_id':candidate.candidate_id,
            'p_asset_sha256':candidate.asset_sha256,
            'p_asset_kind':candidate.asset_kind,
            'p_source_location':candidate.location,
            'p_page_number':candidate.page_number,
        }
        req=request.Request(
            self._base_url+'/rest/v1/rpc/persist_unverified_document_asset_candidate',
            data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),
            method='POST',
            headers={
                'apikey':self._key,
                'Authorization':'Bearer '+self._key,
                'Content-Type':'application/json',
            },
        )
        try:
            with self._opener(req,timeout=30) as response:
                body=response.read().decode('utf-8')
        except (error.HTTPError,error.URLError,TimeoutError) as exc:
            raise SupabaseAssetCandidateTransportError('asset candidate RPC failed') from exc
        try:
            candidate_row_id=json.loads(body)
            UUID(candidate_row_id)
        except (ValueError,TypeError,AttributeError) as exc:
            raise SupabaseAssetCandidateTransportError('invalid asset candidate RPC response') from exc
        return candidate_row_id


def production_asset_candidate_transport():
    return SupabaseAssetCandidateTransport(
        os.environ.get('SUPABASE_URL',''),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY',''),
    )
