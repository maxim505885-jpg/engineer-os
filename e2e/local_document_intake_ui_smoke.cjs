/* Real Chromium, original preview and explicit model decoder boundary. */
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-intake-ui-'));let child,browser;
 try{
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:'http://127.0.0.1:9',GOOGLE_DRIVE_CLIENT_ID:'',GOOGLE_DRIVE_CLIENT_SECRET:'',GOOGLE_DRIVE_REFRESH_TOKEN:''}});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Launcher timeout')),10000);child.stdout.on('data',data=>{log+=data;const match=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve(match[1]);}});child.once('exit',code=>{clearTimeout(timer);reject(Error('Launcher exit '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#upload').disabled);
  const fixture=spawnSync(process.env.PYTHON||'python3',['-c',"import fitz,sys;d=fitz.open();d.new_page().insert_text((40,70),'Height 4 metres');sys.stdout.buffer.write(d.tobytes())"],{cwd:root});assert.equal(fixture.status,0,fixture.error?.message||fixture.stderr?.toString());
  await page.setInputFiles('#upload',{name:'original.pdf',mimeType:'application/pdf',buffer:fixture.stdout});await page.waitForSelector('.file');await page.getByRole('button',{name:'Просмотреть оригинал',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#source-image').naturalWidth>0);assert.equal(await page.locator('#source-viewer').isVisible(),true);assert.equal(await page.locator('#evidence-list').textContent(),'');
  assert.equal(await page.locator('.advanced-document-actions summary').isVisible(),false,'Low-level extraction stays hidden in normal mode');
  await page.locator('#ui-mode-toggle').click();
  await page.locator('.advanced-document-actions summary').click();assert.equal(await page.getByRole('button',{name:'Локальный OCR · русский и английский',exact:true}).count(),1);
  await page.setInputFiles('#upload',{name:'model.lir',mimeType:'application/octet-stream',buffer:Buffer.from('ULIRA-SAPR synthetic container')});await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);assert.ok((await page.locator('#files').textContent()).includes('Декодер не подключён'));
  await page.reload();await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);assert.ok((await page.locator('#files').textContent()).includes('MODEL_DECODER_UNAVAILABLE'));assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({result:'PASS',real_chromium:true,checks:['original-page-preview-without-candidate','visible-viewer','local-ocr-action','lir-intake-no-decoder-claim','reload-originals'],engineering_acceptance:false}));
 }finally{if(browser)await browser.close();if(child&&child.exitCode===null){child.kill('SIGINT');await new Promise(resolve=>{const timer=setTimeout(()=>{child.kill('SIGKILL');resolve();},2500);child.once('exit',()=>{clearTimeout(timer);resolve();});});}fs.rmSync(temp,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
