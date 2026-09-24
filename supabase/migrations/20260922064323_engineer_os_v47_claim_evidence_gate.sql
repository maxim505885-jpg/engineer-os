-- ENGINEER OS V47: Claim -> Evidence traceability gate
create or replace function public.claim_evidence_traceability_gate(p_orchestration_run_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  v_untraceable int := 0;
  v_weak int := 0;
  v_blocking int := 0;
begin
  select count(*) into v_untraceable
  from engineering_conclusion_traces t
  where t.orchestration_run_id=p_orchestration_run_id
    and coalesce(t.trace_status,'') not in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
    and (coalesce(jsonb_array_length(t.evidence_refs),0)=0 or coalesce(jsonb_array_length(t.fact_refs),0)=0);

  select count(*) into v_weak
  from evidence_claims c
  where c.project_id in (select project_id from engineering_conclusion_traces where orchestration_run_id=p_orchestration_run_id)
    and coalesce(c.status,'') not in ('VERIFIED','ACCEPTED','PASS')
    and coalesce(c.claim_type,'') in ('FINDING','CONCLUSION','FACT');

  select count(*) into v_blocking
  from engineering_contradictions c
  where c.project_id in (select project_id from engineering_conclusion_traces where orchestration_run_id=p_orchestration_run_id)
    and c.blocking=true
    and coalesce(c.status,'') not in ('RESOLVED','CLOSED','ACCEPTED');

  return jsonb_build_object(
    'gate','CLAIM_EVIDENCE_TRACEABILITY',
    'status',case when v_untraceable=0 and v_blocking=0 then 'PASS' else 'BLOCK' end,
    'untraceable_conclusions',v_untraceable,
    'weak_claims',v_weak,
    'blocking_contradictions',v_blocking
  );
end;
$$;
revoke all on function public.claim_evidence_traceability_gate(uuid) from public, anon, authenticated;
grant execute on function public.claim_evidence_traceability_gate(uuid) to service_role;

-- Extend global integrity snapshot with the same traceability invariant.
create or replace function public.engineer_os_integrity_snapshot()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare r jsonb;
begin
  select jsonb_build_object(
    'status', case when
      (select count(*) from orchestration_runs o where o.status in ('COMPLETED','FAILED','BLOCKED','CANCELLED') and exists(select 1 from job_queue j where j.orchestration_run_id=o.id and j.status in ('QUEUED','RUNNING'))) = 0
      and (select count(*) from engineering_conclusion_traces t where t.trace_status not in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE') and coalesce(jsonb_array_length(t.evidence_refs),0)=0) = 0
      and (select count(*) from engineering_contradictions c where c.blocking=true and coalesce(c.status,'') not in ('RESOLVED','CLOSED','ACCEPTED')) = 0
      then 'PASS' else 'BLOCK' end,
    'terminal_orchestration_active_jobs',(select count(*) from orchestration_runs o where o.status in ('COMPLETED','FAILED','BLOCKED','CANCELLED') and exists(select 1 from job_queue j where j.orchestration_run_id=o.id and j.status in ('QUEUED','RUNNING'))),
    'untraceable_conclusions',(select count(*) from engineering_conclusion_traces t where t.trace_status not in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE') and coalesce(jsonb_array_length(t.evidence_refs),0)=0),
    'blocking_contradictions',(select count(*) from engineering_contradictions c where c.blocking=true and coalesce(c.status,'') not in ('RESOLVED','CLOSED','ACCEPTED')),
    'captured_at',now()
  ) into r;
  return r;
end;
$$;
revoke all on function public.engineer_os_integrity_snapshot() from public, anon, authenticated;
grant execute on function public.engineer_os_integrity_snapshot() to service_role;
