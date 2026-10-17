const assert=require('node:assert/strict');
const fs=require('node:fs');const os=require('node:os');const path=require('node:path');
const {spawn}=require('node:child_process');const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-ifc-ui-'));let child,browser;
 try{
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,PYTHONUTF8:'1'}});
  const origin=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Startup timeout')),15000);child.stdout.on('data',data=>{output+=data;const match=output.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve(match[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error('Server exited '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1366,height:950}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#prompt').disabled);
  const source=fs.readFileSync(path.join(root,'tests/fixtures/bim/reference.ifc'));
  await page.setInputFiles('#upload',{name:'reference.ifc',mimeType:'application/octet-stream',buffer:source});
  await page.waitForFunction(()=>document.querySelector('.file')&&!document.querySelector('#send').disabled);
  await page.evaluate(()=>{document.querySelector('#domain-panel').open=true;document.querySelector('#engineering-tools-panel').open=true;});
  await page.waitForFunction(()=>document.querySelector('#engineering-source').options.length===1);
  await page.selectOption('#engineering-tool','IFC_INVENTORY');
  assert.equal(await page.locator('#engineering-width_m').isVisible(),false);
  await page.click('#engineering-submit');
  await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('IFC_INVENTORY: UNCERTAINTY')&&!document.querySelector('#send').disabled);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('GUID'));
  const state=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return {run:snap.jobs.find(j=>j.mode==='ENGINEERING_RUN').result.engineering_run,evidence:snap.evidence};});
  assert.equal(state.run.input_data_class,'PROJECT');assert.equal(state.run.actual_structure_verified,false);
  assert.equal(state.run.result.resource_boundary.child_isolated,true);assert.equal(state.run.acceptance_granted,false);assert.equal(state.evidence.length,0);
  const propertyPath=['properties','BaseQuantities','Length'];
  await page.selectOption('#ifc-evidence-property',JSON.stringify(propertyPath));await page.click('#ifc-evidence-read');
  await page.waitForFunction(()=>document.querySelector('#ifc-evidence-quote').textContent.includes('6000')&&!document.querySelector('#ifc-evidence-save').disabled);
  assert.ok((await page.locator('#ifc-evidence-quote').textContent()).includes('NOT_QUALIFIED'));
  for(const [name,viewport] of [['guid-desktop',{width:1366,height:950}],['guid-mobile',{width:390,height:844}]]){
   await page.setViewportSize(viewport);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,name+' overflow');
   await page.locator('#engineering-tools-panel').screenshot({path:path.join(temp,name+'.png')});
  }
  await page.setViewportSize({width:1366,height:950});
  await page.fill('#ifc-evidence-statement','Controlled PROJECT model quantity, not a site measurement.');await page.click('#ifc-evidence-save');
  await page.waitForFunction(()=>document.querySelector('#evidence-list').textContent.includes('6000')&&!document.querySelector('#send').disabled);
  const candidate=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return snap.evidence[0];});
  assert.equal(candidate.data_class,'P');assert.equal(candidate.acceptance_granted,false);assert.equal(candidate.locator.kind,'IFC_GUID');assert.deepEqual(candidate.locator.property_path,propertyPath);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.selectOption('#engineering-tool','IFC_GEOMETRY');
  await page.click('#engineering-submit');
  await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('IFC_GEOMETRY: UNCERTAINTY')&&!document.querySelector('#send').disabled);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('NOT_VISIBLE'));
  const geometry=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return snap.jobs.find(j=>j.mode==='ENGINEERING_RUN').result.engineering_run.result;});
  assert.equal(geometry.resource_boundary.timeout_seconds,30);
  await page.selectOption('#engineering-tool','IFC_REQUIREMENTS');
  await page.fill('#engineering-ifc-requirements',JSON.stringify([{id:'TZ-1',source:'Controlled test requirement',ifc_type:'IfcBeam',pset:'BaseQuantities',property:'Length',equals:6000,unit:'project_length'}]));
  await page.click('#engineering-submit');await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('IFC_REQUIREMENTS: UNCERTAINTY')&&!document.querySelector('#send').disabled);
  const requirements=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return snap.jobs.find(j=>j.mode==='ENGINEERING_RUN').result.engineering_run.result;});
  assert.equal(requirements.checks[0].status,'PASS');assert.equal(requirements.acceptance_granted,false);
  await page.setInputFiles('#upload',{name:'revision.ifc',mimeType:'application/octet-stream',buffer:source});
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===2&&!document.querySelector('#send').disabled);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-source-2').options.length===2);
  await page.selectOption('#engineering-tool','IFC_DIFF');
  assert.notEqual(await page.locator('#engineering-source').inputValue(),await page.locator('#engineering-source-2').inputValue(),'Comparison must offer distinct model revisions');
  await page.click('#engineering-submit');
  await page.waitForFunction(()=>document.querySelector('#messages').textContent.includes('IFC_DIFF: UNCERTAINTY')&&!document.querySelector('#send').disabled);
  await page.getByRole('button',{name:'Обновить исходники и результаты',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#engineering-results').textContent.includes('changed_guids'));
  const diff=await page.evaluate(async()=>{const snap=await api(`/api/sessions/${current}`);return snap.jobs.find(j=>j.mode==='ENGINEERING_RUN').result.engineering_run.result;});
  assert.deepEqual(diff.changed_guids,[]);assert.equal(diff.acceptance_granted,false);
  for(const [name,viewport] of [['desktop',{width:1366,height:950}],['mobile',{width:390,height:844}]]){
   await page.setViewportSize(viewport);await page.locator('#engineering-tools-panel').scrollIntoViewIfNeeded();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,name+' overflow');
   await page.locator('#engineering-tools-panel').screenshot({path:path.join(temp,name+'.png')});
  }
  await page.evaluate(async()=>{const next=await api('/api/sessions',{method:'POST',body:{title:'Other IFC project'}});await switchSession(next.id,{internal:true});});
  assert.equal(await page.locator('#engineering-results').textContent(),'');assert.equal(await page.locator('#engineering-source option').count(),0);
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',scope:'CONTROLLED_IFC_INVENTORY_GEOMETRY_REQUIREMENTS_DIFF_GUID_NOT_ACTUAL_QUALIFICATION',screenshots:temp}));
 }finally{
  if(browser)await browser.close();
  if(child){if(process.platform==='win32')await new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});killer.on('exit',resolve);});else child.kill('SIGTERM');}
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
