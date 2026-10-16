'use strict';
/* Supplied SPU window/tray shell, adapted to ENGINEER OS owned backend. */

const { app, BrowserWindow, Tray, Menu, shell, dialog, nativeImage, screen, ipcMain, Notification } =
  require('electron');
const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');
const {startBackend,allowedExternal,trustedSender}=require('./server-owner.cjs');
app.setName('ENGINEER OS SPU');
if(argValue('--state-dir')) { fs.mkdirSync(path.resolve(argValue('--state-dir')),{recursive:true}); app.setPath('userData',path.resolve(argValue('--state-dir'))); }

const SELF_TEST = process.argv.includes('--self-test');
let activePort=null,APP_URL='';

const CONFIG_PATH = () => path.join(app.getPath('userData'), 'desktop-config.json');
const STATE_PATH = () => path.join(app.getPath('userData'), 'window-state.json');
const SERVER_LOG_PATH = () => path.join(app.getPath('userData'), 'platform-server.log');
const SELF_TEST_RESULT_PATH = () => path.join(app.getPath('userData'), 'self-test-result.json');

function readJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { return fallback; }
}
function writeJson(file, data) {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
  } catch (e) { /* состояние не критично — молча продолжаем */ }
}
function config() { return readJson(CONFIG_PATH(), {}); }
function patchConfig(patch) { writeJson(CONFIG_PATH(), Object.assign(config(), patch)); }

// ---------- поиск платформы и питона ----------
function looksLikePlatform(dir) {
  return !!dir && fs.existsSync(path.join(dir, 'scripts','run_local_app.py')) && fs.existsSync(path.join(dir, 'engineering','local_app'));
}

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : null;
}

function findPlatformDir() {
 return [argValue('--project-dir'),process.env.ENGINEER_OS_PROJECT_DIR,path.resolve(__dirname,'..'),config().projectDir].filter(Boolean).find(looksLikePlatform)||null;
}

async function askPlatformDir() {
  const res = await dialog.showOpenDialog({
    title: 'Где лежит ENGINEER OS?',
    message: 'Укажите папку, в которой находятся scripts/run_local_app.py и engineering/local_app',
    properties: ['openDirectory'],
    buttonLabel: 'Выбрать эту папку'
  });
  if (res.canceled || !res.filePaths.length) return null;
  const dir = res.filePaths[0];
  if (!looksLikePlatform(dir)) {
    dialog.showErrorBox('Это не папка платформы',
      'В выбранной папке нет scripts/run_local_app.py или engineering/local_app.\nВыбрано: ' + dir);
    return null;
  }
  patchConfig({ projectDir: dir });
  return dir;
}

// Встроенный Python из установщика: resources/python или desktop/build/python в разработке.
function bundledPython() {
  const candidates = [
    process.resourcesPath && path.join(process.resourcesPath, 'python', 'python.exe'),
    path.join(__dirname, 'build', 'python', 'python.exe')
  ].filter(Boolean);
  return candidates.find((p) => fs.existsSync(p)) || null;
}

// Поиск запускает процессы, поэтому помним результат: спрашиваем и из настроек, и из самопроверки.
let pythonCache = null;

function findPythonInfo() {
  if (pythonCache) return pythonCache;
  const explicit = argValue('--python') || process.env.ENGINEER_OS_PYTHON || path.join(projectDir,'.venv-engineering','Scripts','python.exe');
  const bundled = bundledPython();
  // если пользователь сам указал встроенный интерпретатор — он всё равно встроенный
  const explicitIsBundled = !!(explicit && bundled && path.resolve(explicit) === path.resolve(bundled));
  const candidates = [
    explicit && { cmd: explicit, embedded: explicitIsBundled,
                  src: explicitIsBundled ? 'встроенный в приложение' : 'путь из настроек' },
    bundled && { cmd: bundled, embedded: true, src: 'встроенный в приложение' },
    { cmd: 'python', embedded: false, src: 'системный Python' },
    { cmd: 'python3', embedded: false, src: 'системный Python' },
    { cmd: 'py', embedded: false, src: 'системный Python' }
  ].filter(Boolean);
  for (const c of candidates) {
    try {
      const r = spawnSync(c.cmd, ['-V'], { encoding: 'utf8', windowsHide: true, timeout: 10000 });
      if (r.status === 0) { pythonCache = c; return pythonCache; }
    } catch (e) { /* пробуем следующий */ }
  }
  pythonCache = { cmd: null, src: 'не найден' };
  return pythonCache;
}

