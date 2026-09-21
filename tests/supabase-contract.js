#!/usr/bin/env node
const fs = require("node:fs");

const app = fs.readFileSync("app.js", "utf8");

const tableContract = [
  "projects","documents","evidence","engineering_findings","engineering_tasks",
  "engineering_measurements","structural_elements","technical_assignment_items",
  "orchestration_runs","engineering_locations","engineering_result_validations",
  "engineering_contradictions","engineering_result_handoffs",
  "engineering_execution_queue","job_queue","project_recovery_runs","agents","user_profiles"
];
const edgeFunctionContract = [
  "security-self-test-v1","pipeline-self-test-v1","model-connection-test-v1","autonomous-recovery-v28"
];
const rpcContract = [
  "create_project_with_membership","claim_engineer_os_owner","create_personal_engineer_project"
];

const missing = [];

for (const name of tableContract) {
  const referenced = app.includes('db("' + name + '"') || app.includes('from("' + name + '"');
  if (!referenced) missing.push("table not referenced as expected: " + name);
}

for (const name of edgeFunctionContract) {
  if (!app.includes('functions.invoke("' + name + '"')) {
    missing.push("edge function contract missing from frontend: " + name);
  }
}

for (const name of rpcContract) {
  if (!app.includes('rpc("' + name + '"')) {
    missing.push("RPC contract missing from frontend: " + name);
  }
}

if (missing.length) {
  console.error("ENGINEER OS Supabase contract: FAIL");
  for (const item of missing) console.error(" - " + item);
  process.exit(1);
}

console.log("ENGINEER OS Supabase contract: PASS");
console.log("Validated " + tableContract.length + " table contracts, " +
  edgeFunctionContract.length + " Edge Function contracts and " +
  rpcContract.length + " RPC contracts.");
