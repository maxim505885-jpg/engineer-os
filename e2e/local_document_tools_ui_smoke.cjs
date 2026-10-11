/* Actual app UI: local PDF viewer, optional table availability, source formula. */
const {stopChild}=require('./stop_child.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process'),{chromium}=require('playwright');
(async()=>{let child,browser;const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-tools-'));
try{
const fixture=`import sys,fitz,shutil
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.server import make_server
from tests.test_office_documents import Model
from tests.test_word_formula_preview import document
s=Store(sys.argv[1]);sid=s.create_session()['id'];pdf=fitz.open();p=pdf.new_page(width=400,height=300);p.insert_text((40,60),'Source table A 1');p=pdf.new_page(width=400,height=300);p.insert_text((40,60),'Second source page')
f=preserve_file(s,sid,'tools.pdf',pdf.tobytes());pdf.close()
word=preserve_file(s,sid,'tools.docx',document('<m:oMath><m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f></m:oMath>'))
m=Model();m.health=lambda:dict(model='synthetic',available=True,note='fixture',state='READY')
server=make_server(s,m,drive_client=None);print('ORIGIN '+server.origin,flush=True);server.serve_forever()`;
child=spawn(process.env.PYTHON||'python3',['-u','-c',fixture,temp],{cwd:path.resolve(__dirname,'..')});
const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);child.stdout.on('data',d=>{log+=d;const m=log.match(/ORIGIN (http:\/\/127\.0\.0\.1:\d+)/);if(m){clearTimeout(timer);resolve(m[1]);}});child.stderr.on('data',d=>{log+=d;});child.once('exit',c=>{clearTimeout(timer);reject(Error('Fixture exit '+c+' '+log));});});
browser=await chromium.launch({headless:true});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
const pdfCard=page.locator('.file').filter({has:page.getByText('tools.pdf',{exact:true})});
await pdfCard.locator('.pdf-viewer-open').click();await page.waitForFunction(()=>document.querySelector('.pdf-viewer-status')?.textContent.includes('Оригинальная страница PDF'));
assert.match(await page.locator('.pdf-viewer-caption').first().textContent(),/tools.pdf/);
await page.getByRole('button',{name:'Следующая страница',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.pdf-viewer-controls')?.textContent.includes('Страница 2 / 2'));
await page.keyboard.press('Escape');assert.equal(await page.locator('dialog').count(),0);
await pdfCard.locator('.source-assets > summary').click();await pdfCard.locator('.region-readback > summary').click();
for(const [label,value] of [['Слева','0'],['Сверху','0'],['Справа','200'],['Снизу','100']])await pdfCard.getByLabel(label+' · точки PDF',{exact:true}).fill(value);
await pdfCard.locator('.table-read').click();await page.waitForFunction(()=>document.querySelector('.region-result')?.textContent.includes('UNAVAILABLE'));
assert.match(await pdfCard.locator('.region-result').textContent(),/source_sha256/);
const wordCard=page.locator('.file').filter({has:page.getByText('tools.docx',{exact:true})});
await wordCard.locator('.source-assets > summary').click();await wordCard.getByRole('button',{name:'Прочитать активы',exact:true}).click();
await wordCard.locator('.formula-preview').click();
await page.waitForFunction(()=>document.querySelector('.formula-result img')?.naturalWidth>0||document.querySelector('#error')?.textContent.includes('converter unavailable'),{},{timeout:65000});
const rendered=await wordCard.locator('.formula-result img').count();
if(process.env.ENGINEER_OS_FORMULA_REQUIRED==='1')assert.equal(rendered,1);
if(rendered){assert.match(await wordCard.locator('.formula-result').textContent(),/mathematics_verified|math_verified/);assert.match(await wordCard.locator('.formula-result').textContent(),/UNCERTAINTY/);}
assert.equal(await page.locator('#evidence-list').textContent(),'');assert.deepEqual(errors,[]);
console.log(JSON.stringify({result:'PASS',checks:['actual-app-pdfjs-two-pages','authenticated-source-hash','table-unavailable-raster-source-dossier','formula-source-bound-preview-or-unavailable','no-created-evidence'],formula_rendered:!!rendered,engineering_acceptance:false}));
}finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(e=>{console.error(e);process.exitCode=1;});
