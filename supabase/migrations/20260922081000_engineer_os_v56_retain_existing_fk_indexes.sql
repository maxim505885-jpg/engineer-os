-- ENGINEER OS V56
-- Supabase's FK advisor identified 10 constraints, but the database already
-- contained covering indexes with the *_fk_idx names. V55 added redundant
-- copies; V56 removes only those redundant copies.
-- Existing *_fk_idx indexes remain intact.

drop index if exists public.document_ingestion_runs_owner_id_idx;
drop index if exists public.engineering_conclusion_traces_analysis_run_id_idx;
drop index if exists public.engineering_conclusion_traces_task_id_idx;
drop index if exists public.engineering_validation_gates_task_id_idx;
drop index if exists public.engineering_validation_gates_validation_id_idx;
drop index if exists public.model_batch_jobs_provider_id_idx;
drop index if exists public.model_health_events_endpoint_id_idx;
drop index if exists public.model_health_events_provider_id_idx;
drop index if exists public.model_result_cache_provider_id_idx;
drop index if exists public.model_router_runs_selected_provider_id_idx;
