"""Versioned draft conclusions. Never an engineering acceptance issuer."""
import json
import time
import uuid
from .analysis_identity import digest
from .real_case import report as case_report
from .store import identifier, ReviewConflict

LABEL='ЧЕРНОВИК — НЕ ПРИНЯТО'

def _text(value,limit):
    if not isinstance(value,str) or len(value)>limit or any(not (ord(c) in {9,10,13} or 32<=ord(c)<=0xD7FF or 0xE000<=ord(c)<=0xFFFD or 0x10000<=ord(c)<=0x10FFFF) for c in value):
        raise ValueError('Invalid draft text or text limit exceeded')
    return value.strip()

def _state(store,session_id):
    identifier(session_id)
    with store.connection() as db:
        if not db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone():raise ValueError('Conversation not found')
        rows=[]
        for row in db.execute('SELECT id,session_id,revision,record FROM conclusion_drafts WHERE session_id=? ORDER BY revision',(session_id,)):
            record=json.loads(row['record'])
            if (record.get('id'),record.get('session_id'),record.get('revision'))!=(row['id'],row['session_id'],row['revision']):raise ValueError('Draft storage identity changed')
            if rows:rows[-1].pop('content',None)
            rows.append(record)
        return rows

def _basis(store,session_id):
    report=case_report(store,session_id)
    case=next((c for c in report['cases'] if c['current']),None)
    if not case:raise ValueError('Сначала соберите снимок проекта')
    return case,dict(case_id=case['id'],case_sha256=case['case_sha256'])

def _section(key,title,paragraphs=(),headers=(),rows=()):
    return dict(key=key,title=title,paragraphs=list(paragraphs),headers=list(headers),rows=[list(row) for row in rows])

def _content(store,session_id,case,author,summary,recommendations,limitations):
    snap=store.snapshot(session_id);originals=case['identity']['originals'];selected={f['id'] for f in originals}
    facts=[c for c in snap['evidence'] if c['file_id'] in selected]
    reqs=case['requirements']['requirements'];packets=case['domain_packets'].get('packets',[])
    reasons=list(dict.fromkeys(x for s in case['stages'].values() for x in s.get('reasons',[])))
    source_rows=[[f['id'],f['name'],f['sha256']] for f in originals]
    req_rows=[[r['id'],r['text'],r['status'],r.get('conclusion') or 'Вывод не записан',', '.join(s.get('candidate_id','') for s in r.get('sources',[]))] for r in reqs]
    fact_rows=[];fact_paragraphs=[]
    for c in facts:
        review=c.get('latest_review') or {}
        place=json.dumps(dict(page=c.get('page'),locator=c.get('locator'),source_binding=c.get('source_binding')),ensure_ascii=False,sort_keys=True)
        fact_rows.append([c['id'],c['data_class']+' — заявлен',str(review.get('decision','NOT_REVIEWED'))])
        fact_paragraphs.extend(['Кандидат '+c['id']+'; файл '+c['file_id']+'; '+place,'Точная цитата: '+c['quote'],'Запись пользователя: '+c['statement']])
    def domain(kind):
        lines=[]
        for p in packets:
            if p['kind']!=kind:continue
            lines.append('Пакет '+p['id']+'; версия '+str(p['revision'])+'; '+p['status'])
            for k,v in (p.get('packet',{}).get('chain') or {}).items():lines.append(k+': '+str(v))
            for binding in p.get('packet',{}).get('bindings',[]):lines.append('Роль '+binding['role']+'; файл '+binding['file_id']+'; кандидаты '+', '.join(binding.get('candidate_ids',[])))
            for key in ('semantic_review','exchange_review','solver_review','execution_review','result_review','structure_review','arithmetic','authority_review','authority_source','data_class_review'):
                if p.get(key) is not None:lines.append(key+': '+json.dumps(p[key],ensure_ascii=False,sort_keys=True))
            decision=p.get('substantive_decision') or {}
            if decision:lines.append('Записанное предметное решение: '+json.dumps(decision,ensure_ascii=False,sort_keys=True))
            lines.extend('Основание '+s['candidate_id']+'; SHA256 '+s['source_sha256'] for s in p.get('sources',[]))
            lines.extend('Ограничение: '+r for r in p.get('reasons',[]))
        return lines or ['Данные не представлены. Проверка и инженерное принятие не подтверждены.']
    findings=[]
    for role in case['stages']['specialists'].get('results',[]):
        findings.append(role['agent']+'; '+role['execution']+'; '+role['status'])
        if role.get('summary'):findings.append(role['summary'])
        findings.extend('Ограничение роли: '+str(v) for v in role.get('limitations',[]))
        for finding in role.get('findings',[]):
            findings.append(finding['text']+'; основания: '+', '.join(finding.get('source_ids',[]))+'; требования: '+', '.join(finding.get('requirement_ids',[])))
    sections=[
        _section('scope','Объект и область проверки',[snap['session']['title'],'Снимок проекта '+case['id'],'Автор записи: '+author+'; личность и квалификация не подтверждены.','Формируется предварительный документ по сохранённым данным. Инженерное принятие отсутствует.']),
        _section('sources','Исходные документы',headers=['ID файла','Документ','SHA256'],rows=source_rows),
        _section('requirements','Требования технического задания',paragraphs=[] if req_rows else ['Требования ТЗ не представлены.'],headers=['ID','Требование','Статус','Записанный вывод','Кандидаты источников'],rows=req_rows),
        _section('facts','Факты и доказательства',paragraphs=fact_paragraphs if fact_rows else ['Доказательства не зарегистрированы.'],headers=['ID кандидата','Тип данных','Проверка источника'],rows=fact_rows),
        _section('normative','Нормативная проверка',domain('NORMATIVE')),
        _section('calculations','Расчётная проверка',domain('CALCULATION')),
        _section('findings','Замечания и контроль качества',findings+['BLOCK: '+r for r in reasons] or ['Замечания не представлены; это не доказательство отсутствия дефектов.']),
        _section('summary','Предварительные выводы',[summary or 'Выводы не записаны.','Авторский текст не прошёл инженерную проверку.']),
        _section('recommendations','Рекомендации',[recommendations or 'Рекомендации не записаны.']),
        _section('limitations','Ограничения',[limitations or 'Дополнительные ограничения не записаны.','Расчётная семантика, полномочия проверяющего и инженерное принятие требуют отдельного подтверждения.','acceptance=false; FINAL AUDIT NOT_RUN для этого документа.']),
    ]
    content=dict(title='Черновик инженерного заключения',label=LABEL,sections=sections)
    for section in sections:
        for text in section['paragraphs']+section['headers']+[str(cell) for row in section['rows'] for cell in row]:_text(text,1_000_000)
    if len(json.dumps(content,ensure_ascii=False))>1_000_000:raise ValueError('Draft document exceeds supported content limit')
    return content,reasons

