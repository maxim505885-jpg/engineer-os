-- ENGINEER OS V58
-- Remove only indexes proven redundant by a stronger covering index
-- on the same leftmost key(s). No workload-specific indexes are removed.

drop index if exists public.engineering_trace_audits_analysis_run_id_fk_idx;
drop index if exists public.report_quality_runs_document_id_fk_idx;
drop index if exists public.engineering_task_runs_task_id_fk_idx;
drop index if exists public.engineering_result_handoffs_target_task_id_fk_idx;
drop index if exists public.idx_engineering_result_handoffs_run;
drop index if exists public.job_queue_depends_on_job_id_fk_idx;
