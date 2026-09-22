-- ENGINEER OS v46: integrity snapshot
-- Read-only health/integrity gate. Does not mutate engineering state.

create or replace function public.engineer_os_integrity_snapshot()
returns jsonb
language sql
security definer
set search_path=public
as $$
with duplicate_stages as (
  select orchestration_run_id, stage, count(*) as n
  from job_queue
  where status in ('QUEUED','RUNNING')
  group by orchestration_run_id, stage
  having count(*) > 1
),
terminal_active as (
  select count(*) n
  from job_queue j
  join orchestration_runs o on o.id=j.orchestration_run_id
  where o.status in ('COMPLETED','FAILED','BLOCKED','CANCELLED')
    and j.status in ('QUEUED','RUNNING')
),
active_counts as (
  select
    (select count(*) from orchestration_runs where status in ('QUEUED','RUNNING')) orchestrations,
    (select count(*) from job_queue where status in ('QUEUED','RUNNING')) jobs,
    (select count(*) from engineering_task_runs where status in ('QUEUED','RUNNING')) task_runs,
    (select count(*) from engineering_tasks where status='PENDING') pending_tasks
)
select jsonb_build_object(
  'generated_at', now(),
  'status', case when (select n from terminal_active)=0
      and not exists(select 1 from duplicate_stages)
    then 'PASS' else 'BLOCK' end,
  'active', (select to_jsonb(ac) from active_counts ac),
  'violations', jsonb_build_object(
    'terminal_orchestration_with_active_jobs',(select n from terminal_active),
    'duplicate_active_stages',coalesce((select jsonb_agg(to_jsonb(ds)) from duplicate_stages ds),'[]'::jsonb),
    'unvalidated_claims',(select count(*) from evidence_claims where status is null or status in ('PENDING','UNVALIDATED')),
    'blocking_contradictions',(select count(*) from engineering_contradictions where blocking=true and status not in ('RESOLVED','CLOSED'))
  )
);
$$;

revoke all on function public.engineer_os_integrity_snapshot() from public, anon, authenticated;
grant execute on function public.engineer_os_integrity_snapshot() to service_role;

comment on function public.engineer_os_integrity_snapshot() is
'ENGINEER OS integrity gate: detects terminal-run active jobs and duplicate active stages, and reports evidence/contradiction debt without changing state.';