def build(store,session_id,*,expected_revision,author,summary='',recommendations='',limitations='',expected_basis_sha256=None):
    if type(expected_revision) is not int or expected_revision<0:raise ValueError('Draft revision required')
    author=_text(author,120)
    if not author:raise ValueError('Укажите автора записи')
    summary=_text(summary,20000);recommendations=_text(recommendations,20000);limitations=_text(limitations,20000)
    case,basis=_basis(store,session_id)
    if not case['fresh']:raise ValueError('Снимок проекта устарел. Обновите его перед подготовкой черновика.')
    if expected_basis_sha256 is not None and expected_basis_sha256!=basis['case_sha256']:raise ReviewConflict('Основание черновика изменилось; перечитайте источники')
    content,reasons=_content(store,session_id,case,author,summary,recommendations,limitations)
    event=dict(id=str(uuid.uuid4()),session_id=session_id,created=time.time(),basis=basis,author=author,
               summary=summary,recommendations=recommendations,limitations=limitations,content=content,
               content_sha256=digest(content),status='BLOCK' if reasons else 'UNCERTAINTY',
               qc_reasons=reasons+['AUTHOR_TEXT_UNVERIFIED','DRAFT_NOT_ACCEPTANCE'],acceptance_granted=False,final_audit='NOT_RUN')
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        count=db.execute('SELECT count(*) FROM conclusion_drafts WHERE session_id=?',(session_id,)).fetchone()[0]
        if count!=expected_revision:raise ReviewConflict('Черновик изменился. Откройте текущую версию перед сохранением.')
        if count>=100:raise ValueError('Draft history limit: 100')
        record=dict(event,revision=count+1)
        record['record_sha256']=digest(record)
        db.execute('INSERT INTO conclusion_drafts VALUES(?,?,?,?)',(record['id'],session_id,record['revision'],json.dumps(record,ensure_ascii=False)))
    return record

def report(store,session_id):
    state=_state(store,session_id)
    if not state:return dict(drafts=[],revision=0,acceptance_granted=False)
    current=state[-1];reasons=[]
    if digest({k:v for k,v in current.items() if k!='record_sha256'})!=current.get('record_sha256') or digest(current.get('content'))!=current.get('content_sha256'):
        reasons.append('DRAFT_INTEGRITY_CHANGED')
    try:
        case,basis=_basis(store,session_id)
        if basis!=current['basis']:reasons.append('DRAFT_BASIS_CHANGED')
        if not case['fresh']:reasons.extend(case['stale_reasons'] or ['CASE_NOT_FRESH'])
    except (ValueError,KeyError):reasons.append('DRAFT_BASIS_UNAVAILABLE')
    return dict(drafts=[dict(r,current=r['id']==current['id'],fresh=r['id']==current['id'] and not reasons,
                            stale_reasons=reasons if r['id']==current['id'] else ['SUPERSEDED_DRAFT']) for r in state],
                revision=current['revision'],acceptance_granted=False)

def export(store,session_id,*,revision,format):
    if type(revision) is not int:raise ValueError('Draft revision required')
    if format not in {'docx','pdf'}:raise ValueError('Unsupported draft export')
    state=report(store,session_id);record=next((r for r in state['drafts'] if r['revision']==revision),None)
    if not record or not record['current'] or not record['fresh']:raise ValueError('Экспорт требует актуального проверенного черновика')
    from .conclusion_export import render
    return render(record,format)
