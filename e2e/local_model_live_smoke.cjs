/* Opt-in real inference. Requires an installed Ollama and a locally stored model. */
const assert=require('node:assert/strict');
const fs=require('node:fs');const os=require('node:os');const path=require('node:path');
const {spawn}=require('node:child_process');const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-live-model-'));
 const modelName=process.env.ENGINEER_OS_LIVE_MODEL||'qwen3:0.6b';let app,browser;
 async function stop(child){if(!child||child.exitCode!==null)return;child.kill('SIGINT');await new Promise(resolve=>{const timer=setTimeout(()=>{child.kill('SIGKILL');resolve();},3000);child.once('exit',()=>{clearTimeout(timer);resolve();});});}
 try{
  const env={...process.env,ENGINEER_OS_LOCAL_MODEL_URL:process.env.ENGINEER_OS_LIVE_ORIGIN||'http://127.0.0.1:11434',ENGINEER_OS_LOCAL_MODEL_KEY:''};
  delete env.ENGINEER_OS_LOCAL_MODEL;delete env.ENGINEER_OS_LOCAL_THINK;delete env.ENGINEER_OS_LOCAL_MODEL_TIMEOUT;
  app=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Startup timeout')),10000);app.stdout.on('data',data=>{log+=data;const found=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});app.on('exit',code=>{clearTimeout(timer);reject(Error('Startup '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#prompt').disabled);
  await page.locator('.model-panel summary').click();await page.waitForFunction(()=>modelFormLoaded);
  await page.fill('#model-setting-MODEL','engineer-os-definitely-missing-model');await page.selectOption('#model-setting-thinking','false');await page.click('#model-settings-form button');
  try{await page.waitForFunction(()=>document.querySelector('#model-status').textContent.includes('модель отсутствует'));}
  catch(error){console.error(JSON.stringify({stage:'missing-model-ui',diagnostic:await page.evaluate(async()=>({status:document.querySelector('#model-status').textContent,notice:document.querySelector('.model-panel p').textContent,error:document.querySelector('#error').textContent,health:await api('/api/status')})),page_errors:errors}));throw error;}
  await page.fill('#model-setting-MODEL',modelName);await page.click('#model-settings-form button');
  await page.waitForFunction(()=>document.querySelector('#model-status').textContent.includes('модель найдена'));
  await page.getByRole('button',{name:'Проверить реальный ответ',exact:true}).click();
  await page.waitForSelector('.message.assistant',{timeout:180000});
  const snap=await page.evaluate(()=>api(`/api/sessions/${current}`));
  assert.equal(snap.jobs[0].state,'SUCCEEDED');assert.ok(snap.jobs[0].result.text.trim());assert.equal(snap.jobs[0].result.acceptance_granted,false);assert.equal(snap.files.length,0);
  const text=snap.jobs[0].result.text;
  await page.reload();await page.waitForSelector('.message.assistant');assert.ok(await page.locator('.message.assistant').textContent().then(x=>x.includes(text)));
  await page.setInputFiles('#upload',{name:'source.txt',mimeType:'text/plain',buffer:Buffer.from('Unverified source: building height is 4 metres.')});
  await page.waitForSelector('.file');await page.waitForFunction(()=>!document.querySelector('#send').disabled);
  await page.fill('#prompt','Какую высоту сообщает прикреплённый источник? Ответь одним предложением.');await page.click('#send');
  await page.waitForFunction(()=>document.querySelectorAll('.message.assistant').length===2,{},{timeout:180000});
  const attachmentSnap=await page.evaluate(()=>api(`/api/sessions/${current}`));
  assert.equal(attachmentSnap.jobs[0].state,'SUCCEEDED');assert.equal(attachmentSnap.jobs[0].result.acceptance_granted,false);
  assert.equal(attachmentSnap.jobs[0].result.source_coverage[0].id,attachmentSnap.files[0].id);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({result:'PASS',real_ollama:true,synthetic_model:false,model:modelName,checks:['actual-model-list','missing-model-ui','saved-live-settings','real-inference-through-ui','separate-diagnostic-history','persisted-answer','attachment-through-real-model','source-coverage','no-engineering-acceptance'],response_chars:text.length}));
 }finally{if(browser)await browser.close();await stop(app);fs.rmSync(temp,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