function findPython() { return findPythonInfo().cmd; }

// ---------- сервер платформы ----------
let serverProc = null;
let serverOwned = false;         // true — сервер подняли мы и должны его остановить
let serverOutput = [];           // хвост журнала сервера для сообщений об ошибках
let projectDir = null;

function appendServerLog(chunk) {
  const text = chunk.toString('utf8');
  serverOutput.push(text);
  if (serverOutput.length > 400) serverOutput = serverOutput.slice(-200);
  try { fs.appendFileSync(SERVER_LOG_PATH(), text, 'utf8'); } catch (e) { /* не критично */ }
}

let backendOwner=null,startup=null,startupController=null;
async function ensureServer(onTick) {
 try {
  if(onTick)onTick('Запускаю ядро ENGINEER OS…');
  if(quitting)throw Error('Application is quitting');
  if(startup)throw Error('Backend startup already pending');
  startupController=new AbortController();
  startup=startBackend({signal:startupController.signal,python:findPython(),root:projectDir,dataDir:argValue('--data-dir'),selectionFile:argValue('--selection-file'),onOutput:appendServerLog});
  try{backendOwner=await startup;}finally{startup=null;startupController=null;}
  if(quitting)return {ok:false,error:'Application is quitting'};
  serverProc=backendOwner.child;serverOwned=true;APP_URL=backendOwner.origin+'/';activePort=Number(new URL(APP_URL).port);
  serverProc.once('exit',()=>{if(serverOwned&&!quitting)showStartupFailure('Процесс ядра завершился. Откройте журнал сервера.');});
  return {ok:true,owned:true,port:activePort,build:backendOwner.record.build};
 } catch(error) { return {ok:false,error:String(error.message||error)}; }
}

function serverTail(limit) {
  const text = serverOutput.join('');
  return text.length > limit ? text.slice(-limit) : text;
}

let stopping=null;
async function stopOwnedServer() {
 if(stopping)return stopping;
 stopping=(async()=>{
  startupController?.abort();
  if(startup){try{await startup;}catch{}}
  const owner=backendOwner;backendOwner=null;serverOwned=false;serverProc=null;
  if(owner)await owner.stop();
 })();
 try{await stopping;}finally{stopping=null;}
}

let restarting=false;
async function restartServer() {
  if(restarting||quitting)return;restarting=true;
  try{
  await stopOwnedServer();
  serverOutput = [];
  if (win && !win.isDestroyed()) loadSplash('Перезапускаю сервер платформы…');
  const res = await ensureServer(setSplashStatus);
  if (res.ok && win && !win.isDestroyed()) win.loadURL(APP_URL);
  else if (win && !win.isDestroyed()) showStartupFailure(res.error);
  }finally{restarting=false;}
}

// ---------- окно ----------
let win = null;
let tray = null;
let quitting = false;
app.isQuitting = false;

function defaultBounds() {
  const area = screen.getPrimaryDisplay().workAreaSize;
  const width = Math.min(1480, Math.max(1024, Math.round(area.width * 0.82)));
  const height = Math.min(940, Math.max(660, Math.round(area.height * 0.86)));
  return { width, height };
}

