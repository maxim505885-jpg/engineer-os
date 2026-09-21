#!/usr/bin/env node
const fs = require("node:fs");

const required = [
  "index.html",
  "app.js",
  "auth-recovery.js",
  "styles.css",
  "Dockerfile",
  "nginx.conf.template",
];

for (const file of required) {
  if (!fs.existsSync(file)) throw new Error(`Missing required file: ${file}`);
}

const html = fs.readFileSync("index.html", "utf8");
const app = fs.readFileSync("app.js", "utf8");
const css = fs.readFileSync("styles.css", "utf8");
const docker = fs.readFileSync("Dockerfile", "utf8");
const nginx = fs.readFileSync("nginx.conf.template", "utf8");

const assert = (ok, message) => {
  if (!ok) throw new Error(message);
};

assert(/<html\b[^>]*lang="ru"/i.test(html), "index.html: lang=ru missing");
assert(/<meta\s+charset="utf-8"/i.test(html), "index.html: UTF-8 meta missing");
assert(/<title>ENGINEER OS<\/title>/i.test(html), "index.html: title missing");
assert(/id="nav"/.test(html), "index.html: navigation missing");
assert(/id="page"/.test(html), "index.html: page mount missing");
assert(/id="projectSelect"/.test(html), "index.html: project selector missing");
assert(/id="connectionText"/.test(html), "index.html: connection status missing");

assert(/createClient\(/.test(app), "app.js: Supabase client initialization missing");
assert(/function\s+loadProjects\s*\(/.test(app), "app.js: project loading missing");
assert(/function\s+renderPipeline\s*\(/.test(app), "app.js: pipeline view missing");
assert(/function\s+runSecurityTest\s*\(/.test(app), "app.js: security self-test missing");
assert(/function\s+runPipelineTest\s*\(/.test(app), "app.js: pipeline self-test missing");
assert(/function\s+runModelTest\s*\(/.test(app), "app.js: model self-test missing");
assert(/function\s+runRecovery\s*\(/.test(app), "app.js: recovery action missing");
assert(/function\s+esc\s*\(/.test(app), "app.js: HTML escaping helper missing");
assert(/supabase\.rpc\("create_project_with_membership"/.test(app), "app.js: project creation RPC missing");
assert(!/service_role/i.test(app), "app.js: service-role secret must not be present in frontend");
assert(!/sk-[A-Za-z0-9_-]{20,}/.test(app), "app.js: OpenAI secret-like token detected in frontend");

assert(/nginx:alpine/.test(docker), "Dockerfile: nginx:alpine base image missing");
assert(/EXPOSE\s+8080/.test(docker), "Dockerfile: port 8080 missing");
assert(/__PORT__/.test(nginx), "nginx.conf.template: dynamic port placeholder missing");
assert(/try_files\s+\$uri\s+\$uri\/\s+\/index\.html/.test(nginx), "nginx.conf.template: SPA fallback missing");

console.log("ENGINEER OS regression suite: PASS");
console.log(`Checked ${required.length} required files and core runtime invariants.`);
