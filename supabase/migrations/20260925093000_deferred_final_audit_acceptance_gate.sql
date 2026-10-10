-- Fail closed at the database boundary: accepting FINAL_AUDIT requires evidence and a valid conclusion trace.
create or replace function public.enforce_final_audit_acceptance_integrity()
returns trigger
language plpgsql
security definer
set search_path=public
as $function$
begin
  if NEW.status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE','ACCEPTED_WITH_REMARKS') then
    if jsonb_typeof(NEW.evidence) <> 'object' then
      raise exception 'FINAL_AUDIT_ACCEPTANCE_BLOCKED: evidence must be an object';
    end if;
    if not exists (
      select 1 from public.engineering_conclusion_traces t
      where t.task_id = NEW.task_id
        and t.trace_status in ('PASS','ACCEPTED','ACCEPTED_ALTERNATIVE')
        and jsonb_typeof(t.fact_refs) = 'array' and jsonb_array_length(t.fact_refs) > 0
        and jsonb_typeof(t.evidence_refs) = 'array' and jsonb_array_length(t.evidence_refs) > 0
    ) then
      raise exception 'FINAL_AUDIT_ACCEPTANCE_BLOCKED: no valid conclusion trace for task %', NEW.task_id;
    end if;
  end if;
  return NEW;
end;
$function$;

drop trigger if exists trg_final_audit_acceptance_integrity on public.final_audit_results;
create constraint trigger trg_final_audit_acceptance_integrity
after insert or update of status, evidence, task_id
on public.final_audit_results
deferrable initially deferred
for each row
execute function public.enforce_final_audit_acceptance_integrity();

revoke all on function public.enforce_final_audit_acceptance_integrity() from public, anon, authenticated;
grant execute on function public.enforce_final_audit_acceptance_integrity() to service_role;
