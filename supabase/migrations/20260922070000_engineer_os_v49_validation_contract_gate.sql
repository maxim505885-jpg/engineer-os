create or replace function public.validation_contract_gate(p_orchestration_run_id uuid, p_stage text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $function$
declare
  v_validation_count int := 0;
  v_validation_pass int := 0;
  v_validation_block int := 0;
  v_red_team_completed int := 0;
  v_traceability jsonb := '{}'::jsonb;
  v_status text := 'PASS';
begin
  if p_stage not in ('RED_TEAM','FINAL_AUDIT') then
    return jsonb_build_object(
      'gate','VALIDATION_CONTRACT',
      'stage',p_stage,
      'status','PASS',
      'not_applicable',true
    );
  end if;

  select count(*),
         count(*) filter (where status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')),
         count(*) filter (where status in ('BLOCK','ERROR','FAILED'))
    into v_validation_count, v_validation_pass, v_validation_block
  from engineering_result_validations
  where orchestration_run_id=p_orchestration_run_id;

  v_traceability := public.claim_evidence_traceability_gate(p_orchestration_run_id);

  select count(*)
    into v_red_team_completed
  from orchestration_stage_results
  where orchestration_run_id=p_orchestration_run_id
    and stage='RED_TEAM'
    and status='COMPLETED';

  if v_validation_count=0 or v_validation_pass=0 or v_validation_block>0 then
    v_status := 'BLOCK';
  end if;

  if coalesce(v_traceability->>'status','BLOCK') <> 'PASS' then
    v_status := 'BLOCK';
  end if;

  if p_stage='FINAL_AUDIT' and v_red_team_completed=0 then
    v_status := 'BLOCK';
  end if;

  return jsonb_build_object(
    'gate','VALIDATION_CONTRACT',
    'stage',p_stage,
    'status',v_status,
    'contract','RESULT_VALIDATION -> EVIDENCE -> TRACEABILITY -> RED_TEAM -> FINAL_AUDIT',
    'result_validation_count',v_validation_count,
    'result_validation_pass',v_validation_pass,
    'result_validation_block',v_validation_block,
    'traceability',v_traceability,
    'red_team_completed',v_red_team_completed
  );
end;
$function$;

create or replace function public.guard_red_team_final_audit(p_orchestration_run_id uuid, p_stage text)
returns boolean
language plpgsql
security definer
set search_path = public
as $function$
declare
  v_gate jsonb;
begin
  if p_stage not in ('RED_TEAM','FINAL_AUDIT') then return true; end if;
  v_gate := public.validation_contract_gate(p_orchestration_run_id,p_stage);
  return (v_gate->>'status')='PASS';
end
$function$;

revoke all on function public.validation_contract_gate(uuid,text) from public, anon, authenticated;
grant execute on function public.validation_contract_gate(uuid,text) to service_role;

revoke all on function public.guard_red_team_final_audit(uuid,text) from public, anon, authenticated;
grant execute on function public.guard_red_team_final_audit(uuid,text) to service_role;
