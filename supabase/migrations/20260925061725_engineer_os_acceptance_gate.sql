create or replace function public.claim_engineer_os_acceptance_gate(p_task_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=public
as $function$
declare
  v_task public.engineering_tasks%rowtype;
  v_integrity jsonb;
  v_required jsonb;
  v_missing jsonb := '[]'::jsonb;
  v_final_audit_ok boolean;
  v_trace_ok boolean;
  v_report_ok boolean := true;
  v_normative_ok boolean := true;
  v_calculation_ok boolean := true;
  v_analysis_run_id uuid;
begin
  select * into v_task from public.engineering_tasks where id = p_task_id;
  if not found then
    return jsonb_build_object('status','BLOCK','task_id',p_task_id,'reason','ENGINEERING_TASK_NOT_FOUND');
  end if;

  v_integrity := public.engineer_os_integrity_snapshot();
  if coalesce(v_integrity->>'status','BLOCK') <> 'PASS' then
    return jsonb_build_object('status','BLOCK','task_id',p_task_id,
      'reason','GLOBAL_INTEGRITY_BLOCK','integrity',v_integrity);
  end if;

  v_final_audit_ok := exists (
    select 1 from public.final_audit_results f
    where f.task_id = p_task_id
      and f.status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE','ACCEPTED_WITH_REMARKS')
      and jsonb_typeof(f.evidence) = 'object'
  );

  v_trace_ok := exists (
    select 1 from public.engineering_conclusion_traces t
    where t.task_id = p_task_id
      and t.trace_status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
      and jsonb_typeof(t.fact_refs) = 'array' and jsonb_array_length(t.fact_refs) > 0
      and jsonb_typeof(t.evidence_refs) = 'array' and jsonb_array_length(t.evidence_refs) > 0
  );

  if not v_final_audit_ok then v_missing := v_missing || jsonb_build_array('FINAL_AUDIT'); end if;
  if not v_trace_ok then v_missing := v_missing || jsonb_build_array('CONCLUSION_TRACE'); end if;

  v_analysis_run_id := (
    select ar.id from public.analysis_runs ar
    where ar.task_id = p_task_id order by ar.created_at desc limit 1
  );
  v_required := coalesce(v_task.prerequisites, '[]'::jsonb);

  if v_required ? 'report' then
    v_report_ok := exists (
      select 1 from public.report_quality_runs r
      where r.task_id = p_task_id
        and r.status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE','COMPLETED')
    );
    if not v_report_ok then v_missing := v_missing || jsonb_build_array('REPORT_QUALITY'); end if;
  end if;

  if v_required ? 'normative' then
    v_normative_ok := exists (
      select 1 from public.normative_validations n
      where n.project_id = v_task.project_id
        and (v_analysis_run_id is null or n.analysis_run_id = v_analysis_run_id)
        and n.validation_status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
    );
    if not v_normative_ok then v_missing := v_missing || jsonb_build_array('NORMATIVE_VERIFICATION'); end if;
  end if;

  if v_required ? 'calculation' then
    v_calculation_ok := exists (
      select 1 from public.calculation_tasks c
      where c.task_id = p_task_id
        and c.input_status in ('PASS','ACCEPTED','READY')
        and c.model_status in ('PASS','ACCEPTED','READY')
        and c.calculation_status in ('PASS','ACCEPTED','COMPLETED')
        and c.verification_status in ('PASS','ACCEPTED')
        and c.conclusion_status in ('PASS','ACCEPTED')
    )
    and exists (
      select 1 from public.calculation_verifications v
      join public.calculation_tasks c on c.id = v.calculation_task_id
      where c.task_id = p_task_id
        and v.status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
        and jsonb_typeof(v.verification_basis) = 'object'
    )
    and exists (
      select 1 from public.calculation_model_audits a
      join public.calculation_tasks c on c.id = a.calculation_task_id
      where c.task_id = p_task_id
        and a.status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
        and jsonb_typeof(a.evidence) = 'object'
    );
    if not v_calculation_ok then v_missing := v_missing || jsonb_build_array('CALCULATION_VERIFICATION'); end if;
  end if;

  if jsonb_array_length(v_missing) > 0 then
    return jsonb_build_object('status','BLOCK','task_id',p_task_id,
      'reason','DOMAIN_ACCEPTANCE_INCOMPLETE','missing',v_missing,'integrity',v_integrity);
  end if;

  return jsonb_build_object('status','PASS','task_id',p_task_id,
    'missing','[]'::jsonb,'integrity',v_integrity);
end;
$function$;

revoke all on function public.claim_engineer_os_acceptance_gate(uuid) from public, anon, authenticated;
grant execute on function public.claim_engineer_os_acceptance_gate(uuid) to service_role;
