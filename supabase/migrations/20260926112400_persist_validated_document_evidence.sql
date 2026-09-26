create or replace function public.persist_validated_document_evidence(
 p_project_id uuid,p_document_id uuid,p_source_sha256 text,p_evidence_code text,
 p_data_class text,p_description text,p_source_ref text,p_confidence text default 'PROVENANCE_VALIDATED'
) returns uuid
language plpgsql security definer set search_path=public
as $$
declare v_doc public.documents%rowtype; v_id uuid;
begin
 select * into v_doc from public.documents where id=p_document_id;
 if not found then raise exception 'DOCUMENT_NOT_FOUND'; end if;
 if v_doc.project_id is distinct from p_project_id then raise exception 'DOCUMENT_PROJECT_MISMATCH'; end if;
 if p_source_sha256 !~ '^[0-9a-f]{64}$' then raise exception 'INVALID_SOURCE_SHA256'; end if;
 if v_doc.source_checksum is null or lower(v_doc.source_checksum) <> lower(p_source_sha256) then raise exception 'SOURCE_CHECKSUM_MISMATCH'; end if;
 if p_evidence_code !~ '^doc-evidence:[0-9a-f]{64}$' then raise exception 'INVALID_EVIDENCE_CODE'; end if;
 if p_data_class not in ('PROJECT','ACTUAL','MEASURED','TESTED','CALCULATED','ASSUMED','INTERPRETED','UNKNOWN') then raise exception 'INVALID_DATA_CLASS'; end if;
 if nullif(btrim(p_description),'') is null or nullif(btrim(p_source_ref),'') is null then raise exception 'EMPTY_EVIDENCE'; end if;
 insert into public.evidence(project_id,document_id,evidence_code,data_class,description,source_ref,confidence)
 values(p_project_id,p_document_id,p_evidence_code,p_data_class,p_description,p_source_ref,p_confidence)
 on conflict (document_id,evidence_code) where document_id is not null
 do update set description=excluded.description,source_ref=excluded.source_ref,data_class=excluded.data_class,confidence=excluded.confidence
 returning id into v_id;
 return v_id;
end $$;
revoke all on function public.persist_validated_document_evidence(uuid,uuid,text,text,text,text,text,text) from public, anon, authenticated;
grant execute on function public.persist_validated_document_evidence(uuid,uuid,text,text,text,text,text,text) to service_role;
