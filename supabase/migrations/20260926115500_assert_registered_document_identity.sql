create or replace function public.assert_registered_document_identity(
  p_project_id uuid,
  p_document_id uuid,
  p_source_sha256 text
) returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  v_checksum text;
  v_project_id uuid;
begin
  if p_source_sha256 is null or p_source_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception 'INVALID_SOURCE_SHA256';
  end if;
  select project_id, source_checksum into v_project_id, v_checksum
  from public.documents where id = p_document_id;
  if not found then raise exception 'DOCUMENT_NOT_FOUND'; end if;
  if v_project_id <> p_project_id then raise exception 'PROJECT_DOCUMENT_MISMATCH'; end if;
  if v_checksum is null or lower(v_checksum) <> p_source_sha256 then
    raise exception 'SOURCE_CHECKSUM_MISMATCH';
  end if;
  return true;
end;
$$;
revoke all on function public.assert_registered_document_identity(uuid,uuid,text) from public;
revoke all on function public.assert_registered_document_identity(uuid,uuid,text) from anon;
revoke all on function public.assert_registered_document_identity(uuid,uuid,text) from authenticated;
grant execute on function public.assert_registered_document_identity(uuid,uuid,text) to service_role;
