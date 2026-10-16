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
  assert.equal(await page.locator('#spu-workspace-shell').count(),1,'Supplied SPU workspace shell must be mounted');
  await page.waitForFunction(()=>document.querySelector('#spu-stat-projects').textContent==='1'&&document.querySelector('#spu-stat-files').textContent==='0');assert.equal(await page.locator('#spu-stat-projects').textContent(),'1');assert.equal(await page.locator('#spu-stat-files').textContent(),'0');assert.equal(await page.locator('#spu-stat-jobs').textContent(),'0');
  assert.equal(await page.locator('#spu-project-list .spu-project-open').count(),1);
  await page.setInputFiles('#upload',{name:'source.txt',mimeType:'text/plain',buffer:Buffer.from('Source declaration: height 4 m.')});
  await page.waitForFunction(()=>document.querySelector('#spu-stat-files').textContent==='1');
  const first=await page.evaluate(()=>current);
  const other=await page.evaluate(async()=>{const row=await api('/api/sessions',{method:'POST',body:{title:'<img src=x onerror=window.spuInjected=true>'}});await switchSession(row.id,{internal:true});return row.id;});
  await page.waitForFunction(()=>document.querySelector('#spu-stat-projects').textContent==='2');assert.equal(await page.locator('#spu-stat-files').textContent(),'0');assert.equal(await page.evaluate(()=>window.spuInjected),undefined);assert.equal(await page.locator('#spu-project-list img').count(),0);
  await page.locator(`.spu-project-open[data-session="${first}"]`).click();await page.waitForFunction(()=>document.querySelector('#spu-stat-files').textContent==='1');
  await page.evaluate(()=>document.querySelector('#evidence-panel').open=true);await page.fill('#evidence-quote','Unsaved source draft');await page.evaluate(()=>refresh());assert.equal(await page.locator('#evidence-quote').inputValue(),'Unsaved source draft');
  await page.locator('[data-spu-target="calculations"]').first().click();assert.equal(await page.locator('#domain-panel').getAttribute('open'),'');
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){await page.setViewportSize(viewport);await page.evaluate(()=>scrollTo({top:0,behavior:"instant"}));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,name+' overflow');await page.screenshot({path:path.join(temp,name+'.png')});}
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',scope:'SPU_REUSED_WORKSPACE_WITH_EXISTING_ENGINEER_BACKEND',screenshots:temp}));
 }finally{if(browser)await browser.close();if(child){if(process.platform==='win32')await new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});killer.on('exit',resolve);});else child.kill('SIGTERM');}}
})().catch(error=>{console.error(error);process.exitCode=1;});