// сохранённая геометрия годится только если окно реально попадает на какой-то экран
function visibleOnSomeDisplay(b) {
  if (!b || !b.width || !b.height) return false;
  return screen.getAllDisplays().some((d) => {
    const a = d.workArea;
    const interW = Math.min(b.x + b.width, a.x + a.width) - Math.max(b.x, a.x);
    const interH = Math.min(b.y + b.height, a.y + a.height) - Math.max(b.y, a.y);
    return interW > 120 && interH > 80;
  });
}

function loadWindowState() {
  const saved = readJson(STATE_PATH(), {});
  const bounds = visibleOnSomeDisplay(saved) ? saved : Object.assign(defaultBounds(), { x: undefined, y: undefined });
  return { bounds, maximized: !!saved.maximized };
}

let stateSaveTimer = null;
function saveWindowState() {
  if (!win || win.isDestroyed()) return;
  const b = win.getNormalBounds ? win.getNormalBounds() : win.getBounds();
  writeJson(STATE_PATH(), Object.assign({}, b, { maximized: win.isMaximized() }));
}

function trackWindowState() {
  const schedule = () => {
    clearTimeout(stateSaveTimer);
    stateSaveTimer = setTimeout(saveWindowState, 500);
  };
  win.on('resize', schedule);
  win.on('move', schedule);
  win.on('maximize', schedule);
  win.on('unmaximize', schedule);
}

function iconImage() {
  const p = path.join(__dirname, 'build', 'icon.png');
  return fs.existsSync(p) ? nativeImage.createFromPath(p) : nativeImage.createEmpty();
}

// в трее лучше отдельный маленький значок: без пересжатия большая иконка мутнеет
function trayImage() {
  const p = path.join(__dirname, 'build', 'tray.png');
  if (fs.existsSync(p)) return nativeImage.createFromPath(p);
  return iconImage().resize({ width: 16, height: 16 });
}

function loadSplash(status) {
  if (!win || win.isDestroyed()) return;
  win.loadFile(path.join(__dirname, 'splash.html'));
  win.webContents.once('did-finish-load', () => setSplashStatus(status));
}

function setSplashStatus(text) {
  if (!win || win.isDestroyed() || !text) return;
  win.webContents.executeJavaScript(
    'window.setStatus && window.setStatus(' + JSON.stringify(text) + ')'
  ).catch(() => {});
}

function showStartupFailure(reason) {
  if (!win || win.isDestroyed()) return;
  const tail = serverTail(2500);
  win.webContents.executeJavaScript(
    'window.setStatus && window.setStatus(' + JSON.stringify('Не удалось запустить сервер: ' + (reason || '') + '\n\n' + tail) + ', true)'
  ).catch(() => {});
}

function createWindow() {
  const st = loadWindowState();
  win = new BrowserWindow({
    x: st.bounds.x,
    y: st.bounds.y,
    width: st.bounds.width,
    height: st.bounds.height,
    minWidth: 980,
    minHeight: 620,
    show: false,
    title: 'ENGINEER OS · СПУ',
    backgroundColor: '#0a0a0c',
    autoHideMenuBar: true,
    icon: iconImage(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      spellcheck: false
    }
  });

  win.removeMenu();
  if (st.maximized) win.maximize();
  trackWindowState();

  // Заголовок окна всегда наш: интерфейс платформы не должен представляться чужим
  // продуктом, даже если на порту случайно ответит другая страница.
  win.webContents.on('page-title-updated', (event) => {
    event.preventDefault();
    win.setTitle('ENGINEER OS · СПУ');
  });

  win.once('ready-to-show', () => {if(!SELF_TEST)win.show();});

  win.webContents.setWindowOpenHandler(({url})=>{
    if(allowedExternal(url))shell.openExternal(url);
    return {action:'deny'};
  });
  win.webContents.on('will-navigate',(event,url)=>{
    let own=false;try{own=!!backendOwner&&new URL(url).origin===backendOwner.origin;}catch{}
    if(!own){event.preventDefault();if(allowedExternal(url))shell.openExternal(url);}
  });
  win.webContents.session.setPermissionRequestHandler((_contents,_permission,callback)=>callback(false));
  win.webContents.session.on('will-download',(event,item)=>{
    let own=false;try{own=!!backendOwner&&new URL(item.getURL()).origin===backendOwner.origin;}catch{}
    if(!own)event.preventDefault();
  });

  // горячие клавиши локального инструмента
  win.webContents.on('before-input-event', (event, input) => {
    if (input.type !== 'keyDown') return;
    const key = (input.key || '').toLowerCase();
    if (key === 'f12' || (input.control && input.shift && key === 'i')) {
      win.webContents.toggleDevTools();
      event.preventDefault();
    } else if (key === 'f5' || (input.control && key === 'r')) {
      win.webContents.reload();
      event.preventDefault();
    }
  });

  win.webContents.on('did-fail-load', (e, code, desc, url) => {
    if (SELF_TEST) return;
    showStartupFailure(`страница ${url} не загрузилась (${code} ${desc})`);
  });

  // закрытие окна — сворачивание в трей (выключить можно в меню трея)
  win.on('close', (event) => {
    if (quitting || config().closeToTray === false) return;
    event.preventDefault();
    win.hide();
    notifyTrayOnce();
  });

  loadSplash('Запускаю сервер платформы…');
  return win;
}

