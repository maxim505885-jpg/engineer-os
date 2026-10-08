"""Deterministic CORE preparation, never a specialist execution or evidence grant."""
import hashlib
from pathlib import Path
from .coverage import summary, incomplete
from engineering.core.contracts import EngineerTask,MaterialRef
from engineering.core.engineer_core import EngineerCore

LABELS={'report-audit-agent':'Проверка отчёта','normative-agent':'Нормативная проверка','inspection-agent':'Обследование','calculation-agent':'Проверка расчёта','final-audit-agent':'FINAL AUDIT'}


def verify_originals(files):
    for f in files:
        path=Path(f['path'])
        if path.stat().st_size!=f['size']:raise ValueError('Original identity check failed')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=f['sha256']:raise ValueError('Original identity check failed')


def prepare(store,job):
    files=[store.get_file(fid) for fid in job['file_ids']]
    if any(f['session_id']!=job['session_id'] for f in files):raise ValueError('Attachment isolation failure')
    verify_originals(files)
    materials=tuple(MaterialRef(f['id'],'UNVERIFIED_SOURCE',f['name']) for f in files)
    task=EngineerTask(job['id'],job['prompt'],materials,tuple(job['requested_checks']))
    core=EngineerCore();state=core.plan(task)
    plan=dict(task_id=job['id'],tz=job['prompt'],status=core.final_status(state).value,
        specialists=[dict(agent=p.agent,skill=p.skill,label=LABELS[p.agent],execution='NOT_RUN') for p in state.planned],
        materials=[dict(id=f['id'],name=f['name'],sha256=f['sha256'],size=f['size'],source_status=f['extraction_status'],text_truncated=f['text_truncated'],evidentiary_status='NOT_EVIDENCE',extraction_coverage=summary(f['extraction_coverage'])) for f in files],
        evidence_ids=[],acceptance_granted=False,final_audit='NOT_RUN',
        missing=['Проверка извлечения и полноты исходников','Факты с координатами и реестр доказательств','Выполнение профильных проверок','FINAL AUDIT и acceptance gate'])
    candidates=[r for r in store.snapshot(job['session_id'])['evidence'] if r['file_id'] in job['file_ids']]
    plan['source_reviews']=dict(scope='SOURCE_REVIEW_ONLY',candidates_total=len(candidates),truncated=len(candidates)>100,candidates=[dict(candidate_id=r['id'],source_sha256=r['source_sha256'],review_revision=r['review_revision'],decision=r['latest_review']['decision'] if r['latest_review'] else 'NOT_REVIEWED',review_event_id=r['latest_review']['id'] if r['latest_review'] else None,acceptance_granted=False) for r in candidates[:100]])
    from .requirements import report
    requirements=report(store,job['session_id'],selected_files=job['file_ids']);plan['requirements_report']=requirements
    from .specialist_checks import report as specialist_report
    from .domain_packets import report as domain_report
    domains=domain_report(store,job['session_id'],selected_files=job['file_ids'])
    checks=specialist_report(job,domains);plan['specialist_checks']=checks
    if checks['status']=='BLOCK' or requirements['status']=='BLOCK':plan['status']='BLOCK'
    text='План инженерной проверки подготовлен ENGINEER CORE. Проверки ещё не выполнены.\nТЗ: '+job['prompt']+'\n'+ '\n'.join('• '+p['label']+' — не выполнено' for p in plan['specialists'])+'\nИсходников: '+str(len(files))+'. Статус: '+plan['status']+'. Инженерное принятие отсутствует.'
    return dict(text=text,core_plan=plan,requirements_report=requirements,specialist_checks=checks,domain_packets=domains,context_truncated=plan['source_reviews']['truncated'] or any(f['text_truncated'] or f['extraction_status']=='UNAVAILABLE' or incomplete(f['extraction_coverage']) for f in files))
