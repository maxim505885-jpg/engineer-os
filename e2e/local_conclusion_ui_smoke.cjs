const {stopChild}=require('./stop_child.cjs');
/* Real Chromium: generate/edit/version/reload/download a blocked draft. */
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-conclusion-'));let child,browser;
 try{
  const seed=spawnSync(process.env.PYTHON||'python3',['-c',`import json,sys,fitz
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.worker import Worker
from engineering.local_app.real_case import build
class Model:
 def chat(self,messages): return json.dumps(dict(status='UNCERTAINTY',summary='Controlled draft',observations=[],limitations=['Not accepted']))
s=Store(sys.argv[1]);sid=s.create_session('Тест черновика')['id'];f=preserve_file(s,sid,'source.txt',b'Controlled source');p=fitz.open();p.new_page().insert_text((72,72),'Source illustration');image=preserve_file(s,sid,'image.pdf',p.tobytes());p.close();j=s.enqueue(sid,'Review',[f['id'],image['id']],mode='CORE_RUN',requested_checks=['report','calculation']);Worker(s,Model()).run_once();build(s,sid,job_id=j['id'],expected_revision=0)
` ,temp],{cwd:root});assert.equal(seed.status,0,seed.stderr.toString());
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:'http://127.0.0.1:9',GOOGLE_DRIVE_CLIENT_ID:'',GOOGLE_DRIVE_CLIENT_SECRET:'',GOOGLE_DRIVE_REFRESH_TOKEN:''}});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Launcher timeout')),10000);child.stdout.on('data',d=>{log+=d;const match=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve(match[1]);}});child.once('exit',code=>{clearTimeout(timer);reject(Error('Launcher exit '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
  await page.locator('#conclusion-panel > summary').click();await page.waitForFunction(()=>!document.querySelector('#conclusion-save').disabled);
  await page.locator('#conclusion-author').fill('Автор теста');await page.locator('#conclusion-summary').fill('Первый черновик');await page.locator('#conclusion-save').click();
  await page.waitForFunction(()=>document.querySelector('#conclusion-state').textContent.includes('Версия 1'));
  await page.locator('#conclusion-summary').fill('Изменённый черновик <script>');await page.waitForTimeout(2700);assert.equal(await page.locator('#conclusion-summary').inputValue(),'Изменённый черновик <script>');
  let releaseSave,enteredSave;const gate=new Promise(r=>{releaseSave=r}),entered=new Promise(r=>{enteredSave=r});
  await page.route('**/conclusions',async route=>{if(route.request().method()==='POST'){enteredSave();await gate;}await route.continue();});
  await page.locator('#conclusion-save').click();await entered;await page.locator('#conclusion-summary').fill('Правка во время сохранения');releaseSave();
  await page.waitForFunction(()=>document.querySelector('#conclusion-state').textContent.includes('Версия 2'));assert.equal(await page.locator('#conclusion-summary').inputValue(),'Правка во время сохранения');
  await page.unroute('**/conclusions');await page.locator('#conclusion-save').click();await page.waitForFunction(()=>document.querySelector('#conclusion-state').textContent.includes('Версия 3'));
  await page.reload();await page.locator('#conclusion-panel > summary').click();await page.waitForFunction(()=>document.querySelector('#conclusion-state').textContent.includes('Версия 3'));assert.equal(await page.locator('#conclusion-summary').inputValue(),'Правка во время сохранения');
  assert.ok((await page.locator('#conclusion-results').textContent()).includes('CALCULATION_DOMAIN_PACKET_MISSING'));
  await page.locator('#conclusion-template').selectOption('inspection');await page.locator('#conclusion-illustration-enabled').check();await page.locator('#conclusion-save').click();await page.waitForFunction(()=>document.querySelector('#conclusion-state').textContent.includes('Версия 4')).catch(async e=>{throw Error(e.message+' UI: '+await page.locator('#error').textContent());});
  for(const format of ['docx','pdf']){const download=page.waitForEvent('download');await page.locator('#conclusion-export-'+format).click();const d=await download;assert.equal(await d.failure(),null);assert.ok(d.suggestedFilename().endsWith('.'+format));const file=await d.path();assert.ok(fs.statSync(file).size>100);}
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({result:'PASS',real_chromium:true,checks:['blocked-draft','edit-preserved-during-refresh','version-history','reload','draft-template','source-bound-illustration','docx-pdf-download','no-acceptance']}));
 }finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(e=>{console.error(e);process.exitCode=1;});
