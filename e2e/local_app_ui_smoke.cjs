/* Synthetic model protocol, actual launcher/worker, Chromium UI and persistence. */
const assert=require('node:assert/strict');
const fs=require('node:fs');const os=require('node:os');const path=require('node:path');
const http=require('node:http');const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
(async()=>{
  const root=path.resolve(__dirname,'..');const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-os-ui-'));
  let child,browser;const requests=[];
  const model=http.createServer((req,res)=>{
    res.setHeader('Content-Type','application/json');
    if(req.method==='GET'){res.end(JSON.stringify({data:[{id:'qwen3:8b'}]}));return;}
    let raw='';req.on('data',data=>raw+=data);req.on('end',()=>{requests.push(JSON.parse(raw));res.end(JSON.stringify({choices:[{message:{content:'СИНТЕТИЧЕСКИЙ ОТВЕТ: источник требует проверки. <script>window.injected=true</script>'}}]}));});
  });
  try{
    await new Promise(resolve=>model.listen(0,'127.0.0.1',resolve));
    child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:`http://127.0.0.1:${model.address().port}`,ENGINEER_OS_LOCAL_MODEL:'qwen3:8b',ENGINEER_OS_LOCAL_MODEL_KEY:''}});
    const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(new Error('Launcher startup timeout')),10000);child.stdout.on('data',data=>{log+=data;const found=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`Launcher exited ${code}`));});});
    browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1366,height:950}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#prompt').disabled);
    assert.equal(await page.locator('body').getAttribute('data-ui-mode'),'normal');
    assert.equal(await page.locator('#ui-mode-toggle').isVisible(),true);
    assert.equal(await page.locator('.workflow-bar a').count(),6);
    const unlabeled=await page.evaluate(()=>[...document.querySelectorAll('input:not([type="hidden"]),select,textarea')].filter(el=>!(el.labels&&el.labels.length)&&!el.getAttribute('aria-label')).map(el=>el.id||el.name||el.tagName));
    assert.deepEqual(unlabeled,[],'All form controls need labels or aria-labels');
    await page.locator('#ui-mode-toggle').click();
    assert.equal(await page.locator('body').getAttribute('data-ui-mode'),'advanced');
    await page.locator('#ui-mode-toggle').click();
    assert.equal(await page.locator('body').getAttribute('data-ui-mode'),'normal');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,'Desktop must not horizontally overflow');
    await page.screenshot({path:path.join(temp,'desktop.png'),fullPage:true});
    const first=await page.evaluate(()=>current);
    await page.setInputFiles('#upload',{name:'ТЗ.md',mimeType:'text/plain',buffer:Buffer.from('Высота по ТЗ 4 м')});
    await page.waitForSelector('.file');await page.waitForFunction(()=>!document.querySelector('#send').disabled);
    await page.fill('#prompt','Проверь высоту по ТЗ');await page.click('#send');
    await page.waitForSelector('.message.assistant');assert.equal(requests.length,1);assert.ok(JSON.stringify(requests[0]).includes('Высота по ТЗ 4 м'));
    assert.equal(await page.evaluate(()=>window.injected),undefined);
    await page.waitForFunction(()=>!document.querySelector('#send').disabled);
    assert.equal(await page.locator('nav .session').first().isEnabled(),true,'Conversation navigation must re-enable after send');
    await page.reload();await page.waitForSelector('.message.assistant');assert.equal(await page.locator('.file').count(),1);
    await page.click('#new-chat');await page.waitForFunction(first=>current!==first,first);
    await page.getByRole('button',{name:'Проверь высоту по ТЗ',exact:true}).click();await page.waitForSelector('.message.assistant');
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true,'Mobile must not horizontally overflow');
    assert.equal(await page.locator('.workflow-bar').isVisible(),true);
    await page.screenshot({path:path.join(temp,'mobile.png'),fullPage:true});
    assert.equal(errors.length,0,errors.join('\n'));
    if(process.env.ENGINEER_OS_UI_SCREENSHOT)fs.copyFileSync(path.join(temp,'mobile.png'),process.env.ENGINEER_OS_UI_SCREENSHOT);
    if(process.env.ENGINEER_OS_UI_SCREENSHOT_DIR){const dir=path.resolve(root,process.env.ENGINEER_OS_UI_SCREENSHOT_DIR);fs.mkdirSync(dir,{recursive:true});fs.copyFileSync(path.join(temp,'desktop.png'),path.join(dir,'local-cabinet-desktop.png'));fs.copyFileSync(path.join(temp,'mobile.png'),path.join(dir,'local-cabinet-mobile.png'));}
    console.log(JSON.stringify({result:'PASS',synthetic_model:true,real_ollama:false,checks:['launcher','worker','upload','source-context','chat','inert-model-markup','history-reload','session-switch','ui-mode-toggle','labeled-controls','desktop-layout','mobile-layout','no-horizontal-overflow','reference-screenshots'],requests:requests.length}));
  }finally{
    if(browser)await browser.close();if(child){child.kill('SIGINT');await new Promise(resolve=>{if(child.exitCode!==null)return resolve();const t=setTimeout(()=>{child.kill('SIGKILL');resolve();},2500);child.once('exit',()=>{clearTimeout(t);resolve();});});}
    await new Promise(resolve=>model.close(resolve));fs.rmSync(temp,{recursive:true,force:true});
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
