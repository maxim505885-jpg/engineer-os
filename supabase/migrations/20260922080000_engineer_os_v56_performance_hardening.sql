-- ENGINEER OS V56
-- Targeted performance hardening based on Supabase Advisor.
-- No unused indexes are removed in this migration; usage data is workload-dependent.

create index if not exists document_ingestion_runs_owner_id_fk_idx
  on public.document_ingestion_runs(owner_id);

create index if not exists engineering_conclusion_traces_analysis_run_id_fk_idx
  on public.engineering_conclusion_traces(analysis_run_id);

create index if not exists engineering_conclusion_traces_task_id_fk_idx
  on public.engineering_conclusion_traces(task_id);

create index if not exists engineering_validation_gates_task_id_fk_idx
  on public.engineering_validation_gates(task_id);

create index if not exists engineering_validation_gates_validation_id_fk_idx
  on public.engineering_validation_gates(validation_id);

create index if not exists model_batch_jobs_provider_id_fk_idx
  on public.model_batch_jobs(provider_id);

create index if not exists model_health_events_endpoint_id_fk_idx
  on public.model_health_events(endpoint_id);

create index if not exists model_health_events_provider_id_fk_idx
  on public.model_health_events(provider_id);

create index if not exists model_result_cache_provider_id_fk_idx
  on public.model_result_cache(provider_id);

create index if not exists model_router_runs_selected_provider_id_fk_idx
  on public.model_router_runs(selected_provider_id);

drop policy if exists engineer_os_owner_self on public.engineer_os_owner;
create policy engineer_os_owner_self
  on public.engineer_os_owner
  for select to authenticated
  using (owner_id = (select auth.uid()));

drop policy if exists user_profiles_self_select on public.user_profiles;
create policy user_profiles_self_select
  on public.user_profiles
  for select to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists user_profiles_self_insert on public.user_profiles;
create policy user_profiles_self_insert
  on public.user_profiles
  for insert to authenticated
  with check (user_id = (select auth.uid()));

drop policy if exists user_profiles_self_update on public.user_profiles;
create policy user_profiles_self_update
  on public.user_profiles
  for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

drop policy if exists learning_member on public.learning_events;

drop index if exists public.idx_engineering_result_validations_run_task_status;
