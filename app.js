const SUPABASE_URL = "https://jaikhckrwblrkhoizikn.supabase.co";
const SUPABASE_KEY = "sb_publishable_T8KMHBiql8I6TmUVwX4FXA_1pWvBOQd";
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

const state = { page:"dashboard", projects:[], projectId:null, session:null };
const $ = (s) => document.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function toast(msg){const el=$("#toast");el.textContent=msg;el.hidden=false;setTimeout(()=>el.hidden=true,3200)}
function statusClass(s){return /PASS|READY|COMPLETED|ACTIVE|RUNNING/i.test(s||"")?"ok":/ERROR|BLOCK|FAILED/i.test(s||"")?"bad":"warn"}
function fmtDate(v){return v?new Date(v).toLocaleString("ru-RU"):"—"}

async function db(table, query={}) {
  let q=supabase.from(table).select(query.select||"*");
  if(query.projectId) q=q.eq("project_id",query.projectId);
  if(query.order) q=q.order(query.order,{ascending:false});
  if(query.limit) q=q.limit(query.limit);
  const {data,error}=await q;
  if(error) throw error;
  return data||[];
}

async function loadProjects(){
  if(!state.session){ state.projects=[]; state.projectId=null; return; }
  const {data,error}=await supabase.from("projects").select("id,name,status,updated_at").order("updated_at",{ascending:false});
  if(error){$("#connectionDot").className="dot bad";$("#connectionText").textContent="Ошибка БД";throw error}
  state.projects=data||[];
  const sel=$("#projectSelect");
  sel.innerHTML='<option value="">Выберите проект</option>'+state.projects.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join("");
  if(state.projectId && state.projects.some(p=>p.id===state.projectId)) sel.value=state.projectId;
  else if(state.projects[0]){state.projectId=state.projects[0].id;sel.value=state.projectId}
  else state.projectId=null;
  $("#connectionDot").className="dot ok";$("#connectionText").textContent="Supabase подключён";
}

async function counts(){
  const p=state.projectId;if(!p)return {};
  const names=["documents","evidence","engineering_findings","engineering_tasks","engineering_measurements","structural_elements","technical_assignment_items"];
  const out={};
  for(const n of names){try{out[n]=(await db(n,{projectId:p,select:"id",limit:1000})).length}catch{out[n]=0}}
  return out;
}

const pageNames={dashboard:"Обзор",case:"Инженерный кейс",documents:"Документы",tasks:"Задачи",agents:"Агенты",calculations:"Расчёты",audit:"Аудит",pipeline:"Pipeline / v28 Recovery"};

async function render(){
  $("#pageTitle").textContent=pageNames[state.page];
  document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.page===state.page));
  if(state.page==="dashboard") return renderDashboard();
  if(state.page==="case") return renderCase();
  if(state.page==="documents") return renderTablePage("documents","Документы","name,document_type,status,processing_status,created_at");
  if(state.page==="tasks") return renderTasks();
  if(state.page==="agents") return renderAgents();
  if(state.page==="calculations") return renderTablePage("calculations","Расчёты","id,status,calculation_type,created_at");
  if(state.page==="audit") return renderAudit();
  if(state.page==="pipeline") return renderPipeline();
}

