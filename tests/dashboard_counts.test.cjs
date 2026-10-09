const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

test('local upload uses 256 MiB only for OOXML extensions', () => {
  const source=fs.readFileSync(path.join(__dirname,'../engineering/local_app/ui/app.js'),'utf8');
  const match=source.match(/function uploadLimitBytes\(name\)\{[^\n]+\}/);
  assert.ok(match,'local upload size policy missing');
  const context={};vm.createContext(context);vm.runInContext(match[0],context);
  assert.equal(context.uploadLimitBytes('report.DOCX'),256*1024*1024);
  assert.equal(context.uploadLimitBytes('table.xlsx'),256*1024*1024);
  assert.equal(context.uploadLimitBytes('report.docx.exe'),100*1024*1024);
});

test('late initial session list preserves user-created conversation', async () => {
  const source=fs.readFileSync(path.join(__dirname,'../engineering/local_app/ui/app.js'),'utf8');
  const initializer=source.match(/\(async\(\)=>\{try\{const list=await sessions\(\);[^\n]+pollStatus\(\);\}\)\(\);/);
  assert.ok(initializer,'local session initializer missing');
  for(const state of [{current:'user-created',creating:false},{current:null,creating:true}]){
    let release;const actions=[];
    const context={current:null,creating:false,sessions:()=>new Promise(resolve=>{release=resolve;}),
      switchSession:async id=>actions.push('switch:'+id),createSession:async()=>actions.push('create'),
      controls:()=>{},poll:()=>{},pollStatus:()=>{},error:error=>{throw error;}};
    vm.createContext(context);const initialized=vm.runInContext(initializer[0],context);
    Object.assign(context,state);release([{id:'old-conversation'}]);await initialized;
    assert.deepEqual(actions,[],'Late bootstrap response must preserve user action');
  }
});

function app(responses) {
  const calls = [];
  const elements = new Map();
  const client = {
    auth: {getSession: () => new Promise(() => {})},
    from(table) {
      const call = {table}; calls.push(call);
      return {
        select(columns, options) {call.columns = columns; call.options = options; return this;},
        eq(column, value) {call.filter = [column, value]; return this;},
        order() {return this;}, limit() {return this;},
        then(resolve, reject) {
          return new Promise(r => setTimeout(() => r(responses[table] || {data: [], count: 0, error: null}), 5)).then(resolve, reject);
        }
      };
    }
  };
  const context = vm.createContext({
    window: {supabase: {createClient: () => client}},
    document: {
      querySelectorAll: () => [],
      querySelector(selector) {
        if (!elements.has(selector)) elements.set(selector, {innerHTML: '', style: {}, addEventListener() {}});
        return elements.get(selector);
      }
    }, console, setTimeout
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8'), context);
  vm.runInContext("state.projectId='project-a';", context);
  return {context, calls, elements};
}

test('dashboard uses exact project counts above the old 1000-row limit', async () => {
  const {context, calls} = app({documents: {data: null, count: 1201, error: null}});
  const result = await vm.runInContext('counts()', context);
  assert.equal(result.documents, 1201);
  assert.equal(calls.length, 4);
  for (const call of calls) {
    assert.deepEqual(call.filter, ['project_id', 'project-a']);
    assert.equal(call.options.count, 'exact');
    assert.equal(call.options.head, true);
  }
});

test('dashboard starts all visible counter requests before any completes', async () => {
  const {context, calls} = app({});
  const pending = vm.runInContext('counts()', context);
  await Promise.resolve(); await Promise.resolve();
  const started = calls.length;
  await pending;
  assert.equal(started, 4);
});

test('unavailable evidence counts render as unknown rather than a false zero', async () => {
  const {context, elements} = app({evidence: {data: null, count: null, error: {message: 'access denied'}}});
  const result = await vm.runInContext('counts()', context);
  assert.equal(result.evidence, null);
  await vm.runInContext('renderDashboard()', context);
  const html = elements.get('#page').innerHTML;
  assert.match(html, /Доказательства<\/div><div class="metric">—<\/div>/);
  assert.match(html, /Не удалось получить данные/);
});

test('missing project never makes an unscoped request', async () => {
  const {context, calls} = app({});
  vm.runInContext('state.projectId=null', context);
  const result = await vm.runInContext('counts()', context);
  assert.equal(Object.keys(result).length, 0);
  assert.equal(calls.length, 0);
});
