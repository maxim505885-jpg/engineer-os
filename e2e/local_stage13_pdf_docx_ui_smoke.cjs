/* Real Chromium stage13 document upload/reload smoke. Not a Supabase E2E claim. */
const {stopChild}=require('./stop_child.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process'),{chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-stage13-ui-'));let child,browser;
 try{
  const generator=`import sys,fitz,zipfile
d=fitz.open();d.new_page().insert_text((40,70),'Height 4 metres');d.save(sys.argv[1]);d.close()
xml=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><w:p><w:r><w:t>Inspection</w:t></w:r></w:p><m:oMath><m:r/></m:oMath></w:body></w:document>'
with zipfile.ZipFile(sys.argv[2],'w') as z:
 z.writestr('word/document.xml',xml)
 z.writestr('word/media/figure.emf',b'SYNTHETIC-EMF-UNVERIFIED')
`;
  const pdf=path.join(temp,'fixture.pdf'),docx=path.join(temp,'fixture.docx');
  const generated=spawnSync(process.env.PYTHON||'python3',['-c',generator,pdf,docx],{cwd:root});
  assert.equal(generated.status,0,generated.stderr.toString());
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:'http://127.0.0.1:9',GOOGLE_DRIVE_CLIENT_ID:'',GOOGLE_DRIVE_CLIENT_SECRET:'',GOOGLE_DRIVE_REFRESH_TOKEN:''}});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('App startup timeout')),15000);child.stdout.on('data',part=>{log+=part;const match=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve(match[1]);}});child.once('exit',code=>{clearTimeout(timer);reject(Error('App exited '+code));});});
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage(),errors=[];page.on('pageerror',err=>errors.push(err.message));
  await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#upload').disabled);
  await page.setInputFiles('#upload',pdf);
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===1);
  await page.setInputFiles('#upload',docx);
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);
  assert.match(await page.locator('#files').textContent(),/fixture\.pdf/);
  assert.match(await page.locator('#files').textContent(),/fixture\.docx/);
  assert.equal(await page.locator('#evidence-list').textContent(),'','Unverified upload cannot create evidence');
  await page.reload();await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);
  assert.match(await page.locator('#files').textContent(),/fixture\.pdf/);
  assert.match(await page.locator('#files').textContent(),/fixture\.docx/);
  assert.equal(await page.locator('#evidence-list').textContent(),'');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'PASS',checks:['pdf-upload','docx-upload','both-source-files-persist-after-reload','no-auto-accepted-evidence','no-browser-errors'],supabase_live_roundtrip:false,document_semantics_verified:false}));
 }finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(error=>{console.error(error);process.exitCode=1;});
