const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

test('Office image actions preserve source job, unit and image ordinal', () => {
  const source=fs.readFileSync(path.join(__dirname,'../engineering/local_app/ui/app.js'),'utf8');
  const match=source.match(/function renderOfficeImages\(box,ref\)\{[\s\S]*?\n\}/);
  assert.ok(match,'Source-linked image controls missing');
  const calls=[],nodes=[];
  const context={node:(tag,text)=>({tag,text}),showPreview:value=>calls.push(value),sourceLocation:()=> 'абзац 3'};
  vm.createContext(context);vm.runInContext(match[0],context);
  context.renderOfficeImages({append:n=>nodes.push(n)},{source_job:'source-job',logical_unit:3,locator:{images:[{image:1,status:'BOUND_PACKAGE_IMAGE',part:'word/media/a.png'},{image:2,status:'UNAVAILABLE',reason:'IMAGE_PART_MISSING'}]}});
  const button=nodes.find(n=>n.tag==='button');assert.ok(button);button.onclick();
  assert.equal(calls[0].office_job,'source-job');assert.equal(calls[0].logical_unit,3);assert.equal(calls[0].image,1);
  assert.equal(nodes.filter(n=>n.tag==='button').length,1);
  assert.ok(nodes.some(n=>n.text.includes('IMAGE_PART_MISSING')));
});

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

test('browser fixture waits for child closure after forced shutdown', async () => {
  const {EventEmitter}=require('node:events');
  const source=fs.readFileSync(path.join(__dirname,'../e2e/local_document_intake_ui_smoke.cjs'),'utf8');
  const cleanup=source.match(/\}finally\{([^\n]+)\}\n\}\)\(\)/);
  assert.ok(cleanup,'intake fixture cleanup missing');
  const child=new EventEmitter();child.exitCode=null;child.signalCode=null;let closed=false,removed=false;
  child.kill=signal=>{if(signal==='SIGKILL')setTimeout(()=>{closed=true;child.signalCode='SIGKILL';child.emit('exit');child.emit('close');},20);return true;};
  const helper=path.join(__dirname,'../e2e/stop_child.cjs');
  const context={browser:null,child,temp:'fixture',stopChild:fs.existsSync(helper)?child=>require(helper).stopChild(child,{graceMs:2,killWaitMs:200}):undefined,
    setTimeout:(fn,ms)=>setTimeout(fn,Math.min(ms,2)),clearTimeout,
    fs:{rmSync:()=>{assert.ok(closed,'Cleanup must wait for process closure after SIGKILL');removed=true;}}};
  vm.createContext(context);await vm.runInContext('(async()=>{'+cleanup[1]+'})()',context);assert.ok(removed);
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


test('Word auxiliary source buttons and table inventory show part and note identity', () => {
 const source=fs.readFileSync(path.join(__dirname,'../engineering/local_app/ui/app.js'),'utf8');
 const functions=source.slice(source.indexOf('function sourceLocation('),source.indexOf('function renderFiles('));
 const context={analysisViews:new Map(),renderAnalysisResume:()=>{},texts:[],
   node:(tag,text)=>{if(text!==undefined)context.texts.push(text);return {append:()=>{}};}};
 vm.createContext(context);vm.runInContext(functions,context);
 const body=context.sourceLocation({locator:{kind:'paragraph',part:'word/document.xml',paragraph:1}});
 const header=context.sourceLocation({locator:{kind:'paragraph',component:'header',part:'word/header1.xml',paragraph:1}});
 const note=context.sourceLocation({locator:{kind:'paragraph',component:'footnote',note_id:'7',part:'word/notes.xml',paragraph:1}});
 assert.notEqual(header,body);assert.notEqual(note,body);assert.match(header,/word\/header1.xml/);assert.match(note,/7/);
 context.renderAutomaticAnalysis({append:()=>{}},{id:'j',result:{document_analysis:{stage:'COMPLETED',sources:[{name:'report',coverage_manifest:{sheets:[],tables:[{table:'1',part:'word/document.xml',cells:2},{table:'1',part:'word/header1.xml',cells:1},{table:'1',part:'word/notes.xml',note_id:'7',cells:1}]}}]}}});
 assert.ok(context.texts.some(t=>t.includes('Таблица 1')&&t.includes('word/header1.xml')));
 assert.ok(context.texts.some(t=>t.includes('Таблица 1')&&t.includes('7')));
});
