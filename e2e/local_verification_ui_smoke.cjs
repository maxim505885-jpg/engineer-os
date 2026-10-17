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
  await page.setInputFiles('#upload',{name:'project.txt',mimeType:'text/plain',buffer:Buffer.from('Project declaration: height 4 m.')});await page.waitForFunction(()=>document.querySelector('.file')&&!document.querySelector('#send').disabled);
  const candidate=await page.evaluate(async()=>{const snapshot=await api(`/api/sessions/${current}`);const row=await api(`/api/sessions/${current}/evidence`,{method:'POST',body:{file_id:snapshot.files[0].id,quote:'Project declaration: height 4 m.',statement:'Controlled PROJECT declaration',data_class:'P'}});await api(`/api/sessions/${current}/evidence/${row.id}/reviews`,{method:'POST',body:{expected_revision:0,decision:'SOURCE_CONFIRMED',note:'Exact source quotation',actor:'Controlled reader'}});await refresh();return row.id;});
  await page.evaluate(()=>{document.querySelector('#evidence-panel').open=true;document.querySelector('#engineering-review-panel').open=true;});
  await page.waitForFunction(()=>document.querySelector('#engineering-review-subject').options.length===1);
  await page.click('#engineering-review-provision');await page.waitForFunction(()=>!document.querySelector('#engineering-review-submit').disabled);
  await page.fill('#engineering-review-reviewer','Controlled browser reviewer');await page.fill('#engineering-review-method','Exact PROJECT quotation and class review');await page.fill('#engineering-review-reason','The document declaration alone is reviewed. No actual measurement is asserted.');await page.check('#engineering-review-confirm');await page.click('#engineering-review-submit');
  await page.waitForFunction(()=>document.querySelector('#engineering-review-status').textContent.includes('ACCEPTED')&&!document.querySelector('#engineering-review-submit').disabled);
  const state=await page.evaluate(async id=>({review:await api(`/api/sessions/${current}/verifications?kind=EVIDENCE&subject_id=${id}`),audit:await api(`/api/sessions/${current}/final-audit`),snapshot:await api(`/api/sessions/${current}`)}),candidate);
  assert.equal(state.review.verified_subject.data_class,'P');assert.equal(state.review.verified_subject.engineering_verification.reviewer_identity_verified,false);assert.equal(state.audit.acceptance_granted,false);assert.equal(state.snapshot.evidence[0].engineering_verified,undefined);
  for(const [name,viewport] of [['desktop',{width:1366,height:950}],['mobile',{width:390,height:844}]]){await page.setViewportSize(viewport);await page.locator('#engineering-review-panel').scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true);await page.locator('#engineering-review-panel').screenshot({path:path.join(temp,name+'.png')});}
  await page.evaluate(async id=>{await api(`/api/sessions/${current}/evidence/${id}/reviews`,{method:'POST',body:{expected_revision:1,decision:'NEEDS_DATA',note:'Controlled stale-source test',actor:'Second reader'}});},candidate);
  await page.getByRole('button',{name:'Обновить основания review',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#engineering-review-status').textContent.includes('SOURCE_NOT_CONFIRMED'));
  assert.equal(await page.locator('#engineering-review-confirm').isChecked(),false);
  await page.evaluate(async()=>{const other=await api('/api/sessions',{method:'POST',body:{title:'Other review project'}});await switchSession(other.id,{internal:true});});
  assert.equal(await page.locator('#engineering-review-reviewer').inputValue(),'');assert.equal(await page.locator('#engineering-review-sources').textContent(),'');assert.equal(await page.locator('#engineering-review-confirm').isChecked(),false);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',scope:'CONTROLLED_PROJECT_REVIEW_NOT_OBJECT_ACCEPTANCE',screenshots:temp}));
 }finally{if(browser)await browser.close();if(child){if(process.platform==='win32')await new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});killer.on('exit',resolve);});else child.kill('SIGTERM');}}
})().catch(error=>{console.error(error);process.exitCode=1;});
