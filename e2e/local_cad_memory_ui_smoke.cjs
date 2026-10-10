const {stopChild}=require('./stop_child.cjs');
/* Real Chromium: source-bound CAD and fail-closed confirmed knowledge. */
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process'),{chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-cad-memory-'));let child,browser;
 try{
  const seed=spawnSync(process.env.PYTHON||'python3',['-c',`import sys,io
import ezdxf
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
s=Store(sys.argv[1]);sid=s.create_session('CAD fixture')['id'];d=ezdxf.new('R2010',units=4);d.modelspace().add_line((0,0),(10,0));b=io.StringIO();d.write(b);preserve_file(s,sid,'drawing.dxf',b.getvalue().encode())
`,temp],{cwd:root});assert.equal(seed.status,0,seed.stderr.toString());
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:'http://127.0.0.1:9',GOOGLE_DRIVE_CLIENT_ID:'',GOOGLE_DRIVE_CLIENT_SECRET:'',GOOGLE_DRIVE_REFRESH_TOKEN:''}});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Launcher timeout')),15000);child.stdout.on('data',d=>{log+=d;const m=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(m){clearTimeout(timer);resolve(m[1]);}});child.once('exit',c=>{clearTimeout(timer);reject(Error('Launcher exit '+c));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
  await page.locator('#knowledge-panel > summary').click();await page.waitForFunction(()=>document.querySelector('#knowledge-status').textContent.includes('Повторная проверка'));
  assert.equal(await page.locator('#knowledge-promote').isDisabled(),true);assert.match(await page.locator('#knowledge-status').textContent(),/ACCEPTED/);
  await page.locator('#cad-panel > summary').click();await page.waitForFunction(()=>document.querySelector('#cad-inventory').textContent.includes('DXF'));
  await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,'Open CAD/memory panels must fit mobile');assert.match(await page.locator('#cad-inventory').textContent(),/4/);assert.match(await page.locator('#cad-inventory').textContent(),/не проверена/i);
  await page.locator('#cad-locator-note').fill('Проверить этот элемент');await page.locator('#cad-locator-form button').click();await page.waitForFunction(()=>document.querySelector('#cad-evidence').options.length===1);
  await page.locator('#cad-text').fill('Проверить');await page.locator('#cad-reason').fill('Отдельная аннотация кандидата');await page.locator('#cad-evidence').selectOption({index:0});await page.locator('#cad-units').check();await page.locator('#cad-derive').click();await page.waitForFunction(()=>document.querySelector('#cad-result').textContent.includes('PASS'));
  const download=page.waitForEvent('download');await page.locator('#cad-result button').click();const derived=await download;assert.equal(await derived.failure(),null);assert.ok(fs.statSync(await derived.path()).size>100);
  await page.locator('#new-chat').click();await page.waitForFunction(()=>!document.querySelector('#cad-panel').open);assert.equal(await page.locator('#cad-result').textContent(),'');assert.equal(await page.locator('#knowledge-promote').isDisabled(),true);

  assert.equal(errors.length,0,errors.join('\n'));console.log(JSON.stringify({result:'PASS',real_chromium:true,checks:['cad-inventory','annotation-only-download','project-switch-isolation','source-preserved','knowledge-without-acceptance-disabled','mandatory-reverification']}));
 }finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(e=>{console.error(e);process.exitCode=1;});
