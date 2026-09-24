-- ENGINEER OS V55
-- Cover foreign keys identified by Supabase Performance Advisor.
-- No unused-index removals are performed in this migration.

create index if not exists document_ingestion_runs_owner_id_idx
  on public.document_ingestion_runs(owner_id);

create index if not exists engineering_conclusion_traces_analysis_run_id_idx
  on public.engineering_conclusion_traces(analysis_run_id);

create index if not exists engineering_conclusion_traces_task_id_idx
  on public.engineering_conclusion_traces(task_id);

create index if not exists engineering_validation_gates_task_id_idx
  on public.engineering_validation_gates(task_id);

create index if not exists engineering_validation_gates_validation_id_idx
  on public.engineering_validation_gates(validation_id);

create index if not exists model_batch_jobs_provider_id_idx
  on public.model_batch_jobs(provider_id);

create index if not exists model_health_events_endpoint_id_idx
  on public.model_health_events(endpoint_id);

create index if not exists model_health_events_provider_id_idx
  on public.model_health_events(provider_id);

create index if not exists model_result_cache_provider_id_idx
  on public.model_result_cache(provider_id);

create index if not exists model_router_runs_selected_provider_id_idx
  on public.model_router_runs(selected_provider_id);
