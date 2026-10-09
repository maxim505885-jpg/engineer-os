'use strict';
// These panels reuse the current session, local token and immutable originals.
(()=>{
 const cadPanel=$('cad-panel'),knowledgePanel=$('knowledge-panel');
 let cadRecord=null,cadFile=null,acceptedAudit=null,knowledgeGeneration=0,cadGeneration=0,editing=false;
 function options(select,rows,label){const choice=select.value;select.replaceChildren();for(const row of rows){const o=node('option',label(row));o.value=row.id;select.append(o);}if(rows.some(r=>r.id===choice))select.value=choice;}
 async function cadLoad(){if(!current)return;const sid=current,g=++cadGeneration,snap=await api(`/api/sessions/${sid}`);if(sid!==current||g!==cadGeneration)return;
  const files=snap.files.filter(f=>/\.(dxf|dwg)$/i.test(f.name));options($('cad-file'),files,f=>f.name);cadFile=files.find(f=>f.id===$('cad-file').value)||null;cadRecord=null;$('cad-derive').disabled=true;$('cad-inventory').replaceChildren();
  if(!cadFile){$('cad-inventory').textContent='Прикрепите DXF или DWG оригинал.';return;}
  const inv=await api(`/api/sessions/${sid}/cad/${cadFile.id}`);if(sid!==current||g!==cadGeneration)return;cadRecord=inv;
  $('cad-inventory').append(node('strong',(inv.format||'DXF')+' · '+inv.status),node('p','Единицы: '+(inv.unit_name||'не установлены')+' · '+(inv.units??'нет')),node('p','Инженерная корректность не проверена. Оригинал сохраняется.'),node('p',(inv.reasons||[]).join(', ')),node('p',JSON.stringify(inv.entity_counts||{})));
  options($('cad-handle'),(inv.entities||[]).map(e=>({...e,id:e.handle})),e=>e.type+' · '+e.handle+' · '+e.layer);
  options($('cad-evidence'),(snap.evidence||[]).filter(e=>e.file_id===cadFile.id),e=>e.statement||e.quote||e.id);$('cad-derive').disabled=inv.status==='BLOCK';
 }
 cadPanel.ontoggle=()=>{if(cadPanel.open)cadLoad().catch(error);};$('cad-file').onchange=()=>cadLoad().catch(error);
 $('cad-locator-form').onsubmit=async e=>{e.preventDefault();if(!current||!cadFile||editing)return;const sid=current;editing=true;try{await api(`/api/sessions/${sid}/cad/${cadFile.id}/locator`,{method:'POST',body:{handle:$('cad-handle').value,statement:$('cad-locator-note').value}});if(sid===current){await cadLoad();await refresh();}}catch(ex){error(ex);}finally{editing=false;}};
 $('cad-derive-form').onsubmit=async e=>{e.preventDefault();if(!current||!cadFile||!cadRecord||editing)return;const sid=current;editing=true;$('cad-derive').disabled=true;try{
  const request={source_sha256:cadFile.sha256,text:$('cad-text').value,insert:[Number($('cad-x').value),Number($('cad-y').value)],height:Number($('cad-height').value),reason:$('cad-reason').value,evidence_ids:Array.from($('cad-evidence').selectedOptions,o=>o.value),units_acknowledged:$('cad-units').checked?cadRecord.units:null};
  const r=await api(`/api/sessions/${sid}/cad/${cadFile.id}/derive`,{method:'POST',body:{request}});if(sid!==current)return;$('cad-result').replaceChildren(node('p','Отдельная аннотация сохранена. Проверка геометрии: '+r.verification.status+'; требуется ручная инженерная проверка.'));
  const b=node('button','Скачать проверенный DXF');b.type='button';b.onclick=()=>download(`/api/sessions/${sid}/cad/${r.id}/export`,'ENGINEER_OS_DERIVED.dxf',sid).catch(error);$('cad-result').append(b);
 }catch(ex){error(ex);}finally{editing=false;$('cad-derive').disabled=cadRecord?.status==='BLOCK';}};
 async function knowledgeLoad(){if(!current)return;const sid=current,g=++knowledgeGeneration;const [r,a,snap]=await Promise.all([api(`/api/sessions/${sid}/knowledge`),api(`/api/sessions/${sid}/final-audit`),api(`/api/sessions/${sid}`)]);if(sid!==current||g!==knowledgeGeneration)return;
  acceptedAudit=a.acceptance_granted&&a.current_fresh?a.current_audit_id:null;$('knowledge-status').textContent='Сохранение только из актуального ACCEPTED. Повторная проверка обязательна; память не является доказательством.';options($('knowledge-evidence'),snap.evidence||[],e=>e.statement||e.quote||e.id);$('knowledge-promote').disabled=!acceptedAudit;
  $('knowledge-records').replaceChildren();for(const row of r.records){const card=node('article');card.append(node('strong',(row.title||'Удалённая запись')+' · '+row.state+' · версия '+row.revision));for(const action of ['revoke','delete']){const b=node('button',action==='revoke'?'Отозвать':'Удалить содержание');b.type='button';b.disabled=row.state==='DELETED';b.onclick=async()=>{if(!current||current!==sid||editing)return;editing=true;try{await api(`/api/sessions/${sid}/knowledge/${row.id}/${action}`,{method:'POST',body:{expected_revision:row.revision,actor:$('knowledge-actor').value,reason:$('knowledge-reason').value}});await knowledgeLoad();}catch(ex){error(ex);}finally{editing=false;}};card.append(b);}$('knowledge-records').append(card);}
 }
 knowledgePanel.ontoggle=()=>{if(knowledgePanel.open)knowledgeLoad().catch(error);};
 $('knowledge-form').onsubmit=async e=>{e.preventDefault();if(!current||!acceptedAudit||editing)return;const sid=current;editing=true;$('knowledge-promote').disabled=true;try{await api(`/api/sessions/${sid}/knowledge`,{method:'POST',body:{expected_audit_id:acceptedAudit,title:$('knowledge-title').value,evidence_ids:Array.from($('knowledge-evidence').selectedOptions,o=>o.value),actor:$('knowledge-actor').value}});if(sid===current)await knowledgeLoad();}catch(ex){error(ex);}finally{editing=false;$('knowledge-promote').disabled=!acceptedAudit;}};
 $('knowledge-recall').onclick=async()=>{if(!current)return;const sid=current,r=await api(`/api/sessions/${sid}/knowledge/recall?query=${encodeURIComponent($('knowledge-query').value)}`);if(sid!==current)return;$('knowledge-references').replaceChildren(node('p','Повторная проверка обязательна. Найдено: '+r.records.length));for(const x of r.records)$('knowledge-references').append(node('h3',x.title),node('p',JSON.stringify(x.evidence)),node('small','NOT_EVIDENCE · исходный audit '+x.audit_id));};
 $('knowledge-export').onclick=()=>{if(current)download(`/api/sessions/${current}/knowledge/export`,'ENGINEER_OS_KNOWLEDGE.json',current).catch(error);};
 async function download(url,name,sid){if(current!==sid)return;const response=await api(url);const blob=response instanceof Response?await response.blob():new Blob([JSON.stringify(response,null,2)],{type:'application/json'});if(current!==sid)return;const href=URL.createObjectURL(blob),a=node('a');a.href=href;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),1000);}
 $('knowledge-recall').addEventListener('click',()=>error(null));
 document.addEventListener('engineer-session-change',()=>{
  cadGeneration++;knowledgeGeneration++;cadRecord=null;cadFile=null;acceptedAudit=null;
  for(const id of ['cad-inventory','cad-result','knowledge-records','knowledge-references'])$(id).replaceChildren();
  for(const id of ['cad-file','cad-handle','cad-evidence','knowledge-evidence'])$(id).replaceChildren();
  $('cad-derive').disabled=true;$('knowledge-promote').disabled=true;
  for(const id of ['cad-text','cad-reason','cad-locator-note','knowledge-title','knowledge-query','knowledge-reason'])$(id).value='';
  cadPanel.open=false;knowledgePanel.open=false;
 });
})();
