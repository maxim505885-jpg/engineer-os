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
  await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#prompt').disabled);
  const made=require('node:child_process').spawnSync(process.env.PYTHON||'python3',['-c',"import ezdxf,sys; from pathlib import Path; p=Path(sys.argv[1]); d=ezdxf.new('R2010',units=4); e=d.modelspace().add_line((0,0),(10,0)); d.saveas(p/'before.dxf'); e.dxf.end=(11,0,0); d.saveas(p/'after.dxf')",temp],{encoding:'utf8'});assert.equal(made.status,0,made.stderr);
  for(const name of ['before.dxf','after.dxf']){await page.setInputFiles('#upload',path.join(temp,name));await page.waitForFunction(()=>!document.querySelector('#send').disabled);}
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);
  await page.evaluate(()=>{document.querySelector('#domain-panel').open=true;document.querySelector('#engineering-tools-panel').open=true;});
  await page.waitForFunction(()=>document.querySelector('#engineering-source').options.length===2);
  assert.equal(await page.locator('#engineering-tool option[value="CAD_INVENTORY"]').count(),1,'CAD queue must be available in ordinary UI');
  await page.selectOption('#engineering-tool','CAD_INVENTORY');
  const ids=await page.evaluate(async()=>{const s=await api(`/api/sessions/${current}`);return Object.fromEntries(s.files.map(f=>[f.name,f.id]));});
  await page.selectOption('#engineering-source',ids['before.dxf']);await page.click('#engineering-submit');
  await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('CAD_INVENTORY:')&&!document.querySelector('#send').disabled);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('LINE'));
  const inventory=await page.evaluate(async()=>{const s=await api(`/api/sessions/${current}`);return s.jobs[0].result.engineering_run;});assert.equal(inventory.input_data_class,'PROJECT');assert.equal(inventory.result.entity_counts.LINE,1);assert.equal(inventory.result.resource_boundary.child_isolated,true);
  await page.selectOption('#engineering-tool','CAD_DIFF');await page.selectOption('#engineering-source',ids['before.dxf']);await page.selectOption('#engineering-source-2',ids['after.dxf']);await page.click('#engineering-submit');
  await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('CAD_DIFF:')&&!document.querySelector('#send').disabled);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('Изменено объектов: 1'));
  const snapshot=await page.evaluate(async()=>api(`/api/sessions/${current}`));const diff=snapshot.jobs[0].result.engineering_run.result;assert.equal(diff.status,'BLOCK');assert.equal(diff.changed_handles.length,1);assert.equal(diff.acceptance_granted,false);assert.deepEqual(snapshot.evidence,[]);
  for(const [name,viewport] of [['desktop',{width:1366,height:950}],['mobile',{width:390,height:844}]]){await page.setViewportSize(viewport);await page.locator('#engineering-results').scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true);await page.screenshot({path:path.join(temp,name+'.png')});}
  await page.evaluate(async()=>{const s=await api('/api/sessions',{method:'POST',body:{title:'Other CAD project'}});await switchSession(s.id,{internal:true});});assert.equal(await page.locator('#engineering-results').textContent(),'');assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',scope:'SYNTHETIC_DXF_WORKER_UI_NOT_DWG_ACCEPTANCE',screenshots:temp}));
 }finally{if(browser)await browser.close();if(child){if(process.platform==='win32')await new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});killer.on('exit',resolve);});else child.kill('SIGTERM');}}
})().catch(error=>{console.error(error);process.exitCode=1;});
