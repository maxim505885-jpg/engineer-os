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
s=Store(sys.argv[1]);sid=s.create_session()['id'];pdf=fitz.open();p=pdf.new_page()
for x in (40,140,240):p.draw_line((x,40),(x,140))
for y in (40,90,140):p.draw_line((40,y),(240,y))
for x,y,t in ((50,65,'A'),(150,65,'B'),(50,115,'1'),(150,115,'2')):p.insert_text((x,y),t)
f=preserve_file(s,sid,'cells.pdf',pdf.tobytes());pdf.close()
server=make_server(s,Model(),drive_client=None);print('ORIGIN http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()`;
child=spawn(process.env.PYTHON||'python3',['-u','-c',fixture,temp],{cwd:path.resolve(__dirname,'..')});
const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);child.stdout.on('data',d=>{log+=d;const m=log.match(/ORIGIN (http:\/\/127\.0\.0\.1:\d+)/);if(m){clearTimeout(timer);resolve(m[1]);}});child.once('exit',c=>{clearTimeout(timer);reject(Error('Fixture exit '+c));});});
browser=await chromium.launch({headless:true});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);
await page.locator('.source-assets summary').click();await page.getByRole('button',{name:'Прочитать активы',exact:true}).click();
await page.getByRole('button',{name:'Показать ячейки',exact:true}).click();
await page.waitForSelector('.source-assets table');assert.deepEqual(await page.locator('.source-assets td').allTextContents(),['A','B','1','2']);
assert.ok((await page.locator('.source-assets').textContent()).includes('UNCERTAINTY'));
assert.ok((await page.locator('.source-assets').textContent()).includes('растровые ячейки не прочитаны'));
assert.equal(await page.locator('#evidence-list').textContent(),'');assert.deepEqual(errors,[]);
console.log(JSON.stringify({result:'PASS',checks:['native-table-user-readback','source-bound-candidate','uncertainty-only','no-created-evidence'],engineering_acceptance:false}));
}finally{if(browser)await browser.close();await stopChild(child);fs.rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
})().catch(e=>{console.error(e);process.exitCode=1;});
