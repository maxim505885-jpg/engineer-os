'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-calculation-ui-'));
 let child,browser;
 try{
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,PYTHONUTF8:'1'}});
  const origin=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Startup timeout')),15000);child.stdout.on('data',data=>{output+=data;const found=output.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error('Server exited '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1366,height:950}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#prompt').disabled);
  await page.setInputFiles('#upload',{name:'dimensions.txt',mimeType:'text/plain',buffer:Buffer.from('Unverified: width 0.2 m, height 0.4 m')});
  await page.waitForFunction(()=>document.querySelector('.file')&&!document.querySelector('#send').disabled);
  await page.evaluate(()=>{document.querySelector('#domain-panel').open=true;document.querySelector('#engineering-tools-panel').open=true;});
  await page.waitForFunction(()=>document.querySelector('#engineering-source').options.length===1);
  await page.fill('#engineering-width_m','0.2');await page.fill('#engineering-height_m','0.4');await page.click('#engineering-submit');
  try{await page.waitForFunction(()=>document.querySelector('.message.assistant')?.textContent.includes('RECTANGLE: PASS')&&!document.querySelector('#send').disabled);}
  catch(error){console.error(await page.evaluate(async()=>({error:document.querySelector('#error').textContent,invalid:[...document.querySelector('#engineering-tools-form').elements].filter(e=>e.validity&&!e.validity.valid).map(e=>[e.id,e.validationMessage]),snapshot:await api(`/api/sessions/${current}`)})));throw error;}
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('area_m2'));
  assert.ok((await page.locator('#engineering-results').textContent()).includes('ASSUMED'));
  const result=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return {job:snap.jobs.find(j=>j.mode==='ENGINEERING_RUN'),evidence:snap.evidence};});
  assert.equal(result.job.result.acceptance_granted,false);assert.equal(result.evidence.length,0);assert.ok(Math.abs(result.job.result.engineering_run.result.results.area_m2-.08)<1e-10);
  if(process.env.ENGINEER_OS_CALCULATION_CHILD_SMOKE==='1'){
   await page.selectOption('#engineering-tool','BEAM');
   for(const [field,value] of Object.entries({length_m:'6',elastic_modulus_pa:'210000000000',inertia_m4:'0.000008',area_m2:'0.003',load_n_m:'1000'}))await page.fill('#engineering-'+field,value);
   await page.click('#engineering-submit');await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('BEAM: PASS')&&!document.querySelector('#send').disabled);
   await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('reaction_left_n'));
   const beam=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return snap.jobs.find(j=>j.mode==='ENGINEERING_RUN').result.engineering_run.result;});
   assert.equal(beam.status,'PASS');assert.ok(Math.abs(beam.results.reaction_left_n-3000)<1e-5);assert.equal(beam.resource_boundary.child_isolated,true);
  }
  for(const [name,viewport] of [['desktop',{width:1366,height:950}],['mobile',{width:390,height:844}]]){
   await page.setViewportSize(viewport);await page.locator('#engineering-tools-panel').scrollIntoViewIfNeeded();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,name+' overflow');
   await page.screenshot({path:path.join(temp,name+'.png'),fullPage:true});
  }
  await page.evaluate(async()=>{const next=await api('/api/sessions',{method:'POST',body:{title:'Second calculation project'}});await switchSession(next.id,{internal:true});});
  assert.equal(await page.locator('#engineering-results').textContent(),'','Old calculation receipt must not appear in a new project');
  assert.equal(await page.locator('#engineering-width_m').inputValue(),'','Dimensions must not carry into another project');
  assert.equal(await page.locator('#engineering-planar').inputValue(),'');
  assert.equal(await page.locator('#engineering-source option').count(),0);
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',scope:process.env.ENGINEER_OS_CALCULATION_CHILD_SMOKE==='1'?'CONTROLLED_RECTANGLE_AND_BEAM_HTTP_UI':'CONTROLLED_RECTANGLE_HTTP_UI_ONLY',screenshots:temp}));
 }finally{
  if(browser)await browser.close();
  if(child){if(process.platform==='win32')await new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});killer.on('exit',resolve);});else child.kill('SIGTERM');}
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
