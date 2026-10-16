'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process');const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-review-ui-'));let child,browser;
 try{
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,PYTHONUTF8:'1'}});
  const origin=await new Promise((resolve,reject)=>{let text='';const timer=setTimeout(()=>reject(Error('Startup timeout')),15000);child.stdout.on('data',data=>{text+=data;const found=text.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(Error('Server exited '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1366,height:950}});const errors=[];page.on('pageerror',error=>errors.push(error.message));
  // Hold bootstrap to exercise the same startup race seen on a fast CI browser.
  let releaseBootstrap;const bootstrapGate=new Promise(resolve=>releaseBootstrap=resolve);
  const bootstrapRequested=page.waitForRequest(request=>new URL(request.url()).pathname==='/api/sessions'&&request.method()==='GET');
  const bootstrapRoute=async route=>{if(route.request().method()==='GET')await bootstrapGate;await route.continue();};
  await page.route('**/api/sessions',bootstrapRoute);await page.goto(origin);await bootstrapRequested;
  assert.equal(await page.evaluate(()=>current),null,'Bootstrap fixture must hold the current conversation unset');
  let readyResolved=false;
  const ready=page.waitForFunction(()=>typeof current==='string'&&current.length>0&&!document.querySelector('#prompt').disabled).then(()=>{readyResolved=true;});
  try{
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    assert.equal(readyResolved,false,'Catalog setup must wait for the current conversation, not only an enabled prompt');
  }finally{releaseBootstrap();}
  await ready;await page.unroute('**/api/sessions',bootstrapRoute);
  const ids=await page.evaluate(async()=>{
    async function upload(name,text){return api(`/api/sessions/${current}/files?name=${encodeURIComponent(name)}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:new TextEncoder().encode(text).buffer});}
    const norm=await upload('norm.txt','TEST 2026 clause1 Limit 2.5\nm');await upload('norm.txt','Other edition with same name');const actual=await upload('actual.txt','Height 2500 mm');
    const rule={rule_id:'synthetic',rule_version:'1',document:'TEST',edition:'2026',scope:'Scope declaration',clause:'clause1',requirement:'Limit 2.5\nm',normative_source_sha256:norm.sha256,effective_from:'2026-01-01',effective_until:'2026-12-31',operator:'<=',limit:'2.5',limit_unit:'m',clause_text:'clause1 Limit 2.5\nm',source_locator:'clause1',accepted_data_classes:['MEASURED']};
    const catalog=await upload('catalog.json',JSON.stringify({format_version:1,registry_version:'synthetic',rules:[{...rule,source_path:'norm.txt'}]}));
    const n=await api(`/api/sessions/${current}/evidence`,{method:'POST',body:{file_id:norm.id,quote:'TEST 2026 clause1 Limit 2.5\nm',statement:'Synthetic norm',data_class:'P'}});
    const a=await api(`/api/sessions/${current}/evidence`,{method:'POST',body:{file_id:actual.id,quote:'Height 2500 mm',statement:'Synthetic measurement declaration',data_class:'M'}});
    for(const row of [n,a])await api(`/api/sessions/${current}/evidence/${row.id}/reviews`,{method:'POST',body:{expected_revision:0,decision:'SOURCE_CONFIRMED',note:'Exact synthetic source',actor:'Test'}});
    await refresh();return {catalog:catalog.id,norm:n.id,actual:a.id,source:norm.id};
  });
  await page.evaluate(()=>{document.querySelector('#domain-panel').open=true;});
  assert.equal(await page.locator('#normative-catalog-file').count(),1,'Ordinary catalog selection must exist');
  await page.selectOption('#normative-catalog-file',ids.catalog);await page.selectOption('#normative-catalog-sources',[ids.source]);await page.click('#normative-catalog-load');
  await page.waitForFunction(()=>document.querySelector('#normative-catalog-rule').options.length===2);
  await page.selectOption('#normative-catalog-rule','0');
  assert.ok((await page.locator('#normative-catalog-detail').textContent()).includes('clause1 Limit 2.5\nm'));
  assert.equal(await page.locator('#normative-packet-form [name="limit-fragment"]').inputValue(),'2.5\nm');
  await page.fill('#normative-catalog-date','2026-10-16');
  await page.selectOption('#normative-packet-form [name="actual-source"]',ids.actual);
  await page.fill('#normative-packet-form [name="actual_condition"]','Height 2500 mm');await page.fill('#normative-packet-form [name="comparison"]','Synthetic exact units comparison');await page.fill('#normative-packet-form [name="conclusion"]','Synthetic arithmetic only');
  for(const [field,value] of Object.entries({'actual-value':'2500','actual-unit':'mm','actual-fragment':'2500 mm'}))await page.fill(`#normative-packet-form [name="${field}"]`,value);
  for(const [name,viewport] of [['desktop',{width:1366,height:950}],['mobile',{width:390,height:844}]]){await page.setViewportSize(viewport);await page.locator('#normative-catalog-detail').scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true);await page.screenshot({path:path.join(temp,name+'.png')});}
  await page.getByRole('button',{name:'Сохранить нормативный пакет',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.domain-packet-result'));
  const result=await page.evaluate(async()=>api(`/api/sessions/${current}/domain-packets`));assert.equal(result.packets[0].catalog_rule.rule.clause,'clause1');assert.equal(result.packets[0].acceptance_granted,false);
  // Hold a real request, switch projects, then deliver the previous project's response.
  let release;const gate=new Promise(resolve=>release=resolve);
  await page.route('**/normative-catalog',async route=>{await gate;await route.continue();});
  await page.selectOption('#normative-catalog-file',ids.catalog);await page.selectOption('#normative-catalog-sources',[ids.source]);
  const requested=page.waitForRequest(request=>request.url().endsWith('/normative-catalog'));
  await page.click('#normative-catalog-load');await requested;
  await page.evaluate(async()=>{const other=await api('/api/sessions',{method:'POST',body:{title:'Other normative project'}});await switchSession(other.id,{internal:true});});
  const returned=page.waitForResponse(response=>response.url().endsWith('/normative-catalog'));
  release();await (await returned).finished();await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  assert.equal(await page.locator('#normative-catalog-detail').textContent(),'');assert.equal(await page.locator('#normative-catalog-rule').inputValue(),'');assert.equal(await page.locator('#normative-catalog-date').inputValue(),'');assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',scope:'SYNTHETIC_CATALOG_UI_NOT_NORMATIVE_ACCEPTANCE',screenshots:temp}));
 }finally{if(browser)await browser.close();if(child){if(process.platform==='win32')await new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});killer.on('exit',resolve);});else child.kill('SIGTERM');}}
})().catch(error=>{console.error(error);process.exitCode=1;});
