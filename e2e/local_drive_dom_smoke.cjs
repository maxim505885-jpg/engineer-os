/* jsdom + real local HTTP, synthetic Google transport. No OAuth/live Drive. */
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process'),{JSDOM,VirtualConsole}=require('jsdom');
async function until(check){const end=Date.now()+10000;while(Date.now()<end){if(check())return;await new Promise(r=>setTimeout(r,40));}throw Error('DOM condition timeout');}
const fixture=`
import hashlib,io,json,sys
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.server import make_server
from engineering.storage.google_drive import GoogleDriveClient
data=b'Original height 4m'
class Token:
 def access_token(self):return 'PRIVATE_SYNTHETIC_TOKEN'
def opener(req,timeout):
 if 'alt=media' in req.full_url:return io.BytesIO(data)
 return io.BytesIO(json.dumps(dict(id='drive_original_123',name='original.md',mimeType='text/markdown',size=str(len(data)),md5Checksum=hashlib.md5(data).hexdigest(),modifiedTime='2026-10-06T00:00:00Z',capabilities=dict(canDownload=True),trashed=False)).encode())
class Model:
 def health(self):return dict(available=False,note='Synthetic Drive-only fixture')
server=make_server(Store(Path(sys.argv[1])),Model(),drive_client=GoogleDriveClient(Token(),opener))
print('http://127.0.0.1:'+str(server.server_port),flush=True)
server.serve_forever()
`;
(async()=>{
 const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-drive-dom-'));let child,dom;const errors=[];
 try{
  child=spawn(process.env.PYTHON||'python3',['-u','-c',fixture,temp],{cwd:root});
  const origin=await new Promise((resolve,reject)=>{let raw='';const timer=setTimeout(()=>reject(Error('Server timeout')),10000);child.stderr.on('data',d=>process.stderr.write(d));child.stdout.on('data',d=>{raw+=d;const m=raw.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});child.on('exit',code=>{clearTimeout(timer);reject(Error('Server exited '+code));});});
  const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
  async function open(){return JSDOM.fromURL(origin,{resources:'usable',runScripts:'dangerously',virtualConsole:vc,beforeParse(win){win.fetch=(url,options)=>fetch(new URL(url,origin),options);}});}
  dom=await open();let doc=dom.window.document;await until(()=>!doc.querySelector('#drive-import').disabled);
  assert.ok(doc.querySelector('#drive-status').textContent.includes('доступ проверяется при импорте'));
  doc.querySelector('#drive-source').value='https://drive.google.com/file/d/drive_original_123/view';
  doc.querySelector('#drive-sha').value=require('node:crypto').createHash('sha256').update('Original height 4m').digest('hex');
  doc.querySelector('#drive-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
  await until(()=>doc.querySelector('.file')&&!doc.querySelector('#drive-import').disabled);
  assert.equal(doc.querySelectorAll('.file').length,1);assert.ok(doc.querySelector('.file').textContent.includes('drive_original_123'));
  assert.ok(doc.querySelector('.file input').checked,'Imported original must be selected');
  assert.equal(doc.querySelector('#drive-source').value,'');assert.equal(doc.querySelector('#drive-sha').value,'');
  assert.equal(doc.body.textContent.includes('PRIVATE_SYNTHETIC_TOKEN'),false);
  dom.window.close();dom=await open();doc=dom.window.document;await until(()=>doc.querySelector('.file'));
  assert.ok(doc.querySelector('.file').textContent.includes('drive_original_123'),'Import provenance must survive reload');
  doc.querySelector('#drive-source').value='unsaved_original';doc.querySelector('#drive-sha').value='0'.repeat(64);
  doc.querySelector('#new-chat').click();await until(()=>doc.querySelectorAll('nav .session').length===2&&doc.querySelectorAll('.file').length===0);
  assert.equal(doc.querySelector('#drive-source').value,'');assert.equal(doc.querySelector('#drive-sha').value,'');
  doc.querySelector('#drive-source').value='drive_original_123';doc.querySelector('#drive-sha').value='0'.repeat(64);
  doc.querySelector('#drive-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
  try{await until(()=>doc.querySelector('#error').textContent.includes('SHA256'));}catch(e){throw new Error(e.message+': '+doc.querySelector('#error').textContent+' / '+errors.join(';'));}
  assert.equal(doc.querySelectorAll('.file').length,0,'Failed checksum must not create a file');
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({result:'PASS',dom_emulation:true,live_google:false,oauth_verified:false,browser_visual_check:false,checks:['configured-not-connected','import-submit','selected-original','provenance-reload','no-secret','conversation-isolation','draft-isolation','failed-checksum-no-file']}));
 }finally{if(dom)dom.window.close();if(child){child.kill('SIGTERM');await new Promise(r=>{if(child.exitCode!==null)return r();const t=setTimeout(()=>{child.kill('SIGKILL');r();},2000);child.once('exit',()=>{clearTimeout(t);r();});});}fs.rmSync(temp,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
