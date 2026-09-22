create table if not exists public.engineering_stage_contracts (
  stage text primary key,
  depends_on_stages jsonb not null default '[]'::jsonb,
  critical boolean not null default true,
  terminal boolean not null default false,
  created_at timestamptz not null default now(),
  constraint engineering_stage_contracts_deps_array check (jsonb_typeof(depends_on_stages)='array')
);

insert into public.engineering_stage_contracts(stage,depends_on_stages,critical,terminal) values
('SCOPE_CONTROL','[]',true,false),
('DOCUMENT_ANALYSIS','["SCOPE_CONTROL"]',true,false),
('ENGINEER_CORE','["DOCUMENT_ANALYSIS"]',true,false),
('EVIDENCE_ANALYSIS','["DOCUMENT_ANALYSIS","ENGINEER_CORE"]',true,false),
('NORMATIVE_CONTROL','["ENGINEER_CORE","EVIDENCE_ANALYSIS"]',true,false),
('ENGINEERING_TRACEABILITY','["EVIDENCE_ANALYSIS","NORMATIVE_CONTROL"]',true,false),
('RESULT_VALIDATION','["ENGINEERING_TRACEABILITY","NORMATIVE_CONTROL"]',true,false),
('HANDOFF','["RESULT_VALIDATION"]',true,false),
('RED_TEAM','["RESULT_VALIDATION","ENGINEERING_TRACEABILITY"]',true,false),
('REPORT_QUALITY','["RED_TEAM","HANDOFF"]',true,false),
('FINAL_AUDIT','["RED_TEAM","REPORT_QUALITY"]',true,true)
on conflict (stage) do update set depends_on_stages=excluded.depends_on_stages,critical=excluded.critical,terminal=excluded.terminal;

revoke all on public.engineering_stage_contracts from public, anon, authenticated;
grant select on public.engineering_stage_contracts to service_role;

create or replace function public.stage_dag_contract_gate(p_orchestration_run_id uuid, p_stage text)
returns jsonb language plpgsql security definer set search_path=public as $function$
declare v_deps jsonb; v_missing jsonb := '[]'::jsonb; v_invalid int := 0; v_status text := 'PASS';
begin
  select depends_on_stages into v_deps from engineering_stage_contracts where stage=p_stage;
  if v_deps is null then return jsonb_build_object('gate','STAGE_DAG_CONTRACT','stage',p_stage,'status','BLOCK','reason','STAGE_NOT_DECLARED'); end if;
  select count(*) into v_invalid from jsonb_array_elements_text(v_deps) d(dep)
  where not exists (select 1 from engineering_stage_contracts c where c.stage=d.dep);
  if v_invalid>0 then return jsonb_build_object('gate','STAGE_DAG_CONTRACT','stage',p_stage,'status','BLOCK','reason','INVALID_CONTRACT'); end if;
  select coalesce(jsonb_agg(d.dep order by d.dep),'[]'::jsonb) into v_missing
  from jsonb_array_elements_text(v_deps) d(dep)
  where not exists (select 1 from orchestration_stage_results s where s.orchestration_run_id=p_orchestration_run_id and s.stage=d.dep and s.status='COMPLETED');
  if jsonb_array_length(v_missing)>0 then v_status := 'BLOCK'; end if;
  return jsonb_build_object('gate','STAGE_DAG_CONTRACT','stage',p_stage,'status',v_status,'dependencies',v_deps,'missing_dependencies',v_missing);
end;
$function$;

create or replace function public.guard_stage_dag_contract()
returns trigger language plpgsql security definer set search_path=public as $function$
declare v_gate jsonb;
begin
  if new.status in ('RUNNING','COMPLETED') then
    v_gate := public.stage_dag_contract_gate(new.orchestration_run_id,new.stage);
    if v_gate->>'status' <> 'PASS' then return null; end if;
  end if;
  return new;
end;
$function$;

drop trigger if exists trg_stage_dag_contract on public.orchestration_stage_results;
create trigger trg_stage_dag_contract before insert or update on public.orchestration_stage_results
for each row execute function public.guard_stage_dag_contract();

revoke all on function public.stage_dag_contract_gate(uuid,text) from public, anon, authenticated;
grant execute on function public.stage_dag_contract_gate(uuid,text) to service_role;
revoke all on function public.guard_stage_dag_contract() from public, anon, authenticated;
grant execute on function public.guard_stage_dag_contract() to service_role;