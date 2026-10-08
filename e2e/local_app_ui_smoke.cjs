/* Synthetic model protocol, actual launcher/worker, Chromium UI and persistence. */
const assert=require('node:assert/strict');
const fs=require('node:fs');const os=require('node:os');const path=require('node:path');
const http=require('node:http');const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
(async()=>{
  const root=path.resolve(__dirname,'..');const temp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-os-ui-'));
  const recoveryTemp=fs.mkdtempSync(path.join(os.tmpdir(),'engineer-os-recovery-ui-'));
  let child,recoveryChild,browser;const requests=[];
  async function stop(process){if(!process||process.exitCode!==null)return;process.kill('SIGINT');await new Promise(resolve=>{const timer=setTimeout(()=>{process.kill('SIGKILL');resolve();},2500);process.once('exit',()=>{clearTimeout(timer);resolve();});});}
  const model=http.createServer((req,res)=>{
    res.setHeader('Content-Type','application/json');
    if(req.method==='GET'){res.end(JSON.stringify({data:[{id:'qwen3:8b'}]}));return;}
    let raw='';req.on('data',data=>raw+=data);req.on('end',()=>{const payload=JSON.parse(raw);requests.push(payload);const send=()=>res.end(JSON.stringify({choices:[{message:{content:payload.messages[0].content.includes('Назначенная роль:')?JSON.stringify({status:'UNCERTAINTY',summary:'Предварительная роль',observations:[],limitations:['Нет фактических данных']}):'СИНТЕТИЧЕСКИЙ ОТВЕТ: источник требует проверки. <script>window.injected=true</script>'}}]}));if(JSON.stringify(payload).includes('CANCEL_UI'))setTimeout(send,2000);else send();});
  });
  try{
    await new Promise(resolve=>model.listen(0,'127.0.0.1',resolve));
    child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--data-dir',temp],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:`http://127.0.0.1:${model.address().port}`,ENGINEER_OS_LOCAL_MODEL:'qwen3:8b',ENGINEER_OS_LOCAL_MODEL_KEY:''}});
    const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(new Error('Launcher startup timeout')),10000);child.stdout.on('data',data=>{log+=data;const found=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`Launcher exited ${code}`));});});
    browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1366,height:950}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#prompt').disabled);
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
    await page.getByRole('button',{name:'Проверь высоту по ТЗ',exact:true}).click();await page.waitForFunction(first=>current===first,first);await page.waitForSelector('.file');await page.waitForSelector('.message.assistant');
    await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(temp,'mobile.png'),fullPage:true});
    assert.equal(errors.length,0,errors.join('\n'));
    if(process.env.ENGINEER_OS_UI_SCREENSHOT)fs.copyFileSync(path.join(temp,'mobile.png'),process.env.ENGINEER_OS_UI_SCREENSHOT);
    await page.locator('.model-panel summary').click();await page.waitForFunction(()=>modelFormLoaded);
    await page.fill('#model-setting-TIMEOUT','12');await page.click('#model-settings-form button');
    await page.waitForFunction(()=>document.querySelector('.model-panel p').textContent.includes('сохранены и применены'));
    assert.equal(JSON.parse(fs.readFileSync(path.join(temp,'settings.json'),'utf8')).ENGINEER_OS_LOCAL_MODEL_TIMEOUT,'12');
    await page.getByRole('button',{name:'Проверить реальный ответ',exact:true}).click();
    await page.waitForFunction(first=>current!==first,first,{timeout:5000});
    await page.waitForSelector('.message.assistant');assert.equal(await page.locator('.file').count(),0);
    assert.equal(requests.length,2);assert.equal(requests[1].messages.filter(m=>m.role==='user').length,1,'Diagnostic must not transmit prior project history');
    await page.getByRole('button',{name:'Проверь высоту по ТЗ',exact:true}).click();await page.waitForFunction(first=>current===first,first);await page.waitForSelector('.file');await page.waitForSelector('.message.assistant');
    await page.evaluate(async()=>{await api(`/api/sessions/${current}/jobs`,{method:'POST',body:{prompt:'CANCEL_UI',file_ids:[],mode:'CHAT'}});await refresh();});
    await page.waitForSelector('.job.running');await page.locator('.task-cancel').first().click();
    await page.waitForSelector('.job.cancelled');assert.equal(await page.locator('.message.assistant').count(),1,'Cancelled late reply must not enter history');
    await page.locator('.task-retry').first().click();
    await page.waitForFunction(()=>document.querySelectorAll('.message.assistant').length===2);
    assert.equal(requests.length,4,'Retry must execute a new request');
    await page.click('[data-stage="history"]');await page.waitForSelector('#history-records .history-record');
    assert.ok(await page.locator('#history-records').textContent().then(text=>text.includes('Проверь высоту по ТЗ')));
    const torCandidate=await page.evaluate(async()=>{
      const snap=await api(`/api/sessions/${current}`);
      const candidate=await api(`/api/sessions/${current}/evidence`,{method:'POST',body:{file_id:snap.files[0].id,quote:'Высота по ТЗ 4 м',statement:'Исходная цитата ТЗ'}});
      await api(`/api/sessions/${current}/evidence/${candidate.id}/reviews`,{method:'POST',body:{expected_revision:0,decision:'SOURCE_CONFIRMED',note:'Точная цитата TXT',actor:'Browser source reviewer'}});await refresh();return candidate.id;
    });
    await page.locator('#tz-form').evaluate(form=>form.closest('details').open=true);
    await page.fill('#tz-text','Проверить высоту\nПроверить фактические конструкции');
    await page.selectOption('#tz-sources',torCandidate);await page.click('#tz-save');
    await page.waitForFunction(()=>document.querySelectorAll('.requirement-card').length===2&&!document.querySelector('#tz-save').disabled);
    assert.ok(await page.locator('#tz-status').textContent().then(t=>t.includes('SOURCE_REVIEWED')));
    const requirement=page.locator('.requirement-card').first();
    await requirement.locator('.requirement-conclusion').fill('ТЗ задаёт высоту; фактическое значение не подтверждено');
    await requirement.locator('.requirement-actor').fill('Browser assessment reviewer');
    await requirement.locator('input[type=checkbox]').check();await requirement.locator('.requirement-save').click();
    await page.waitForFunction(()=>document.querySelector('.requirement-card').textContent.includes('Browser assessment reviewer')&&!document.querySelector('#tz-save').disabled);
    await page.evaluate(async()=>{
      const snap=await api(`/api/sessions/${current}`);
      await api(`/api/sessions/${current}/jobs`,{method:'POST',body:{prompt:'Сверить ТЗ',file_ids:snap.files.map(f=>f.id),mode:'CORE_RUN',requested_checks:['report','normative']}});
    });
    await page.waitForFunction(()=>document.querySelector('.core-run')?.textContent.includes('Черновик сохранён')&&!document.querySelector('#send').disabled);
    assert.ok(await page.locator('.engineering-review').textContent().then(t=>t.includes('BLOCK')));
    assert.equal(await page.locator('.engineering-requirement').count(),2);
    assert.ok(await page.locator('.specialist-checks').textContent().then(t=>t.includes('BLOCK')));
    const requestsBeforeRecovery=requests.length;
    const reviewDigest=await page.locator('.engineering-review').textContent();
    await page.reload();await page.getByRole('button',{name:'Проверь высоту по ТЗ',exact:true}).click();await page.waitForFunction(first=>current===first,first);await page.waitForSelector('.engineering-review',{state:'attached'});
    assert.equal(await page.locator('.engineering-review').textContent(),reviewDigest);
    assert.equal(errors.length,0,errors.join('\n'));
    const selection=path.join(recoveryTemp,'active-data-dir.txt'),archive=path.join(recoveryTemp,'project.zip'),restored=path.join(recoveryTemp,'восстановленный проект');
    recoveryChild=spawn(process.env.PYTHON||'python3',['scripts/run_data_recovery.py','--no-browser','--data-dir',temp,'--selection-file',selection],{cwd:root});
    const recoveryOrigin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Recovery startup timeout')),10000);recoveryChild.stdout.on('data',data=>{log+=data;const found=log.match(/ENGINEER OS recovery: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});recoveryChild.on('exit',code=>{clearTimeout(timer);reject(Error('Recovery exited '+code));});});
    const recoveryPage=await browser.newPage();await recoveryPage.goto(recoveryOrigin);await recoveryPage.waitForFunction(()=>!document.querySelector('#backup-create').disabled);
    await recoveryPage.fill('#archive-path',archive);await recoveryPage.click('#backup-create');
    await recoveryPage.waitForFunction(()=>document.querySelector('#recovery-error').textContent.includes('already using'));
    assert.equal(fs.existsSync(archive),false,'Active application must retain its exclusive data lock');
    await stop(child);child=null;
    await recoveryPage.click('#backup-create');await recoveryPage.waitForFunction(()=>document.querySelector('#recovery-result').textContent.includes('Копия создана'));
    await recoveryPage.click('#backup-verify');await recoveryPage.waitForFunction(()=>document.querySelector('#recovery-result').textContent.includes('Целостность архива проверена'));
    await recoveryPage.fill('#restore-target',restored);await recoveryPage.click('#backup-restore');await recoveryPage.waitForFunction(()=>document.querySelector('#recovery-result').textContent.includes('Проект восстановлен'));
    await recoveryPage.click('#activate-project');await recoveryPage.waitForFunction(()=>document.querySelector('#recovery-result').textContent.includes('Каталог выбран'));
    assert.equal(fs.readFileSync(selection,'utf8').trim(),restored);
    await recoveryPage.click('#backup-restore');await recoveryPage.waitForFunction(()=>!document.querySelector('#recovery-error').hidden);
    assert.ok(await recoveryPage.locator('#recovery-error').textContent().then(text=>text.includes('existing')||text.includes('new')),'Existing restore target must be refused');
    const originalFiles=fs.readdirSync(path.join(temp,'files')),restoredFiles=fs.readdirSync(path.join(restored,'files'));assert.deepEqual(restoredFiles,originalFiles);for(const name of originalFiles)assert.deepEqual(fs.readFileSync(path.join(restored,'files',name)),fs.readFileSync(path.join(temp,'files',name)));
    child=spawn(process.env.PYTHON||'python3',['scripts/run_local_app.py','--no-browser','--port','0','--selection-file',selection],{cwd:root,env:{...process.env,ENGINEER_OS_LOCAL_MODEL_URL:`http://127.0.0.1:${model.address().port}`,ENGINEER_OS_LOCAL_MODEL:'qwen3:8b',ENGINEER_OS_LOCAL_MODEL_KEY:''}});
    const restoredOrigin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Restored startup timeout')),10000);child.stdout.on('data',data=>{log+=data;const found=log.match(/ENGINEER OS: (http:\/\/127\.0\.0\.1:\d+)/);if(found){clearTimeout(timer);resolve(found[1]);}});child.on('exit',code=>{clearTimeout(timer);reject(Error('Restored exited '+code));});});
    await page.goto(restoredOrigin);await page.getByRole('button',{name:'Проверь высоту по ТЗ',exact:true}).click();await page.waitForFunction(first=>current===first,first);await page.waitForSelector('.file');await page.waitForSelector('.message.assistant');assert.equal(await page.locator('.file').count(),1);assert.equal(requests.length,requestsBeforeRecovery,'Recovery must not rerun completed work');
    console.log(JSON.stringify({result:'PASS',synthetic_model:true,real_ollama:false,checks:['launcher','worker','upload','source-context','chat','inert-model-markup','history-reload','session-switch','mobile-layout','model-settings-ui','isolated-diagnostic-ui','running-cancel-ui','late-answer-refusal','retry-new-task-ui','archive-navigation','recovery-browser','busy-owner-refusal','backup-verify-restore','no-replace','original-bytes','activate-directory','restored-launch-history'],requests:requests.length}));
  }finally{
    if(browser)await browser.close();await stop(child);await stop(recoveryChild);
    await new Promise(resolve=>model.close(resolve));fs.rmSync(temp,{recursive:true,force:true});fs.rmSync(recoveryTemp,{recursive:true,force:true});
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
