-- Keep document-derived evidence idempotent under retries/concurrency.
create unique index if not exists evidence_document_evidence_code_uidx
    on public.evidence (document_id, evidence_code)
    where document_id is not null;