async function renderDashboard(){
  if(!state.projectId){
    $("#page").innerHTML=`<div class="grid two"><div class="card"><div class="eyebrow">PROJECT / CASE</div><h2>Нет доступного проекта</h2><p class="label">Создайте проект через штатный RPC Supabase. Frontend не создаёт project_members напрямую.</p><button id="createProjectBtn" class="btn primary">Создать проект</button></div><div class="card"><div class="eyebrow">CURRENT BACKEND</div><div class="metric" style="font-size:18px">v29 pipeline isolation</div><div class="label">В БД уже присутствуют v27 Result Validation & Handoff и v28 Autonomous Recovery.</div></div></div>`;
    $("#createProjectBtn")?.addEventListener("click",createProject);return;
  }
  const c=await counts();
  let latest=[];try{latest=await db("orchestration_runs",{projectId:state.projectId,select:"id,status,current_stage,progress,updated_at,last_error",order:"updated_at",limit:5})}catch{}
  $("#page").innerHTML=`
    <div class="grid cards">${[['Документы',c.documents],['Доказательства',c.evidence],['Находки',c.engineering_findings],['Задачи',c.engineering_tasks],['ТЗ / требования',c.technical_assignment_items]].slice(0,4).map(x=>`<div class="card"><div class="label">${x[0]}</div><div class="metric">${x[1]}</div><div class="label">текущий проект</div></div>`).join("")}</div>
    <div class="section-title"><h2>Сквозной pipeline</h2><div style="display:flex;gap:8px;flex-wrap:wrap"><button id="launchEngineeringBtn" class="btn primary">Запустить ENGINEER OS</button><button id="pipelineBtn" class="btn secondary">Открыть pipeline</button></div></div><div id="launchResult" class="card" style="display:none;margin-bottom:14px"></div>
    <div class="pipeline">${["AUTH","PROJECT","ТЗ","DOCUMENT","EVIDENCE","TASK","ORCHESTRATOR","QUEUE","WORKER","AGENT","RESULT","VALIDATION","HANDOFF","RECOVERY","FINAL"].map(x=>`<div class="stage"><b>${x}</b><span>контур</span></div>`).join("")}</div>
    <div class="section-title"><h2>Последние orchestration runs</h2></div>
    ${latest.length?table(latest,[["status","Статус"],["current_stage","Этап"],["progress","Прогресс %"],["updated_at","Обновлён"],["last_error","Последняя ошибка"]]):'<div class="card empty">Запусков ещё нет.</div>'}
    <div class="section-title"><h2>Инженерное правило</h2></div>
    <div class="grid two"><div class="card"><div class="label">VALIDATION FIRST</div><div class="metric" style="font-size:18px">Доказательство → проверка → handoff</div><div class="label">Неподтверждённое не становится инженерным фактом.</div></div><div class="card"><div class="label">RECOVERY</div><div class="metric" style="font-size:18px">v28 Autonomous Recovery</div><div class="label">Stale worker lease восстанавливается до исчерпания попыток.</div></div></div>`;
  $("#pipelineBtn").addEventListener("click",()=>{state.page="pipeline";render().catch(e=>toast(e.message))});
  $("#launchEngineeringBtn").addEventListener("click",launchEngineeringRun);
}

\nasync function launchEngineeringRun(){\n  if(!state.projectId){toast("Сначала выберите проект");return;}\n  const docs=await db("documents",{projectId:state.projectId,select:"id,name,document_type,status,processing_status",order:"created_at",limit:100});\n  if(docs.length<2){toast("Нужно минимум два обработанных документа: отчёт и ТЗ");return;}\n  const sourceOptions=docs.map((d,i)=>`${i+1}. ${d.name} [${d.id}]`).join("\\n");\n  const sourceInput=prompt("Введите номер или ID исходного отчёта/документа:\\n\\n"+sourceOptions, "1");\n  if(!sourceInput)return;\n  const source=docs[Number(sourceInput)-1]||docs.find(d=>d.id===sourceInput.trim());\n  if(!source){toast("Исходный документ не найден");return;}\n  const tzInput=prompt("Введите номер или ID документа ТЗ:\\n\\n"+sourceOptions, docs.findIndex(d=>/ТЗ|техническ|assignment/i.test(d.name+" "+(d.document_type||"")))+1||"2");\n  if(!tzInput)return;\n  const tz=docs[Number(tzInput)-1]||docs.find(d=>d.id===tzInput.trim());\n  if(!tz){toast("Документ ТЗ не найден");return;}\n  const objective=prompt("Цель проверки (необязательно):","Провести инженерную проверку отчёта по ТЗ с доказательной базой и FINAL_AUDIT.")||"";\n  const box=$("#launchResult");box.style.display="block";box.innerHTML='<div class="label">Запуск ENGINEER OS…</div>';\n  try{\n    const {data,error}=await supabase.functions.invoke("pipeline-launch-v1",{body:{project_id:state.projectId,document_id:source.id,technical_assignment_document_id:tz.id,title:"Инженерное обследование / аудит отчёта",objective}});\n    if(error)throw error;\n    box.innerHTML=`<div class="eyebrow">ENGINEER OS / LAUNCH</div><h3 style="margin:6px 0">${esc(data?.status||"UNKNOWN")}</h3><div class="label">Task ID: <span class="mono">${esc(data?.task_id||"—")}</span></div><div class="label">Analysis Run: <span class="mono">${esc(data?.analysis_run_id||"—")}</span></div><div class="label" style="margin-top:8px">Оркестратор и очередь получили задачу. Следите за этапами в Pipeline.</div>`;\n    toast("ENGINEER OS запущен");\n  }catch(e){box.innerHTML=`<div class="status BLOCK">BLOCK</div><div style="margin-top:8px">${esc(e.message)}</div>`;toast("Запуск заблокирован: "+e.message);}\n}\n\nasync function renderCase(){
  const p=state.projectId;
  const [els,locs,meas,finds]=await Promise.all([
    db("structural_elements",{projectId:p,select:"id,name,element_type,material,location"}),
    db("engineering_locations",{projectId:p,select:"id,name,description"}),
    db("engineering_measurements",{projectId:p,select:"id,parameter,value,unit,location_id"}),
    db("engineering_findings",{projectId:p,select:"id,title,finding_type,status,severity"})
  ]);
  $("#page").innerHTML=`<div class="notice">Инженерный кейс подключён к реальным таблицам Supabase. Пока нет данных — интерфейс показывает пустое состояние, а не выдуманные результаты.</div>
  <div class="section-title"><h2>Конструкции</h2><span class="label">${els.length}</span></div>${table(els,[["name","Наименование"],["element_type","Тип"],["material","Материал"],["location","Расположение"]])}
  <div class="section-title"><h2>Измерения</h2><span class="label">${meas.length}</span></div>${table(meas,[["parameter","Параметр"],["value","Значение"],["unit","Ед."],["location_id","Location ID"]])}
  <div class="section-title"><h2>Дефекты / находки</h2><span class="label">${finds.length}</span></div>${table(finds,[["title","Наименование"],["finding_type","Тип"],["status","Статус"],["severity","Значимость"]])}`;
}

