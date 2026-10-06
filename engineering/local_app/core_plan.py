"""Deterministic CORE preparation, never a specialist execution or evidence grant."""
from engineering.core.contracts import EngineerTask,MaterialRef
from engineering.core.engineer_core import EngineerCore

LABELS={'report-audit-agent':'Проверка отчёта','normative-agent':'Нормативная проверка','inspection-agent':'Обследование','calculation-agent':'Проверка расчёта','final-audit-agent':'FINAL AUDIT'}


def prepare(store,job):
    files=[store.get_file(fid) for fid in job['file_ids']]
    if any(f['session_id']!=job['session_id'] for f in files):raise ValueError('Attachment isolation failure')
    materials=tuple(MaterialRef(f['id'],'UNVERIFIED_SOURCE',f['name']) for f in files)
    task=EngineerTask(job['id'],job['prompt'],materials,tuple(job['requested_checks']))
    core=EngineerCore();state=core.plan(task)
    plan=dict(task_id=job['id'],tz=job['prompt'],status=core.final_status(state).value,
        specialists=[dict(agent=p.agent,skill=p.skill,label=LABELS[p.agent],execution='NOT_RUN') for p in state.planned],
        materials=[dict(id=f['id'],name=f['name'],sha256=f['sha256'],size=f['size'],source_status=f['extraction_status'],text_truncated=f['text_truncated'],evidentiary_status='NOT_EVIDENCE') for f in files],
        evidence_ids=[],acceptance_granted=False,final_audit='NOT_RUN',
        missing=['Проверка извлечения и полноты исходников','Факты с координатами и реестр доказательств','Выполнение профильных проверок','FINAL AUDIT и acceptance gate'])
    text='План инженерной проверки подготовлен ENGINEER CORE. Проверки ещё не выполнены.\nТЗ: '+job['prompt']+'\n'+ '\n'.join('• '+p['label']+' — не выполнено' for p in plan['specialists'])+'\nИсходников: '+str(len(files))+'. Статус: UNCERTAINTY. Инженерное принятие отсутствует.'
    return dict(text=text,core_plan=plan,context_truncated=any(f['text_truncated'] or f['extraction_status']=='UNAVAILABLE' for f in files))
