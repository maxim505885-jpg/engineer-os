/* Actual browser/API/queue; conversion payload is a labeled synthetic fixture. */
const {stopChild}=require('./stop_child.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process'),{chromium}=require('playwright');
(async()=>{let child,browser;const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-render-ui-'));
try{
const fixture=String.raw`import sys,json,hashlib,threading,fitz
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.server import make_server
from engineering.local_app.worker import Worker
from engineering.local_app import office_render_process
from tests.test_office_documents import Model
s=Store(Path(sys.argv[1]));sid=s.create_session()['id'];original=preserve_file(s,sid,'owned.docx',b'PK\x03\x04owned fixture')
(s.root/'office-renderer.json').write_text(json.dumps(dict(bundle_root=str(s.root/'owned-bundle'),manifest_sha256='a'*64)))
pdf=fitz.open();page=pdf.new_page();page.insert_text((40,60),'OWNED UI PDF COPY');data=pdf.tobytes();pdf.close()
def rendered(source,sha,suffix,**kwargs):return data,dict(source_sha256=sha,derived_sha256=hashlib.sha256(data).hexdigest(),scope='DERIVED_UNVERIFIED',acceptance_granted=False)
office_render_process.render_office=rendered
m=Model();m.health=lambda:dict(model='synthetic',available=True,note='fixture',state='READY')
threading.Thread(target=Worker(s,m).run,daemon=True).start()
server=make_server(s,m,drive_client=None);print('ORIGIN '+server.origin,flush=True);server.serve_forever()`;
child=spawn(process.env.PYTHON||'python3',['-u','-c',fixture,temp],{cwd:root,env:process.env});
const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Fixture timeout '+log)),20000);child.stdout.on('data',d=>{log+=d;const m=log.match(/ORIGIN (http:\/\/127\.0\.0\.1:\d+)/);if(m){clearTimeout(timer);resolve(m[1]);}});child.stderr.on('data',d=>{log+=d;});child.once('exit',c=>{clearTimeout(timer);reject(Error('Fixture exit '+c+' '+log));});});
browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1366,height:950}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
const original=page.locator('.file').filter({has:page.getByText('owned.docx',{exact:true})});await original.getByRole('button',{name:'Создать PDF-копию',exact:true}).click();
const derived=page.locator('.file').filter({has:page.getByText('owned — PDF-копия.pdf',{exact:true})});await derived.waitFor({state:'visible',timeout:20000});
assert.match(await derived.textContent(),/Производная PDF-копия/);await derived.getByRole('button',{name:'Скачать PDF-копию',exact:true}).waitFor();await derived.getByRole('button',{name:'Просмотреть PDF-копию',exact:true}).click();
await page.waitForFunction(()=>document.querySelector('#source-image')?.naturalWidth>0);assert.match(await page.locator('#source-caption').textContent(),/PDF-копия/);assert.doesNotMatch(await page.locator('#source-caption').textContent(),/Оригинал для/);
assert.equal(await page.locator('#evidence-list').textContent(),'');assert.deepEqual(errors,[]);
if(process.env.ENGINEER_OS_UI_QA_DIR){fs.mkdirSync(process.env.ENGINEER_OS_UI_QA_DIR,{recursive:true});await page.screenshot({path:path.join(process.env.ENGINEER_OS_UI_QA_DIR,'office-render-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(process.env.ENGINEER_OS_UI_QA_DIR,'office-render-mobile.png'),fullPage:true});}
console.log(JSON.stringify({result:'PASS',checks:['browser-create-pdf-copy','actual-queue-and-worker','derived-lineage-labels','preview-copy-caption','no-created-evidence'],converter:'SYNTHETIC_FIXTURE',engineering_acceptance:false}));
}finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(e=>{console.error(e);process.exitCode=1;});
