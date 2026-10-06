/* DOM integration (jsdom), actual launcher/worker, synthetic model protocol.
   This verifies UI behavior, not browser rendering or Windows. */
const assert=require('node:assert/strict');const fs=require('node:fs');const os=require('node:os');const path=require('node:path');
const http=require('node:http');const {spawn}=require('node:child_process');const {JSDOM,VirtualConsole}=require('jsdom');
async function until(check){const end=Date.now()+10000;while(Date.now()<end){if(check())return;await new Promise(resolve=>setTimeout(resolve,40));}throw new Error('DOM condition timeout');}
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-os-dom-'));
 const requests=[],errors=[];let child,dom;
 const model=http.createServer((req,res)=>{res.setHeader('Content-Type','application/json');if(req.method==='GET'){res.end(JSON.stringify({data:[{id:'qwen3:8b'}]}));return;}let raw='';req.on('data',data=>raw+=data);req.on('end',()=>{requests.push(JSON.parse(raw));res.end(JSON.stringify({choices:[{message:{content:'СИНТЕТИЧЕСКИЙ ОТВЕТ. <script>window.injected=true</script>'}}]}));});});
 try{
  await new Promise(resolve=>model.listen(0,'127.0.0.1',resolve));
  child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:`http://127.0.0.1:${model.address().port}`,ENGINEER_OS_LOCAL_MODEL:'qwen3:8b',ENGINEER_OS_LOCAL_PROVIDER:'ollama',ENGINEER_OS_LOCAL_MODEL_KEY:''}});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Launcher timeout')),10000);child.stdout.on('data',data=>{log+=data;const f=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(f){clearTimeout(timer);resolve(f[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(Error(`Launcher exited ${code}`));});});
  const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
  async function open(){return JSDOM.fromURL(origin,{resources:'usable',runScripts:'dangerously',virtualConsole:vc,beforeParse(win){win.fetch=(input,options)=>fetch(new URL(input,origin),options);}});}
  dom=await open();let win=dom.window,doc=win.document;await until(()=>doc.querySelector('nav .session')&&!doc.querySelector('#prompt').disabled);
  const source=Buffer.from('ТЗ: высота 4 м');const upload=doc.querySelector('#upload');Object.defineProperty(upload,'files',{value:[{name:'ТЗ.md',size:source.length,arrayBuffer:async()=>new win.Uint8Array(source).buffer}]});
  upload.dispatchEvent(new win.Event('change'));try{await until(()=>doc.querySelector('.file')&&!doc.querySelector('#send').disabled);}catch(e){throw new Error(e.message+': '+doc.querySelector('#error').textContent+' / '+errors.join(';'));}
  doc.querySelector('#prompt').value='Проверь высоту по ТЗ';doc.querySelector('#composer').dispatchEvent(new win.Event('submit',{cancelable:true}));
  await until(()=>doc.querySelector('.message.assistant')&&!doc.querySelector('#send').disabled);
  assert.equal(requests.length,1);assert.ok(JSON.stringify(requests[0]).includes('высота 4 м'));assert.equal(win.injected,undefined);
  assert.equal(doc.querySelector('nav .session').disabled,false,'Conversation navigation must re-enable after sending');
  dom.window.close();dom=await open();win=dom.window;doc=win.document;await until(()=>doc.querySelector('.message.assistant'));assert.equal(doc.querySelectorAll('.file').length,1);
  doc.querySelector('#new-chat').click();await until(()=>doc.querySelectorAll('nav .session').length===2&&doc.querySelectorAll('.message').length===0);
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Проверь высоту по ТЗ').click();await until(()=>doc.querySelector('.message.assistant'));
  assert.ok(doc.querySelector('#task-mode'),'Explicit engineering preparation mode must be available');
  doc.querySelector('#task-mode').value='CORE_PLAN';doc.querySelector('.file input').click();
  doc.querySelector('#prompt').value='ТЗ: проверить отчёт и нормы';
  doc.querySelector('#composer').dispatchEvent(new win.Event('submit',{cancelable:true}));
  await until(()=>doc.querySelector('.core-plan')&&!doc.querySelector('#send').disabled);
  assert.equal(requests.length,1,'CORE preparation must not call model');
  assert.ok(doc.querySelector('.core-plan').textContent.includes('FINAL AUDIT'));
  assert.ok(doc.querySelector('.core-plan').textContent.includes('ТЗ.md'));
  dom.window.close();dom=await open();doc=dom.window.document;
  await until(()=>doc.querySelectorAll('nav .session').length===2);
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Проверь высоту по ТЗ').click();
  await until(()=>doc.querySelector('.core-plan'));
  assert.ok(doc.querySelector('#evidence-form'),'Source candidate form must exist');
  doc.querySelector('#evidence-file').value=doc.querySelector('#evidence-file option').value;
  doc.querySelector('#evidence-quote').value='ТЗ: высота 4 м';
  doc.querySelector('#evidence-statement').value='<script>window.forged=true</script>';
  doc.querySelector('#evidence-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
  await until(()=>doc.querySelector('.evidence-card'));
  assert.ok(doc.querySelector('.evidence-card').textContent.includes('UNVERIFIED'));
  assert.ok(doc.querySelector('.provenance-status').textContent.includes('неприменимы'),'TXT must not invent PDF geometry');
  assert.equal(dom.window.forged,undefined);
  dom.window.close();dom=await open();doc=dom.window.document;
  await until(()=>doc.querySelectorAll('nav .session').length===2);
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Проверь высоту по ТЗ').click();
  await until(()=>doc.querySelector('.evidence-card'));
  doc.querySelector('#evidence-quote').value='Unsaved previous source';
  doc.querySelector('#evidence-statement').value='Unsaved previous assertion';
  doc.querySelector('#evidence-page').value='12';
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Новый диалог').click();
  await until(()=>doc.querySelector('#title').textContent==='Новый диалог');
  assert.equal(doc.querySelector('#evidence-quote').value,'','Draft source quote must not cross conversations');
  assert.equal(doc.querySelector('#evidence-statement').value,'');
  assert.equal(doc.querySelector('#evidence-page').value,'');
  assert.ok(doc.querySelector('#source-viewer'),'Persistent source viewer must exist');
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Проверь высоту по ТЗ').click();
  await until(()=>doc.querySelector('.evidence-card'));
  const pdf=require('node:child_process').execFileSync(process.env.PYTHON||'python3',['-c',"import fitz,sys; d=fitz.open();d.new_page().insert_text((40,40),'height 4m');sys.stdout.buffer.write(d.tobytes())"]);
  const token=doc.querySelector('meta[name="app-token"]').content;
  const sessions=await (await fetch(origin+'/api/sessions',{headers:{'X-Engineer-Token':token}})).json();
  const id=sessions.find(s=>s.title==='Проверь высоту по ТЗ').id;
  const file=await (await fetch(origin+`/api/sessions/${id}/files?name=preview.pdf`,{method:'POST',headers:{'X-Engineer-Token':token,'Content-Type':'application/octet-stream'},body:pdf})).json();
  await fetch(origin+`/api/sessions/${id}/evidence`,{method:'POST',headers:{'X-Engineer-Token':token,'Content-Type':'application/json'},body:JSON.stringify({file_id:file.id,page:1,quote:'height 4m',statement:'Unverified preview'})});
  await until(()=>doc.querySelector('.preview-button'));
  doc.querySelector('.preview-button').click();
  await until(()=>doc.querySelector('#source-image').src.startsWith('data:image/png'));
  assert.ok(doc.querySelector('#source-caption').textContent.includes('preview.pdf'));
  assert.ok(doc.querySelector('#source-caption').textContent.includes('не подтверждает'));
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Новый диалог').click();
  await until(()=>doc.querySelector('#title').textContent==='Новый диалог');
  assert.equal(doc.querySelector('#source-viewer').hidden,true,'Preview must not cross conversations');
  assert.ok(doc.querySelector('#review-form'),'Persistent review form missing');
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Проверь высоту по ТЗ').click();
  await until(()=>doc.querySelector('.review-button'));
  doc.querySelector('.review-button').click();
  doc.querySelector('#review-decision').value='SOURCE_CONFIRMED';
  doc.querySelector('#review-note').value='Source checked <script>window.reviewInjected=true</script>';
  doc.querySelector('#review-actor').value='Local reviewer';
  await new Promise(resolve=>setTimeout(resolve,1700));
  assert.ok(doc.querySelector('#review-note').value.includes('Source checked'),'Polling must preserve review draft');
  doc.querySelector('#review-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
  await until(()=>doc.querySelector('.review-history'));
  assert.equal(dom.window.reviewInjected,undefined);
  assert.ok(doc.querySelector('.review-history').textContent.includes('Source checked'));
  doc.querySelector('.review-button').click();doc.querySelector('#review-note').value='Unsaved review';
  [...doc.querySelectorAll('nav .session')].find(b=>b.textContent==='Новый диалог').click();
  await until(()=>doc.querySelector('#title').textContent==='Новый диалог');
  assert.equal(doc.querySelector('#review-panel').hidden,true);
  assert.equal(doc.querySelector('#review-note').value,'');
  assert.equal(errors.length,0,errors.join('\n'));console.log(JSON.stringify({result:'PASS',dom_emulation:true,browser_visual_check:false,synthetic_model:true,real_ollama:false,checks:['launcher','background-worker','upload-action','source-context','chat','inert-markup','history-reload','session-switch','core-plan-no-model','core-plan-reload','evidence-register','inert-evidence','evidence-reload','evidence-draft-isolation','source-preview','preview-isolation','source-review','review-draft-poll','review-isolation'],requests:requests.length}));
 }finally{
  if(dom)dom.window.close();if(child){child.kill('SIGINT');await new Promise(resolve=>{if(child.exitCode!==null)return resolve();const t=setTimeout(()=>{child.kill('SIGKILL');resolve();},2500);child.once('exit',()=>{clearTimeout(t);resolve();});});}
  await new Promise(resolve=>model.close(resolve));fs.rmSync(temp,{recursive:true,force:true});
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
