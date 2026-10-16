const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),http=require('node:http');
const modulePath=path.resolve(__dirname,'../desktop/server-owner.cjs');
function load(){assert.ok(fs.existsSync(modulePath),'Desktop backend owner is unavailable');return require(modulePath);}
const ready=(origin='http://127.0.0.1:8766')=>({schema:'ENGINEER_OS_DESKTOP_READY_V1',pid:123,origin,build:{source_sha256:'a'.repeat(64),data_root_sha256:'b'.repeat(64),database_schema_version:3,status:'UNCERTAINTY',artifact_verified:false}});
test('accepts only canonical loopback startup descriptor',()=>{const {validateReady}=load();assert.equal(validateReady(ready()).origin,ready().origin);for(const origin of ['https://127.0.0.1:80','http://localhost:8766','http://127.0.0.1:0','http://127.0.0.1:8766/foreign','http://u@127.0.0.1:8766'])assert.throws(()=>validateReady(ready(origin)));assert.throws(()=>validateReady({...ready(),build:{}}));});
test('startup reader rejects duplicate and oversized records',()=>{const {ReadyReader}=load();const r=new ReadyReader();assert.equal(r.push('noise\nENGINEER_OS_DESKTOP_'),null);assert.equal(r.push('READY '+JSON.stringify(ready())+'\n').pid,123);assert.throws(()=>r.push('ENGINEER_OS_DESKTOP_READY '+JSON.stringify(ready())+'\n'));assert.throws(()=>new ReadyReader().push('x'.repeat(262145)));});
test('external navigation excludes executable and local protocols',()=>{const {allowedExternal}=load();assert.equal(allowedExternal('https://example.com'),true);for(const url of ['javascript:alert(1)','file:///C:/x','data:text/html,x','ms-settings:','https://u:p@example.com'])assert.equal(allowedExternal(url),false);});
test('IPC requires the owned main frame and exact origin',()=>{const {trustedSender}=load();const frame={url:'http://127.0.0.1:8766/'},sender={mainFrame:frame};assert.equal(trustedSender({sender,senderFrame:frame},sender,'http://127.0.0.1:8766'),true);assert.equal(trustedSender({sender,senderFrame:{...frame}},sender,'http://127.0.0.1:8766'),false);assert.equal(trustedSender({sender:{},senderFrame:{url:'http://127.0.0.1:8766/'}},sender,'http://127.0.0.1:8766'),false);assert.equal(trustedSender({sender,senderFrame:{url:'file:///C:/x'}},sender,'http://127.0.0.1:8766'),false);});
test('HTTP probe rejects a foreign build and never stops it',async()=>{const {verifyBackend}=load();const server=http.createServer((req,res)=>{res.setHeader('content-type',req.url==='/'?'text/html':'application/json');res.end(req.url==='/'?'<meta name="app-token" content="controlled-test-token-123456">':JSON.stringify({...ready().build,source_sha256:'c'.repeat(64)}));});await new Promise(r=>server.listen(0,'127.0.0.1',r));const record=ready('http://127.0.0.1:'+server.address().port);try{await assert.rejects(verifyBackend(record));assert.equal((await fetch(record.origin)).status,200);}finally{await new Promise(r=>server.close(r));}});

 test('cancelling pending startup terminates its owned Python process',async()=>{
 const {startBackend}=load(),os=require('node:os');
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-cancel-'));fs.mkdirSync(path.join(root,'scripts'));
 fs.writeFileSync(path.join(root,'scripts/run_local_app.py'),"import os,time\nprint('STARTED '+str(os.getpid()),flush=True)\ntime.sleep(60)\n");
 const controller=new AbortController();let pid=null;
 try{
 await assert.rejects(startBackend({python:process.env.PYTHON||'python',root,signal:controller.signal,onOutput:chunk=>{const m=String(chunk).match(/STARTED (\d+)/);if(m){pid=+m[1];controller.abort();}},timeoutMs:15000}),/cancel/i);
 assert.ok(pid,'Delayed child actually started');assert.throws(()=>process.kill(pid,0));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
 });
