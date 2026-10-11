/* Stage13 Chromium smoke: upload PDF + DOCX in one session, restart UI, verify originals retained. */
const {stopChild}=require('./stop_child.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-stage13-ui-'));let child,browser;
 try{
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:'http://127.0.0.1:9',GOOGLE_DRIVE_CLIENT_ID:'',GOOGLE_DRIVE_CLIENT_SECRET:'',GOOGLE_DRIVE_REFRESH_TOKEN:''}});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Launcher timeout')),15000);child.stdout.on('data',data=>{log+=data;const match=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve(match[1]);}});child.once('exit',code=>{clearTimeout(timer);reject(Error('Launcher exit '+code));});});
  const fixture=spawnSync(process.env.PYTHON||'python3',['-c',`import io,sys,zipfile,fitz
d=fitz.open();d.new_page().insert_text((40,70),'Stage 13 engineering evidence');pdf=d.tobytes()
b=io.BytesIO()
with zipfile.ZipFile(b,'w') as z:
 z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
 z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Stage 13 report</w:t></w:r></w:p></w:body></w:document>')
sys.stdout.buffer.write(len(pdf).to_bytes(8,'big')+pdf+b.getvalue())`],{cwd:root});
  assert.equal(fixture.status,0,fixture.stderr?.toString());
  const n=Number(fixture.stdout.readBigUInt64BE(0)),pdf=fixture.stdout.subarray(8,8+n),docx=fixture.stdout.subarray(8+n);
  browser=await chromium.launch({headless:true});const page=await browser.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#upload').disabled);
  await page.setInputFiles('#upload',{name:'stage13-original.pdf',mimeType:'application/pdf',buffer:pdf});
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===1);
  await page.setInputFiles('#upload',{name:'stage13-original.docx',mimeType:'application/vnd.openxmlformats-officedocument.wordprocessingml.document',buffer:docx});
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);
  await page.reload();
  await page.waitForFunction(()=>document.querySelectorAll('.file').length===2);
  const listing=await page.locator('#files').textContent();
  assert.ok(listing.includes('stage13-original.pdf'),'PDF original missing after reload');
  assert.ok(listing.includes('stage13-original.docx'),'DOCX original missing after reload');
  assert.equal(await page.locator('#evidence-list').textContent(),'','unreviewed upload must not auto-create accepted evidence');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'PASS',real_chromium:true,checks:['pdf-docx-same-session-upload','source-reload','no-automatic-evidence'],supabase_live_roundtrip:false,engineering_acceptance:false}));
 }finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(error=>{console.error(error);process.exitCode=1;});
