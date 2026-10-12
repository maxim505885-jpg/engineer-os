/* Real Chromium DOM + vendored renderer test. npm --prefix e2e ci first. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
let chromium;
try { ({chromium} = require('../e2e/node_modules/playwright')); }
catch (_) { ({chromium} = require('playwright')); }
const ui = path.resolve(__dirname, '../engineering/local_app/ui');
const sourceFixture = process.env.PDF_VIEWER_SOURCE;
const viewer = fs.readFileSync(path.join(ui, 'pdf-viewer.js'), 'utf8');
const CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; worker-src 'self'; font-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'";
const fake = `
export const GlobalWorkerOptions = {};
export function getDocument(options) {
  window.options = options;
  const marker = options.data[0];
  let dead = false;
  const task = {destroy() {dead=true; window.destroyed=(window.destroyed||0)+1; return Promise.resolve();}};
  const pdf={numPages:3,destroy:task.destroy,getPage:async n=>{
    await new Promise(r=>setTimeout(r,15));
    return {getViewport:({scale})=>({width:100000*scale,height:100000*scale}),cleanup(){},render:({canvasContext,annotationMode})=>{
      window.annotations=annotationMode; window.active=(window.active||0)+1; window.maxActive=Math.max(window.maxActive||0,window.active);
      let reject, done=false;
      const promise = new Promise((resolve, fail)=>{reject=fail;setTimeout(()=>{if(done)return;done=true;window.active--;canvasContext.fillRect(0,0,2,2);resolve();},35);});
      return {promise,cancel(){if(done)return;done=true;window.active--;const e=new Error('cancelled');e.name='RenderingCancelledException';reject(e);}};
    }};
  }};
  task.promise=new Promise((resolve,reject)=>setTimeout(()=>{
    if(marker===3){task.onPassword();reject(new Error('password'));}
    else if(marker===4)reject(new Error('invalid'));
    else resolve(pdf);
  },marker===2?75:1));
  return task;
}`;
function pdfBytes() {
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R /OpenAction << /S /JavaScript /JS (globalThis.PDF_ACTION_EXECUTED=true) >> >>',
    '<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 240] /Resources << >> /Contents 4 0 R >>',
    '<< /Length 28 >>\nstream\n0 0 1 rg 20 20 100 100 re f\n\nendstream',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 240] /Resources << >> /Contents 6 0 R >>',
    '<< /Length 28 >>\nstream\n1 0 0 rg 20 20 100 100 re f\n\nendstream',
  ];
  let text = '%PDF-1.7\n', offsets=[0];
  objects.forEach((object,i)=>{offsets.push(Buffer.byteLength(text));text+=`${i+1} 0 obj\n${object}\nendobj\n`;});
  const start=Buffer.byteLength(text);
  text+=`xref\n0 7\n0000000000 65535 f \n`+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('');
  text+=`trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n${start}\n%%EOF\n`;
  return [...Buffer.from(text)];
}
async function domTests() {
  const {JSDOM} = require('../e2e/node_modules/jsdom');
  const dom = new JSDOM('<button id="launch">Launch</button>', {runScripts:'outside-only',url:'http://127.0.0.1/'});
  const w = dom.window;
  w.HTMLDialogElement.prototype.showModal = function(){this.open=true;};
  w.HTMLCanvasElement.prototype.getContext = () => ({fillRect(){}});
  w.__pdfLibrary = w.eval('(function(){'+fake.replaceAll('export ', '')+';return {GlobalWorkerOptions,getDocument};})()');
  w.eval(viewer.replace("import('/vendor/pdfjs/pdf.mjs')", 'Promise.resolve(window.__pdfLibrary)'));
  const sleep = ms => new Promise(r=>setTimeout(r,ms));
  const until = async predicate => {for(let n=0;n<100;n++){if(predicate())return;await sleep(10);}throw Error('DOM state timeout');};
  const status = () => w.document.querySelector('.pdf-viewer-status')?.textContent || '';
  const click = text => [...w.document.querySelectorAll('button')].find(n=>n.textContent===text).click();
  try {
    w.document.querySelector('#launch').focus();
    await w.openPDFViewer(new w.Uint8Array([1]),'a'.repeat(64),'<img src=x>');
    await until(()=>status().includes('содержимое источника не проверено'));
    assert.equal(w.document.querySelectorAll('dialog').length,1);
    assert.equal(w.document.querySelectorAll('dialog img, dialog [style]').length,0);
    assert.equal(w.document.querySelector('.pdf-viewer-caption').textContent,'<img src=x>');
    assert.equal(w.options.isEvalSupported,false);assert.equal(w.options.useWasm,false);
    assert.equal(w.options.enableXfa,false);assert.equal(w.options.useWorkerFetch,false);
    assert.equal(w.options.disableFontFace,true);assert.equal(w.options.useSystemFonts,false);
    assert.equal(w.annotations,0);
    const canvas=w.document.querySelector('canvas');assert.ok(canvas.width*canvas.height<=4000000);
    click('Следующая страница');click('Увеличить');click('Предыдущая страница');
    await until(()=>status().includes('содержимое источника не проверено'));assert.equal(w.maxActive,1);
    w.document.querySelector('dialog').dispatchEvent(new w.Event('cancel',{cancelable:true}));
    assert.equal(w.document.querySelectorAll('dialog').length,0);assert.equal(w.document.activeElement.id,'launch');
    await w.openPDFViewer(new w.Uint8Array([1]),'a','render-close');
    await sleep(20);w.closePDFViewer();await sleep(70);assert.equal(w.document.querySelectorAll('dialog').length,0);
    const old=w.openPDFViewer(new w.Uint8Array([2]),'old','old');
    const fresh=w.openPDFViewer(new w.Uint8Array([1]),'new','new');
    await Promise.all([old,fresh]);await sleep(90);
    assert.equal(w.document.querySelectorAll('dialog').length,1);assert.equal(w.document.querySelector('.pdf-viewer-caption').textContent,'new');
    await w.openPDFViewer(new w.Uint8Array([3]),'pw','pw');assert.match(status(),/^Предпросмотр PDF с паролем/);
    await w.openPDFViewer(new w.Uint8Array([4]),'bad','bad');assert.match(status(),/^Предпросмотр PDF недоступен/);
    await assert.rejects(w.openPDFViewer(new w.Uint8Array(0),'',''),/100 MiB/);
    console.log('PASS: jsdom modal controls, bounds, safe options, source identity text escaping, stale-load and active-render close races, unavailable/password errors.');
  } finally {w.closePDFViewer();dom.window.close();}
}
(async()=>{
  if(process.argv.includes('--dom')) {await domTests();return;}
  const requests=[];
  const assets=new Map([
    ['/vendor/pdfjs/pdf.mjs',path.join(ui,'vendor/pdfjs/pdf.mjs')],
    ['/vendor/pdfjs/pdf.worker.mjs',path.join(ui,'vendor/pdfjs/pdf.worker.mjs')]
  ]);
  const server=http.createServer((req,res)=>{
    requests.push(req.url);res.setHeader('Content-Security-Policy',CSP);
    res.setHeader('Content-Type',(req.url.endsWith('.css')?'text/css':req.url.endsWith('.mjs')||req.url.endsWith('.js')?'text/javascript':'text/html')+'; charset=utf-8');
    if(req.url==='/') return res.end('<!doctype html><link rel="stylesheet" href="/test.css"><button id="launch">Launch</button><script src="/pdf-viewer.js"></script>');
    if(req.url==='/source-fixture.pdf' && sourceFixture){res.setHeader('Content-Type','application/pdf');return fs.createReadStream(sourceFixture).pipe(res);}
    if(req.url==='/test.css')return res.end('.pdf-viewer{max-width:95vw;max-height:95vh}.pdf-viewer-canvas-wrap{overflow:auto;max-height:65vh}.pdf-viewer-canvas{display:block}');
    if(req.url==='/pdf-viewer.js')return res.end(viewer);
    if(req.url==='/vendor/pdfjs/pdf.mjs' && server.mock) return res.end(fake);
    if(assets.has(req.url))return res.end(fs.readFileSync(assets.get(req.url)));
    res.writeHead(404);res.end();
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const origin=`http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser=await chromium.launch({headless:true,args:['--no-sandbox']});
    server.mock=true;
    const page=await browser.newPage();
    await page.goto(origin);await page.locator('#launch').focus();
    await page.evaluate(()=>openPDFViewer(new Uint8Array([1]),'a'.repeat(64),'<img src=x onerror=alert(1)>'));
    await page.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.includes('содержимое источника не проверено'));
    assert.equal(await page.locator('dialog').count(),1);
    assert.equal(await page.locator('dialog img').count(),0);
    assert.equal(await page.locator('.pdf-viewer-caption').first().textContent(),'<img src=x onerror=alert(1)>');
    assert.equal(await page.locator('dialog [style]').count(),0);
    const safe = await page.evaluate(()=>({eval:options.isEvalSupported,xfa:options.enableXfa,wasm:options.useWasm,workerFetch:options.useWorkerFetch,font:options.disableFontFace,systemFont:options.useSystemFonts,annotations}));
    assert.deepEqual(safe,{eval:false,xfa:false,wasm:false,workerFetch:false,font:true,systemFont:false,annotations:0});
    const bounds=await page.locator('canvas').evaluate(c=>[c.width,c.height]);
    assert.ok(bounds[0]*bounds[1]<=4000000 && Math.max(...bounds)<=4096);
    await page.getByRole('button',{name:'Следующая страница'}).click();
    await page.getByRole('button',{name:'Увеличить',exact:true}).click();
    await page.getByRole('button',{name:'Предыдущая страница'}).click();
    await page.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.includes('содержимое источника не проверено'));
    assert.equal(await page.evaluate(()=>maxActive),1);
    await page.keyboard.press('Escape');assert.equal(await page.locator('dialog').count(),0);
    assert.equal(await page.evaluate(()=>document.activeElement.id),'launch');
    await page.evaluate(()=>{void openPDFViewer(new Uint8Array([2]),'old','old');closePDFViewer();});
    await page.waitForTimeout(100);assert.equal(await page.locator('dialog').count(),0);
    await page.evaluate(()=>{void openPDFViewer(new Uint8Array([2]),'old','old');void openPDFViewer(new Uint8Array([1]),'new','new');});
    await page.waitForTimeout(120);assert.equal(await page.locator('dialog').count(),1);
    assert.equal(await page.locator('.pdf-viewer-caption').first().textContent(),'new');
    await page.evaluate(()=>openPDFViewer(new Uint8Array([3]),'pw','password'));
    await page.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.startsWith('Предпросмотр PDF с паролем'));
    await page.evaluate(()=>openPDFViewer(new Uint8Array([4]),'bad','bad'));
    await page.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.startsWith('Предпросмотр PDF недоступен'));
    assert.match(await page.evaluate(async()=>{try{await openPDFViewer(new Uint8Array(0),'','')}catch(e){return e.message}}),/100 MiB/);
    await page.close();
    server.mock=false;requests.length=0;
    const real=await browser.newPage();const errors=[];
    real.on('pageerror',e=>errors.push(e.message));
    await real.goto(origin);
    await real.evaluate(bytes=>openPDFViewer(new Uint8Array(bytes),'b'.repeat(64),'Actual two-page PDF'),pdfBytes());
    await real.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.includes('содержимое источника не проверено'));
    assert.match(await real.locator('.pdf-viewer-controls').textContent(),/Страница 1 \/ 2/);
    await real.getByRole('button',{name:'Следующая страница'}).click();
    await real.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.includes('содержимое источника не проверено'));
    assert.match(await real.locator('.pdf-viewer-controls').textContent(),/Страница 2 \/ 2/);
    assert.equal(await real.evaluate(()=>globalThis.PDF_ACTION_EXECUTED),undefined);
    assert.ok(requests.includes('/vendor/pdfjs/pdf.worker.mjs'));
    assert.ok(requests.every(url=>['/','/test.css','/pdf-viewer.js','/vendor/pdfjs/pdf.mjs','/vendor/pdfjs/pdf.worker.mjs','/favicon.ico'].includes(url)),requests.join(','));
    assert.deepEqual(errors,[]);
    await real.getByRole('button',{name:'Закрыть PDF'}).click();assert.equal(await real.locator('dialog').count(),0);
    if(sourceFixture){
      const sha=require('node:crypto').createHash('sha256').update(fs.readFileSync(sourceFixture)).digest('hex');
      await real.evaluate(async sha=>{const response=await fetch('/source-fixture.pdf');await openPDFViewer(new Uint8Array(await response.arrayBuffer()),sha,'V4 оригинал');},sha);
      await real.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.includes('содержимое источника не проверено'),null,{timeout:120000});
      const position=await real.locator('.pdf-viewer-controls').textContent();
      const total=Number(position.match(/\/ (\d+)/)[1]);
      assert.ok(total>0);assert.ok((await real.locator('.pdf-viewer-caption').nth(1).textContent()).includes(sha));
      await real.evaluate(total=>{const next=[...document.querySelectorAll('dialog button')].find(b=>b.textContent==='Следующая страница');for(let i=1;i<total;i++)next.click();},total);
      await real.waitForFunction(()=>document.querySelector('.pdf-viewer-status').textContent.includes('содержимое источника не проверено'),null,{timeout:120000});
      assert.ok((await real.locator('.pdf-viewer-controls').textContent()).includes(`Страница ${total} / ${total}`));
      const pixels=await real.locator('canvas').evaluate(c=>c.width*c.height);assert.ok(pixels<=4000000);
      if(process.env.PDF_VIEWER_SCREENSHOT)await real.screenshot({path:process.env.PDF_VIEWER_SCREENSHOT});
      assert.deepEqual(errors,[]);
      console.log(`PASS actual source: bytes=${fs.statSync(sourceFixture).size} sha256=${sha} pages=${total} first/last rendered canvasPixels=${pixels}`);
      await real.evaluate(()=>closePDFViewer());
    }
    console.log('PASS: Chromium DOM controls, bounds, stale loads, close cancellation, safe settings; real offline PDF.js two-page raster and embedded-JS non-execution.');
  } finally {if(browser)await browser.close();await new Promise(r=>server.close(r));}
})().catch(error=>{console.error(error);process.exitCode=1;});
