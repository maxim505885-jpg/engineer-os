-- ENGINEER OS V52
-- Security hardening: restrict internal SECURITY DEFINER RPC execution
-- to service_role. These functions are backend/internal primitives.

revoke execute on function public.enforce_orchestration_terminal_cleanup() from public, anon, authenticated;
revoke execute on function public.finalize_job_atomic(uuid,text,jsonb,text) from public, anon, authenticated;
revoke execute on function public.claim_engineer_os_owner() from public, anon, authenticated;
revoke execute on function public.create_personal_engineer_project() from public, anon, authenticated;
revoke execute on function public.create_project_with_membership(text,text) from public, anon, authenticated;

grant execute on function public.enforce_orchestration_terminal_cleanup() to service_role;
grant execute on function public.finalize_job_atomic(uuid,text,jsonb,text) to service_role;
grant execute on function public.claim_engineer_os_owner() to service_role;
grant execute on function public.create_personal_engineer_project() to service_role;
grant execute on function public.create_project_with_membership(text,text) to service_role;
