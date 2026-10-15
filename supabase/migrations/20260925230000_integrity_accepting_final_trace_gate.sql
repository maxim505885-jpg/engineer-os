-- ENGINEER OS: accepting final audits require a conclusion trace.
create or replace function public.engineer_os_integrity_snapshot()
returns jsonb
language plpgsql
security definer
set search_path=public
as $function$
declare
  r jsonb;
  v_accepting_final_without_trace integer := 0;
begin
  select count(*) into v_accepting_final_without_trace
  from public.final_audit_results f
  where f.status in ('ACCEPTED','ACCEPTED_WITH_REMARKS','PASS')
    and not exists (
      select 1
      from public.engineering_conclusion_traces t
      where t.task_id = f.task_id
    );

  select jsonb_build_object(
    'status', case when
      (select count(*) from orchestration_runs o where o.status in ('COMPLETED','FAILED','BLOCKED','CANCELLED') and exists(select 1 from job_queue j where j.orchestration_run_id=o.id and j.status in ('QUEUED','RUNNING'))) = 0
      and (select count(*) from engineering_execution_queue q where q.status in ('QUEUED','RUNNING')) = 0
      and (select count(*) from engineering_conclusion_traces t where t.trace_status not in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE') and (coalesce(jsonb_array_length(t.evidence_refs),0)=0 or coalesce(jsonb_array_length(t.fact_refs),0)=0)) = 0
      and (select count(*) from engineering_contradictions c where c.blocking=true and coalesce(c.status,'') not in ('RESOLVED','CLOSED','ACCEPTED')) = 0
      and v_accepting_final_without_trace = 0
      then 'PASS' else 'BLOCK' end,
    'terminal_orchestration_active_jobs',(select count(*) from orchestration_runs o where o.status in ('COMPLETED','FAILED','BLOCKED','CANCELLED') and exists(select 1 from job_queue j where j.orchestration_run_id=o.id and j.status in ('QUEUED','RUNNING'))),
    'engineering_execution_active_jobs',(select count(*) from engineering_execution_queue q where q.status in ('QUEUED','RUNNING')),
    'untraceable_conclusions',(select count(*) from engineering_conclusion_traces t where t.trace_status not in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE') and (coalesce(jsonb_array_length(t.evidence_refs),0)=0 or coalesce(jsonb_array_length(t.fact_refs),0)=0)),
    'blocking_contradictions',(select count(*) from engineering_contradictions c where c.blocking=true and coalesce(c.status,'') not in ('RESOLVED','CLOSED','ACCEPTED')),
    'accepting_final_audits_without_traces',v_accepting_final_without_trace,
    'captured_at',now()
  ) into r;
  return r;
end;
$function$;

revoke all on function public.engineer_os_integrity_snapshot() from public, anon, authenticated;
grant execute on function public.engineer_os_integrity_snapshot() to service_role;