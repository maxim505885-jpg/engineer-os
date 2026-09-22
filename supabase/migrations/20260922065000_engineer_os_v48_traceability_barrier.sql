-- ENGINEER OS V48: mandatory Claim -> Evidence barrier
create or replace function public.enforce_traceability_barrier(p_orchestration_run_id uuid)
returns jsonb language plpgsql security definer set search_path=public as $$
declare v_gate jsonb; v_red int; v_final int;
begin
  v_gate := public.claim_evidence_traceability_gate(p_orchestration_run_id);
  select count(*) into v_red from orchestration_stage_results where orchestration_run_id=p_orchestration_run_id and stage='RED_TEAM' and status='COMPLETED';
  select count(*) into v_final from orchestration_stage_results where orchestration_run_id=p_orchestration_run_id and stage='FINAL_AUDIT' and status='COMPLETED';
  return jsonb_build_object('gate',v_gate,'red_team_completed',v_red>0,'final_audit_completed',v_final>0,
    'barrier_status',case when (v_gate->>'status')='PASS' and v_red>0 and v_final>0 then 'PASS' else 'BLOCK' end);
end $$;
revoke all on function public.enforce_traceability_barrier(uuid) from public,anon,authenticated;
grant execute on function public.enforce_traceability_barrier(uuid) to service_role;

create or replace function public.guard_red_team_final_audit(p_orchestration_run_id uuid,p_stage text)
returns boolean language plpgsql security definer set search_path=public as $$
declare v_gate jsonb;
begin
  if p_stage not in ('RED_TEAM','FINAL_AUDIT') then return true; end if;
  v_gate := public.claim_evidence_traceability_gate(p_orchestration_run_id);
  return (v_gate->>'status')='PASS';
end $$;
revoke all on function public.guard_red_team_final_audit(uuid,text) from public,anon,authenticated;
grant execute on function public.guard_red_team_final_audit(uuid,text) to service_role;

create or replace function public.block_untraceable_red_final()
returns trigger language plpgsql security definer set search_path=public as $$
declare v_gate jsonb;
begin
  if NEW.stage in ('RED_TEAM','FINAL_AUDIT') and NEW.status in ('QUEUED','RUNNING','COMPLETED') then
    v_gate := public.claim_evidence_traceability_gate(NEW.orchestration_run_id);
    if (v_gate->>'status') <> 'PASS' then return null; end if;
  end if;
  return NEW;
end $$;
revoke all on function public.block_untraceable_red_final() from public,anon,authenticated;
grant execute on function public.block_untraceable_red_final() to service_role;
drop trigger if exists trg_traceability_barrier_red_final on public.orchestration_stage_results;
create trigger trg_traceability_barrier_red_final before insert or update on public.orchestration_stage_results
for each row execute function public.block_untraceable_red_final();