function table(rows,cols){
  if(!rows.length)return '<div class="card empty">Данных пока нет.</div>';
  return `<div class="table-wrap"><table class="table"><thead><tr>${cols.map(c=>`<th>${c[1]}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(c[0]==="updated_at"||c[0]==="created_at"?fmtDate(r[c[0]]):r[c[0]])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

async function renderTablePage(name,title,select){
  const rows=await db(name,{projectId:state.projectId,select,order:"created_at",limit:100});
  const cols=Object.keys(rows[0]||{}).map(k=>[k,k]);
  $("#page").innerHTML=`<div class="section-title"><h2>${title}</h2><span class="label">${rows.length} записей</span></div>${table(rows,cols)}`;
}

async function renderTasks(){
  const rows=await db("engineering_tasks",{projectId:state.projectId,select:"id,title,task_type,status,priority,created_at,updated_at",order:"updated_at",limit:100});
  $("#page").innerHTML=`<div class="card"><div class="label">Автономный исполнитель</div><div class="metric" style="font-size:18px">Очередь → Оркестратор → Worker → Validation → Handoff</div><div class="label">Новый расчёт не запускается автоматически; проверка представленного расчёта допускается в режиме аудита.</div></div><div class="section-title"><h2>Задачи</h2></div>${table(rows,[["title","Задача"],["task_type","Тип"],["status","Статус"],["priority","Приоритет"],["updated_at","Обновлена"]])}`;
}

async function renderAgents(){
  const rows=await db("agents",{select:"id,name,role,status,updated_at",limit:100});
  $("#page").innerHTML=`<div class="section-title"><h2>Инженерные агенты</h2></div>${table(rows,[["name","Агент"],["role","Роль"],["status","Статус"],["updated_at","Обновлён"]])}`;
}

async function renderAudit(){
  const [v,a,h]=await Promise.all([
    db("engineering_result_validations",{projectId:state.projectId,select:"id,status,task_id,validated_at,blocking_reasons",order:"created_at",limit:50}),
    db("engineering_contradictions",{projectId:state.projectId,select:"id,classification,description,created_at",order:"created_at",limit:50}),
    db("engineering_result_handoffs",{projectId:state.projectId,select:"id,handoff_status,source_task_id,validation_id,created_at",order:"created_at",limit:50})
  ]);
  $("#page").innerHTML=`<div class="grid three"><div class="card"><div class="label">Result validations</div><div class="metric">${v.length}</div>${v.slice(0,8).map(x=>`<p><span class="status ${statusClass(x.status)}">${esc(x.status)}</span> <span class="mono">${esc(x.task_id)}</span></p>`).join("")||'<div class="empty">Нет результатов.</div>'}</div><div class="card"><div class="label">Contradictions</div><div class="metric">${a.length}</div>${a.slice(0,8).map(x=>`<p><span class="status ${statusClass(x.classification)}">${esc(x.classification)}</span> ${esc(x.description)}</p>`).join("")||'<div class="empty">Противоречий не зарегистрировано.</div>'}</div><div class="card"><div class="label">Handoffs</div><div class="metric">${h.length}</div>${h.slice(0,8).map(x=>`<p><span class="status ${statusClass(x.handoff_status)}">${esc(x.handoff_status)}</span> <span class="mono">${esc(x.source_task_id)}</span></p>`).join("")||'<div class="empty">Handoff ещё нет.</div>'}</div></div>`;
}

async function renderPipeline(){
  if(!state.projectId){$("#page").innerHTML='<div class="card empty">Сначала выберите проект.</div>';return}
  const [runs,jobs,execs,recovery]=await Promise.all([
    db("orchestration_runs",{projectId:state.projectId,select:"id,task_id,status,current_stage,progress,completed_stages,failed_stages,last_error,created_at,updated_at",order:"updated_at",limit:20}),
    db("job_queue",{projectId:state.projectId,select:"id,task_id,stage,status,attempts,max_attempts,available_at,locked_at,last_error,orchestration_run_id",order:"updated_at",limit:50}),
    db("engineering_execution_queue",{projectId:state.projectId,select:"id,task_id,status,priority,attempt_count,max_attempts,orchestration_run_id,created_at,updated_at",order:"updated_at",limit:50}),
    db("project_recovery_runs",{projectId:state.projectId,select:"id,status,recovery_confidence,unresolved_items,created_at",order:"created_at",limit:10})
  ]);
  const running=jobs.filter(x=>x.status==="RUNNING").length, queued=jobs.filter(x=>x.status==="QUEUED").length, failed=jobs.filter(x=>/FAILED|BLOCKED/.test(x.status||"")).length;
  $("#page").innerHTML=`
    <div class="grid cards"><div class="card"><div class="label">Orchestration runs</div><div class="metric">${runs.length}</div></div><div class="card"><div class="label">Job queue</div><div class="metric">${queued}</div><div class="label">queued</div></div><div class="card"><div class="label">Workers</div><div class="metric">${running}</div><div class="label">running</div></div><div class="card"><div class="label">Terminal</div><div class="metric">${failed}</div><div class="label">failed / blocked</div></div></div>
    <div class="section-title"><h2>Контроль системы</h2><div style="display:flex;gap:8px;flex-wrap:wrap"><button id="securityTestBtn" class="btn secondary">Security self-test</button><button id="pipelineTestBtn" class="btn secondary">Pipeline self-test</button><button id="modelTestBtn" class="btn secondary">Тест модели</button></div></div>
    <div id="securityTestResult" class="card" style="display:none;margin-bottom:14px"></div>
    <div class="section-title"><h2>v28 Autonomous Recovery</h2><button id="recoverBtn" class="btn primary">Запустить recovery</button></div>
    <div class="card"><div class="label">Проверяет stale RUNNING leases в job_queue</div><div class="label" style="margin-top:6px">Порог по умолчанию: 10 минут. Retry — до max_attempts; исчерпание попыток переводит job в FAILED.</div></div>
    <div class="section-title"><h2>Orchestration runs</h2></div>${table(runs,[["status","Статус"],["current_stage","Текущий этап"],["progress","Прогресс %"],["task_id","Task ID"],["updated_at","Обновлён"],["last_error","Ошибка"]])}
    <div class="section-title"><h2>Canonical execution queue</h2></div>${table(execs,[["status","Статус"],["priority","Приоритет"],["attempt_count","Попытка"],["max_attempts","Макс."],["task_id","Task ID"],["updated_at","Обновлён"]])}
    <div class="section-title"><h2>Legacy / worker job queue</h2></div>${table(jobs,[["stage","Этап"],["status","Статус"],["attempts","Попытка"],["max_attempts","Макс."],["task_id","Task ID"],["last_error","Ошибка"]])}
    <div class="section-title"><h2>Recovery history</h2></div>${table(recovery,[["status","Статус"],["recovery_confidence","Confidence"],["created_at","Создан"],["unresolved_items","Неразрешённые"]])}`;
  $("#recoverBtn").addEventListener("click",runRecovery);
  $("#securityTestBtn").addEventListener("click",runSecurityTest);
  $("#pipelineTestBtn").addEventListener("click",runPipelineTest);
  $("#modelTestBtn").addEventListener("click",runModelTest);
}

async function runSecurityTest(){
  const box=$("#securityTestResult"); box.style.display="block"; box.innerHTML='<div class="label">Security self-test выполняется…</div>';
  try{
    const {data,error}=await supabase.functions.invoke("security-self-test-v1",{body:{project_id:state.projectId}});
    if(error) throw error;
    const checks=data?.checks||{};
    const rows=Object.entries(checks).map(([k,v])=>`<div style="display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid var(--line)"><b>${esc(k)}</b><span class="status ${statusClass(v.status)}">${esc(v.status)}</span></div>`).join("");
    box.innerHTML=`<div class="eyebrow">SECURITY / OWNER LOCK</div><h3 style="margin:6px 0">${esc(data?.status||"UNKNOWN")}</h3>${rows}<div class="label" style="margin-top:10px">${esc(data?.note||"")}</div>`;
  }catch(e){box.innerHTML=`<div class="status BLOCK">BLOCK</div><div style="margin-top:8px">${esc(e.message)}</div>`}
}

async function runPipelineTest(){
  try{const {data,error}=await supabase.functions.invoke("pipeline-self-test-v1",{body:{project_id:state.projectId}});if(error)throw error;toast(`Pipeline self-test: ${data?.status||"UNKNOWN"}`);console.log("PIPELINE SELF-TEST",data)}
  catch(e){toast("Pipeline self-test: "+e.message)}
}

async function runModelTest(){
  try{const {data,error}=await supabase.functions.invoke("model-connection-test-v1",{body:{}});if(error)throw error;toast(`Model connection: ${data?.status||"UNKNOWN"}`);console.log("MODEL CONNECTION TEST",data)}
  catch(e){toast("Тест модели: "+e.message)}
}

async function runRecovery(){
  const btn=$("#recoverBtn");btn.disabled=true;btn.textContent="Выполняется…";
  try{const {data,error}=await supabase.functions.invoke("autonomous-recovery-v28",{body:{stale_minutes:10}});if(error)throw error;toast(`Recovery: обнаружено ${data?.stale_detected??0}, восстановлено ${data?.recovered?.length??0}`);await renderPipeline();}
  catch(e){toast("Recovery error: "+e.message)}finally{btn.disabled=false;btn.textContent="Запустить recovery"}
}

async function createProject(){
  const name=prompt("Название инженерного проекта:","Новый инженерный проект");if(!name?.trim())return;
  const description=prompt("Краткое описание (необязательно):","")||"";
  const {data,error}=await supabase.rpc("create_project_with_membership",{p_name:name.trim(),p_description:description.trim()});
  if(error){toast("Не удалось создать проект: "+error.message);return}
  state.projectId=data;await loadProjects();await render();toast("Проект создан и привязан к текущему пользователю.");
}

function showLogin(){
  document.querySelector(".sidebar").style.display="none";document.querySelector(".topbar").style.display="none";
  $("#page").innerHTML=`<div style="max-width:440px;margin:8vh auto"><div class="card"><div class="eyebrow">ENGINEER OS / PRIVATE</div><h2 style="margin-top:8px">Аккаунт ENGINEER OS</h2><p class="label">Регистрация и вход выполняются через Supabase Auth. Доступ к инженерному контуру остаётся защищённым owner-lock.</p><div style="display:flex;gap:8px;margin-top:18px"><button id="showLoginBtn" class="btn primary" type="button">Войти</button><button id="showSignupBtn" class="btn secondary" type="button">Зарегистрироваться</button></div><div id="authFormWrap" style="margin-top:18px"></div><div id="loginError" class="notice" hidden style="margin-top:12px"></div></div></div>`;
  $("#showLoginBtn").addEventListener("click",()=>renderAuthForm("login"));
  $("#showSignupBtn").addEventListener("click",()=>renderAuthForm("signup"));
}

function renderAuthForm(mode){
  const wrap=$("#authFormWrap");
  const signup=mode==="signup";
  wrap.innerHTML=signup?'<form id="authForm" class="grid"><input id="authEmail" type="email" autocomplete="email" placeholder="E-mail" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px"><input id="authPassword" type="password" autocomplete="new-password" minlength="8" placeholder="Пароль (не менее 8 символов)" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px"><input id="authPassword2" type="password" autocomplete="new-password" minlength="8" placeholder="Повторите пароль" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px"><button class="btn primary" type="submit">Создать аккаунт</button></form>':'<form id="authForm" class="grid"><input id="authEmail" type="email" autocomplete="username" placeholder="E-mail" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px"><input id="authPassword" type="password" autocomplete="current-password" placeholder="Пароль" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px"><button class="btn primary" type="submit">Войти</button></form>';
  $("#authForm").addEventListener("submit",async e=>{e.preventDefault();const err=$("#loginError");err.hidden=true;const email=$("#authEmail").value.trim(),password=$("#authPassword").value;if(signup){if(password!==$("#authPassword2").value){err.textContent="Пароли не совпадают";err.hidden=false;return}const {data,error}=await supabase.auth.signUp({email,password});if(error){err.textContent="Регистрация отклонена: "+error.message;err.hidden=false;return}if(data.session){
  err.textContent="Аккаунт создан. Настраиваем инженерный контур…";
  err.hidden=false;
  await ensureAccountAccess();
  await loadProjects();
  await render();
  return;
}
err.textContent="Аккаунт создан. Подтвердите e-mail, если подтверждение включено, затем войдите.";
err.hidden=false}else{const {error}=await supabase.auth.signInWithPassword({email,password});if(error){err.textContent="Вход отклонён: "+error.message;err.hidden=false}}});
}

async function ensureAccountAccess(){
  const {data:{session}}=await supabase.auth.getSession();
  if(!session)return false;

  const {data:profile,error:profileError}=await supabase
    .from("user_profiles")
    .select("user_id,email,display_name,account_status")
    .eq("user_id",session.user.id)
    .maybeSingle();

  if(profileError){
    console.error("ENGINEER OS profile:",profileError);
    showLogin();
    toast("Не удалось проверить профиль аккаунта");
    return false;
  }

  if(profile?.account_status==="blocked"){
    await supabase.auth.signOut();
    showLogin();
    toast("Аккаунт заблокирован");
    return false;
  }

  const {data:owner,error:ownerError}=await supabase.rpc("claim_engineer_os_owner");
  if(ownerError){
    console.error("ENGINEER OS owner check:",ownerError);
    showLogin();
    toast("Не удалось проверить доступ ENGINEER OS");
    return false;
  }

  if(owner !== true){
    const {data:projectId,error:projectError}=await supabase.rpc("create_personal_engineer_project");
    if(projectError){
      console.error("ENGINEER OS onboarding:",projectError);
      showLogin();
      toast("Не удалось создать инженерный контур аккаунта");
      return false;
    }
    state.projectId=projectId;
  }

  return true;
}

async function boot(){
  document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>{state.page=b.dataset.page;render().catch(e=>toast(e.message))}));
  $("#projectSelect").addEventListener("change",e=>{state.projectId=e.target.value||null;render().catch(x=>toast(x.message))});
  $("#refreshBtn").addEventListener("click",()=>{loadProjects().then(render).catch(e=>toast(e.message))});
  $("#createProjectTopBtn")?.addEventListener("click",createProject);
  $("#logoutBtn")?.addEventListener("click",()=>supabase.auth.signOut());
  const {data:{session}}=await supabase.auth.getSession();state.session=session;
  supabase.auth.onAuthStateChange(async (_event,session)=>{
    state.session=session;
    if(!session){showLogin();return;}
    document.querySelector(".sidebar").style.display="flex";document.querySelector(".topbar").style.display="flex";
    if(await ensureAccountAccess()){await loadProjects();await render();}
  });
  if(!state.session){showLogin();renderAuthForm("login");return;}
  if(!(await ensureAccountAccess()))return;
  await loadProjects();await render();
}
boot().catch(e=>{console.error(e);toast("Ошибка запуска: "+e.message)});
