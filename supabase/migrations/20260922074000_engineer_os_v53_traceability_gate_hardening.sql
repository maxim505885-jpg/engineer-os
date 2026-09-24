-- ENGINEER OS V53
-- Traceability gate hardening:
-- 1) nonexistent orchestration runs must BLOCK
-- 2) weak FINDING/CONCLUSION/FACT claims must BLOCK
-- 3) service_role-only execution remains enforced

create or replace function public.claim_evidence_traceability_gate(p_orchestration_run_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $function$
declare
  v_exists boolean := false;
  v_untraceable int := 0;
  v_weak int := 0;
  v_blocking int := 0;
begin
  select exists(
    select 1 from public.orchestration_runs
    where id=p_orchestration_run_id
  ) into v_exists;

  if not v_exists then
    return jsonb_build_object(
      'gate','CLAIM_EVIDENCE_TRACEABILITY',
      'status','BLOCK',
      'reason','ORCHESTRATION_RUN_NOT_FOUND',
      'untraceable_conclusions',0,
      'weak_claims',0,
      'blocking_contradictions',0
    );
  end if;

  select count(*) into v_untraceable
  from public.engineering_conclusion_traces t
  where t.orchestration_run_id=p_orchestration_run_id
    and coalesce(t.trace_status,'') not in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
    and (
      coalesce(jsonb_array_length(t.evidence_refs),0)=0
      or coalesce(jsonb_array_length(t.fact_refs),0)=0
    );

  select count(*) into v_weak
  from public.evidence_claims c
  where c.project_id in (
    select project_id from public.engineering_conclusion_traces
    where orchestration_run_id=p_orchestration_run_id
  )
  and coalesce(c.status,'') not in ('VERIFIED','ACCEPTED','PASS')
  and coalesce(c.claim_type,'') in ('FINDING','CONCLUSION','FACT');

  select count(*) into v_blocking
  from public.engineering_contradictions c
  where c.project_id in (
    select project_id from public.engineering_conclusion_traces
    where orchestration_run_id=p_orchestration_run_id
  )
  and c.blocking=true
  and coalesce(c.status,'') not in ('RESOLVED','CLOSED','ACCEPTED');

  return jsonb_build_object(
    'gate','CLAIM_EVIDENCE_TRACEABILITY',
    'status',case
      when v_untraceable=0 and v_weak=0 and v_blocking=0 then 'PASS'
      else 'BLOCK'
    end,
    'untraceable_conclusions',v_untraceable,
    'weak_claims',v_weak,
    'blocking_contradictions',v_blocking
  );
end;
$function$;

revoke execute on function public.claim_evidence_traceability_gate(uuid) from public, anon, authenticated;
grant execute on function public.claim_evidence_traceability_gate(uuid) to service_role;
