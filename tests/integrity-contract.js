#!/usr/bin/env node
const fs = require("node:fs");

const path = "supabase/migrations/20260922063948_engineer_os_v46_integrity_snapshot.sql";
if (!fs.existsSync(path)) throw new Error("v46 migration missing");

const sql = fs.readFileSync(path, "utf8");
const assert = (ok, message) => { if (!ok) throw new Error(message); };

assert(/engineer_os_integrity_snapshot/.test(sql), "integrity snapshot function missing");
assert(/terminal_orchestration_with_active_jobs/.test(sql), "terminal-job invariant missing");
assert(/duplicate_active_stages/.test(sql), "duplicate-stage invariant missing");
assert(/unvalidated_claims/.test(sql), "claim validation debt check missing");
assert(/blocking_contradictions/.test(sql), "blocking contradiction check missing");
assert(/revoke all on function public\.engineer_os_integrity_snapshot/i.test(sql), "public execute revoke missing");
assert(/grant execute on function public\.engineer_os_integrity_snapshot\(\) to service_role/i.test(sql), "service_role grant missing");

console.log("ENGINEER OS integrity contract: PASS");
