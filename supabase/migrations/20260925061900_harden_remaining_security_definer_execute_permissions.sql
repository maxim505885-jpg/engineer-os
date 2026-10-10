revoke all on function public.claim_engineering_execution_queue(uuid, integer) from public, anon, authenticated;
revoke all on function public.claim_engineering_execution_queue(uuid, integer, text) from public, anon, authenticated;
revoke all on function public.claim_engineering_execution_queue(uuid, integer, uuid) from public, anon, authenticated;
revoke all on function public.finish_engineering_execution_queue(uuid, text, jsonb, jsonb, boolean) from public, anon, authenticated;
revoke all on function public.sync_analysis_run_from_task_terminal() from public, anon, authenticated;