let trayNoticeShown = false;
function notifyTrayOnce() {
  if (trayNoticeShown) return;
  trayNoticeShown = true;
  try {
    if (Notification.isSupported()) {
      new Notification({
        title: 'ENGINEER OS · СПУ работает',
        body: 'Окно свёрнуто в трей. Значок рядом с часами, двойной щелчок — вернуть окно.',
        icon: iconImage()
      }).show();
    }
  } catch (e) { /* уведомления не критичны */ }
}

function toggleWindow() {
  if (!win || win.isDestroyed()) return;
  if (win.isVisible() && !win.isMinimized()) { win.hide(); return; }
  win.show();
  if (win.isMinimized()) win.restore();
  win.focus();
}

function createTray() {
  const img = trayImage();
  tray = new Tray(img.isEmpty() ? iconImage() : img);
  tray.setToolTip('ENGINEER OS · СПУ');
  tray.on('double-click', toggleWindow);
  tray.on('click', toggleWindow);
  refreshTrayMenu();
}

function refreshTrayMenu() {
  if (!tray) return;
  const closeToTray = config().closeToTray !== false;
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Открыть платформу', click: toggleWindow },
    { label: 'Открыть в браузере', click: () => shell.openExternal(APP_URL) },
    { type: 'separator' },
    { label: 'Перезапустить сервер платформы', click: () => restartServer() },
    { label: 'Открыть журнал сервера', click: () => shell.openPath(SERVER_LOG_PATH()) },
    { label: 'Открыть папку платформы', click: () => shell.openPath(projectDir) },
    {
      // если папка платформы переехала или появилась своя — переключаемся на неё
      label: 'Выбрать папку платформы…',
      click: async () => {
        const dir = await askPlatformDir();
        if (!dir) return;
        projectDir = dir;
        pythonCache = null;
        restartServer();
      }
    },
    { type: 'separator' },
    {
      label: 'Закрывать окно в трей',
      type: 'checkbox',
      checked: closeToTray,
      click: (item) => { patchConfig({ closeToTray: item.checked }); refreshTrayMenu(); }
    },
    { type: 'separator' },
    { label: 'Выход', click: () => { quitting = true; app.quit(); } }
  ]));
}

