/* Real browser: authenticated native table candidate and source payload readback. */
const {stopChild}=require('./stop_child.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process'),{chromium}=require('playwright');
(async()=>{let child,browser;const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-assets-'));
try{
const fixture=`import sys,fitz
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.server import make_server
from tests.test_office_documents import Model
from tests.test_word_embedded_layers import doc,R
from tests.test_ole_bitmap import compound,bmp
from engineering.local_app.worker import Worker
s=Store(sys.argv[1]);sid=s.create_session()['id'];pdf=fitz.open();p=pdf.new_page()
for x in (40,140,240):p.draw_line((x,40),(x,140))
for y in (40,90,140):p.draw_line((40,y),(240,y))
for x,y,t in ((50,65,'A'),(150,65,'B'),(50,115,'1'),(150,115,'2')):p.insert_text((x,y),t)
f=preserve_file(s,sid,'cells.pdf',pdf.tobytes());pdf.close()
payload=compound([('CONTENTS',bmp())])
data=doc('<w:p><w:object><o:OLEObject Type="Embed" ProgID="PBrush" r:id="obj"/></w:object></w:p>',f'<Relationship Id="obj" Type="{R}/oleObject" Target="embeddings/a.bin"/>',{'word/embeddings/a.bin':payload})
obj=preserve_file(s,sid,'objects.docx',data);m=Model();s.enqueue(sid,'Read object source',[obj['id']]);Worker(s,m).run_once()
server=make_server(s,m,drive_client=None);print('ORIGIN http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()`;
child=spawn(process.env.PYTHON||'python3',['-u','-c',fixture,temp],{cwd:path.resolve(__dirname,'..')});
const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);child.stdout.on('data',d=>{log+=d;const m=log.match(/ORIGIN (http:\/\/127\.0\.0\.1:\d+)/);if(m){clearTimeout(timer);resolve(m[1]);}});child.once('exit',c=>{clearTimeout(timer);reject(Error('Fixture exit '+c));});});
browser=await chromium.launch({headless:true});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
const pdfCard=page.locator('.file').filter({has:page.getByText('cells.pdf',{exact:true})});
await pdfCard.locator('.source-assets > summary').click();await pdfCard.getByRole('button',{name:'Прочитать активы',exact:true}).click();
await page.getByRole('button',{name:'Показать ячейки',exact:true}).click();
await page.waitForSelector('.source-assets table');assert.deepEqual(await page.locator('.source-assets td').evaluateAll(cells=>cells.map(c=>c.firstChild.textContent)),['A','B','1','2']);
await pdfCard.getByLabel('Страница таблиц cells.pdf').fill('2');await pdfCard.locator('.region-select').first().click();assert.equal(await pdfCard.getByLabel('Страница фрагмента',{exact:true}).inputValue(),'1');
await pdfCard.getByLabel('Расположение текста фрагмента',{exact:true}).selectOption('7');
const profileResponse=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/regions'));
await pdfCard.locator('.region-read').click();const profileReceipt=await (await profileResponse).json();
assert.equal(profileReceipt.result.request_binding.ocr_psm,7);assert.equal(profileReceipt.result.request_binding.ocr,false);
await page.waitForSelector('.region-result img');
assert.ok((await pdfCard.locator('.region-result').textContent()).includes('A'));
assert.ok((await pdfCard.locator('.region-result').textContent()).includes('UNCERTAINTY'));
await page.reload();const restored=page.locator('.file').filter({has:page.getByText('cells.pdf',{exact:true})});
await restored.locator('.source-assets > summary').click();await restored.locator('.region-readback > summary').click();await restored.locator('.region-history').click();await restored.locator('.region-history-open').click();await page.waitForSelector('.region-result img');
assert.ok((await restored.locator('.region-result').textContent()).includes('A'));

assert.ok((await restored.locator('.source-assets').textContent()).includes('UNCERTAINTY'));

const objectCard=page.locator('.file').filter({has:page.getByText('objects.docx',{exact:true})});
await objectCard.locator('.source-assets summary').click();await objectCard.getByRole('button',{name:'Прочитать активы',exact:true}).click();
await objectCard.getByRole('button',{name:'Показать растр OLE',exact:true}).click();
await page.waitForFunction(()=>document.querySelector('#source-image').naturalWidth===40);
assert.ok((await page.locator('#source-caption').textContent()).includes('Объект не активирован'));
await page.getByRole('button',{name:'Закрыть просмотр',exact:true}).click();
await page.getByRole('button',{name:'Результаты по частям',exact:true}).click();await page.locator('.analysis-receipt summary').first().click();
await page.locator('.ole-bitmap').click();await page.waitForFunction(()=>document.querySelector('#source-image').naturalWidth===40);
assert.ok((await page.locator('#source-caption').textContent()).includes('содержание не подтверждено'));
await page.getByRole('button',{name:'Закрыть просмотр',exact:true}).click();
assert.equal(await page.locator('#evidence-list').textContent(),'');assert.deepEqual(errors,[]);
console.log(JSON.stringify({result:'PASS',checks:['single-line-profile-request-binding-native-only','region-source-readback-history-reload','native-table-user-readback','source-bound-candidate','uncertainty-only','no-created-evidence','ole-asset-authenticated-png','ole-checkpoint-png','no-ole-activation'],engineering_acceptance:false}));
}finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(e=>{console.error(e);process.exitCode=1;});
