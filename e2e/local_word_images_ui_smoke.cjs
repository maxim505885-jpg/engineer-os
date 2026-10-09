/* Real browser: source-linked DOCX image, authenticated PNG and honest scope. */
const {stopChild}=require('./stop_child.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process');const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-word-images-'));let child,browser;
 try{
  const fixture=`import sys
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.worker import Worker
from engineering.local_app.server import make_server
from tests.test_office_documents import Model
from tests.test_word_images import image_doc
s=Store(sys.argv[1]);sid=s.create_session()['id'];f=preserve_file(s,sid,'images.docx',image_doc());m=Model()
s.enqueue(sid,'Read source images',[f['id']]);Worker(s,m).run_once()
server=make_server(s,m,drive_client=None);print('ORIGIN http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()`;
  child=spawn(process.env.PYTHON||'python3',['-u','-c',fixture,temp],{cwd:root});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);child.stdout.on('data',data=>{log+=data;const match=log.match(/ORIGIN (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve(match[1]);}});child.once('exit',code=>{clearTimeout(timer);reject(Error('Fixture exit '+code));});});
  browser=await chromium.launch({headless:true});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
  await page.getByRole('button',{name:'Результаты по частям',exact:true}).click();
  await page.locator('.analysis-receipt summary').first().click();
  await page.locator('.office-image').first().click();
  await page.waitForFunction(()=>document.querySelector('#source-image').naturalWidth===12);
  assert.equal(await page.locator('#source-viewer').isVisible(),true);
  assert.ok((await page.locator('#source-caption').textContent()).includes('размещение Word не применены'));
  assert.equal(await page.locator('#evidence-list').textContent(),'');
  await page.getByRole('button',{name:'Закрыть просмотр',exact:true}).click();
  assert.equal(await page.locator('#source-viewer').isVisible(),false);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'PASS',checks:['docx-source-image-control','authenticated-real-png','untransformed-scope','no-created-evidence','viewer-close'],engineering_acceptance:false}));
 }finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(error=>{console.error(error);process.exitCode=1;});