// ---------- самопроверка ----------
async function runSelfTest() {
 const report={ok:false,startedAt:new Date().toISOString(),notes:[]};
 try {
  if(!argValue('--data-dir')||!argValue('--state-dir'))throw Error('Self-test requires isolated --data-dir and --state-dir');
  createWindow();const ready=await ensureServer();if(!ready.ok)throw Error(ready.error);
  report.origin=backendOwner.origin;report.build=ready.build;
  await win.loadURL(APP_URL);
  const deadline=Date.now()+30000;
  while(Date.now()<deadline){
   report.window=await win.webContents.executeJavaScript(`(async()=>({shell:!!document.querySelector('#spu-workspace-shell'),forms:document.querySelectorAll('form').length,workspace:typeof spuWorkspaceState!=='undefined'&&spuWorkspaceState?.snapshot?.session?.id===current,sessions:typeof spuSessionState!=='undefined'&&Array.isArray(spuSessionState)?spuSessionState.length:-1,bridge:await window.engineerDesktop.info(),node:typeof require}))()`);
   if(report.window.shell&&report.window.workspace&&report.window.sessions>=0)break;
   await new Promise(resolve=>setTimeout(resolve,200));
  }
  report.icon=!iconImage().isEmpty();saveWindowState();report.windowState=fs.existsSync(STATE_PATH());
  fs.writeFileSync(path.join(app.getPath('userData'),'desktop-self-test.png'),(await win.webContents.capturePage()).toPNG());
  report.ok=report.window.shell&&report.window.workspace&&report.window.forms>5&&report.window.node==='undefined'&&report.window.bridge.serverOwned&&report.icon&&report.windowState;
 }catch(error){report.notes.push(String(error.stack||error));}
 finally{if(win&&!win.isDestroyed())win.destroy();await stopOwnedServer();}
 if(report.origin){try{await fetch(report.origin,{signal:AbortSignal.timeout(1000)});report.backendStopped=false;}catch{report.backendStopped=true;}report.ok=report.ok&&report.backendStopped;}
 report.finishedAt=new Date().toISOString();writeJson(SELF_TEST_RESULT_PATH(),report);
 process.stdout.write('SELF_TEST_RESULT '+JSON.stringify(report)+'\n');app.exit(report.ok?0:1);
}

// ---------- жизненный цикл ----------
const gotLock = SELF_TEST ? true : app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (win) { if (win.isMinimized()) win.restore(); win.show(); win.focus(); }
  });

  let shutdownDone=false;
  app.on('before-quit', event => { quitting=true;app.isQuitting=true;if(!shutdownDone){event.preventDefault();saveWindowState();stopOwnedServer().catch(error=>appendServerLog(String(error))).finally(()=>{shutdownDone=true;app.quit();});} });

  app.on('window-all-closed', () => {
    // приложение живёт в трее: не выходим по закрытию окна
    if (process.platform !== 'darwin' && config().closeToTray === false) { quitting = true; app.quit(); }
  });



  app.whenReady().then(async () => {
    projectDir = findPlatformDir();
    while (!projectDir) {
      projectDir = await askPlatformDir();
      if (!projectDir) {
        const r = await dialog.showMessageBox({
          type: 'warning',
          title: 'ENGINEER OS · СПУ',
          message: 'Без папки платформы приложение работать не может.',
          buttons: ['Выбрать папку ещё раз', 'Выход'],
          defaultId: 0,
          cancelId: 1
        });
        if (r.response === 1) { app.quit(); return; }
      }
    }
    if (SELF_TEST) { await runSelfTest(); return; }

    createWindow();
    createTray();
    const res = await ensureServer(setSplashStatus);
    if (res.ok && !quitting && win && !win.isDestroyed()) {
      win.loadURL(APP_URL);
    } else {
      showStartupFailure(res.error);
    }
  });

  function ipc(name,handler){ipcMain.handle('engineer:'+name,(event,...args)=>{
   if(!backendOwner||!win||!trustedSender(event,win.webContents,backendOwner.origin))throw Error('Untrusted desktop caller');
   return handler(...args);
  });}
  ipc('info',()=>({appVersion:app.getVersion(),electron:process.versions.electron,serverOwned,platformUrl:APP_URL}));
  ipc('openProjectFolder',()=>shell.openPath(projectDir));
  ipc('openServerLog',()=>shell.openPath(SERVER_LOG_PATH()));
  ipc('hideWindow',()=>win.hide());
}
