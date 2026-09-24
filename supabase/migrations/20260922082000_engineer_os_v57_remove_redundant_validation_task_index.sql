-- ENGINEER OS V57
-- engineering_result_validations already has eng_result_validations_task_idx
-- on (task_id, created_at DESC), which covers task_id lookups.
-- The separate FK-only task_id index was unused and redundant.
drop index if exists public.engineering_result_validations_task_id_fk_idx;
