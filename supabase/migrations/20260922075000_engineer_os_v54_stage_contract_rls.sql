-- ENGINEER OS V54
-- engineering_stage_contracts is an internal backend contract table.
-- It is not a user-facing table, so no authenticated/anon policy is created.
-- service_role remains the sole database role with SELECT access.

alter table public.engineering_stage_contracts enable row level security;
alter table public.engineering_stage_contracts force row level security;

revoke all on public.engineering_stage_contracts from public, anon, authenticated;
grant select on public.engineering_stage_contracts to service_role;
