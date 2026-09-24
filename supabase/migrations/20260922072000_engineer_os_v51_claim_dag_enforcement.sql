-- ENGINEER OS V51
-- Bind the declarative stage DAG contract to physical job claiming.
-- A declared pipeline stage cannot be claimed until every declared dependency
-- has a COMPLETED orchestration_stage_results row.

create index if not exists idx_orchestration_stage_results_run_stage_completed
on public.orchestration_stage_results(orchestration_run_id, stage)
where status='COMPLETED';

create or replace function public.claim_next_job(p_worker text)
returns setof public.job_queue
language plpgsql
security definer
set search_path=public
as $function$
declare
  v_job_id uuid;
  v_run_id uuid;
begin
  select j.id, j.orchestration_run_id
    into v_job_id, v_run_id
  from public.job_queue j
  join public.orchestration_runs o on o.id=j.orchestration_run_id
  join public.engineering_tasks t on t.id=j.task_id
  where j.status='QUEUED'
    and j.available_at<=now()
    and o.status in ('QUEUED','RUNNING')
    and t.status='RUNNING'
    and (
      j.depends_on_job_id is null
      or exists (
        select 1
        from public.job_queue d
        where d.id=j.depends_on_job_id
          and d.status='COMPLETED'
      )
    )
    and (
      j.depends_on_group is null
      or not exists (
        select 1
        from public.job_queue d
        where d.orchestration_run_id=j.orchestration_run_id
          and d.parallel_group=j.depends_on_group
          and d.status<>'COMPLETED'
      )
    )
    and not exists (
      select 1
      from public.job_queue active_stage
      where active_stage.orchestration_run_id=j.orchestration_run_id
        and active_stage.stage=j.stage
        and active_stage.status='RUNNING'
        and active_stage.id<>j.id
    )
    and (
      not exists (
        select 1
        from public.engineering_stage_contracts c
        where c.stage=j.stage
      )
      or (
        select public.stage_dag_contract_gate(
          j.orchestration_run_id,
          j.stage
        )->>'status'
      )='PASS'
    )
  order by j.priority asc,j.created_at asc
  for update of j skip locked
  limit 1;

  if v_job_id is null then
    return;
  end if;

  update public.orchestration_runs
  set status='RUNNING',updated_at=now()
  where id=v_run_id and status='QUEUED';

  update public.job_queue
  set status='RUNNING',
      attempts=attempts+1,
      locked_at=now(),
      locked_by=p_worker,
      worker_heartbeat_at=now(),
      updated_at=now()
  where id=v_job_id and status='QUEUED';

  return query
  select j.*
  from public.job_queue j
  where j.id=v_job_id and j.status='RUNNING';
end
$function$;

revoke all on function public.claim_next_job(text) from public,anon,authenticated;
grant execute on function public.claim_next_job(text) to service_role;
