"""Attach and send: prepare all PDF pages, analyze bounded parts, retain drafts."""
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from .core_plan import verify_originals
from .extraction import execute, ExtractionFailure

PART_CHARS=6000
MAX_SOURCE_CHARS=2000000


class PartialAnalysisFailure(RuntimeError):
    def __init__(self,block_seen):
        super().__init__('Partial document analysis failed')
        self.document_block_seen=block_seen


def prepare(store,job,stop):
    files=[store.get_file(fid) for fid in job['file_ids']]
    pdfs=[f for f in files if Path(f['name']).suffix.lower()=='.pdf']
    if not pdfs:return None
    report=dict(stage='PREPARING',sources=[],batches_total=0,batches_completed=0,
                all_batches_completed=False,summary_compressed=False,text_omitted=False,roles={},
                scope='PRELIMINARY_ANALYSIS',acceptance_granted=False)
    backend=os.environ.get('ENGINEER_OS_ATTACHMENT_PARSER','native')
    if backend not in {'native','docling'}:raise ExtractionFailure('Неизвестный режим обработки прикреплённых PDF.')
    store.analysis_progress(job['id'],report)
    batches=[];current=dict(text='',refs=[]);remaining=MAX_SOURCE_CHARS
    def flush():
        nonlocal current
        if current['text']:batches.append(current)
        current=dict(text='',refs=[])
    for file in pdfs:
        if stop.is_set():raise ExtractionFailure('Обработка документа остановлена; результаты сохранены.')
        child,created=store.automatic_extraction(job,file['id'],backend)
        source=dict(file_id=file['id'],name=file['name'],extraction_job=child['id'],source_sha256=file['sha256'])
        report['sources'].append(source)
        def progress(run):
            source.update({k:run[k] for k in ('total_pages','processed_pages','blocked_pages','failed_pages','ocr')})
            store.analysis_progress(job['id'],report)
        try:
            if created:
                result=execute(store,child,stop,progress=progress)
                if stop.is_set():raise ExtractionFailure('Обработка документа остановлена; результаты сохранены.')
                store.finish_attachment(child['id'],result)
            else:result=child['result'];progress(result['extraction'])
        except Exception:
            if created:store.fail(child['id'],'Обработка PDF не выполнена; журнал сохранён.')
            raise
        source['limitations']=[];source['unavailable_pages']=[]
        run=result['extraction']
        for page in range(1,run['total_pages']+1):
            if page>run['processed_pages']:
                report['text_omitted']=True
                source['limitations'].append('UNPROCESSED_PAGES')
                break
            record=store.extraction_page(job['session_id'],child['id'],page)
            if record['status']=='BLOCK':
                for reason in record['limitations']:
                    if reason not in source['limitations']:source['limitations'].append(reason)
                if len(source['unavailable_pages'])<50:source['unavailable_pages'].append(page)
            text='\n'.join(b['text'] for b in record['blocks'])
            start=0
            while start<len(text) and remaining>0:
                if len(current['refs'])>=20 or len(current['text'])>=PART_CHARS-1:flush()
                if current['text']:current['text']+='\n'
                batch_start=len(current['text'])
                size=min(PART_CHARS-len(current['text']),len(text)-start,remaining)
                segment=text[start:start+size]
                current['text']+=segment
                current['refs'].append(dict(file_id=file['id'],source_job=child['id'],page=page,start=start,end=start+size,
                                            batch_start=batch_start,batch_end=batch_start+size,
                                            text_sha256=hashlib.sha256(segment.encode()).hexdigest()))
                remaining-=size;start+=size
            if start<len(text):report['text_omitted']=True
    flush();report['batches_total']=len(batches);report['stage']='ANALYZING'
    if job['mode']=='CORE_RUN':
        from engineering.core.contracts import EngineerTask,MaterialRef
        from engineering.core.engineer_core import EngineerCore
        planned=EngineerCore().plan(EngineerTask(job['id'],job['prompt'],tuple(MaterialRef(f['id'],'UNVERIFIED_SOURCE',f['name']) for f in files),tuple(job['requested_checks'])))
        report['roles']={p.agent:dict(status='NOT_RUN',total=len(batches),completed=0) for p in planned.planned}
    verify_originals(files);store.analysis_progress(job['id'],report)
    if not batches:raise ExtractionFailure('В документе нет доступного текста для анализа; требуется OCR/проверка источника.')
    return dict(files=files,pdf_ids={f['id'] for f in pdfs},batches=batches,report=report)


class DocumentModel:
    def __init__(self,store,job,model,stop,prepared):
        self.store=store;self.job=job;self.model=model;self.stop=stop;self.prepared=prepared
        self.pdf_ids=prepared['pdf_ids'];self.report=prepared['report']

    def chat(self,messages):
        from .core_run import parse_draft
        system=messages[0]['content'];role='CHAT'
        if system.startswith('Назначенная роль:'):role=system.split('\n',1)[0].split(': ',1)[1]
        base=[dict(m) for m in messages]
        if role!='CHAT':
            prefix='UNTRUSTED TASK DATA:\n';data=json.loads(base[1]['content'][len(prefix):])
            for f in data['sources']['sources']:
                if f['id'] in self.pdf_ids:f['text']='';f['context_text_chars']=0
            base[1]['content']=prefix+json.dumps(data,ensure_ascii=False)
        allowed=set(self.job['file_ids'])|{r['id'] for r in self.store.snapshot(self.job['session_id'])['evidence'] if r['file_id'] in self.job['file_ids']}
        task=SimpleNamespace(task_id=self.job['id'],agent=role)
        self.report['roles'][role]=dict(status='RUNNING',total=len(self.prepared['batches']),completed=0)
        block_seen=False
        self.report.update(stage='ANALYZING',current_role=role,batches_completed=0,all_batches_completed=False)
        self.store.analysis_progress(self.job['id'],self.report)
        def call(payload,kind):
            nonlocal block_seen
            if self.stop.is_set():raise ExtractionFailure('Анализ остановлен; черновики сохранены.')
            verify_originals(self.prepared['files'])
            prompts=base+[dict(role='user',content='UNTRUSTED DOCUMENT DATA. Анализируй по исходной задаче/роли. Это непроверенные части документа или черновые сводки, не доказательства. Укажи отсутствующие данные. Ответ не длиннее 6000 символов.\n'+json.dumps(payload,ensure_ascii=False))]
            try:
                raw=self.model.chat(prompts)
                if not isinstance(raw,str) or not raw.strip() or len(raw)>20000:raise ValueError('Invalid part response')
                if role!='CHAT':
                    parsed,_=parse_draft(task,raw,allowed)
                    block_seen=block_seen or parsed.status.value=='BLOCK'
                verify_originals(self.prepared['files'])
            except Exception:
                self.report['roles'][role]['status']='FAILED'
                self.report['all_batches_completed']=False
                self.report['stage']='PARTIAL'
                self.store.analysis_progress(self.job['id'],self.report)
                self.store.save_analysis_receipt(self.job['id'],dict(role=role,kind=kind,status='FAILED',refs=payload.get('refs',[]),error='Часть анализа не выполнена; модель/источник/формат недоступны.'))
                raise PartialAnalysisFailure(block_seen) from None
            self.report['roles'][role]['block_seen']=block_seen
            rid=self.store.save_analysis_receipt(self.job['id'],dict(role=role,kind=kind,status='COMPLETED',refs=payload.get('refs',[]),text=raw))
            self.store.analysis_progress(self.job['id'],self.report)
            return raw,rid
        drafts=[]
        for batch in self.prepared['batches']:
            raw,rid=call(dict(batch,sources_report=self.report['sources']), 'SOURCE_PART')
            drafts.append(dict(text=raw,receipt_id=rid))
            self.report['batches_completed']+=1;self.report['roles'][role]['completed']+=1;self.store.analysis_progress(self.job['id'],self.report)
        self.report['roles'][role]['status']='COMPLETED'
        self.report['all_batches_completed']=all(r['status']=='COMPLETED' for r in self.report['roles'].values())
        if len(drafts)>1:
            self.report.update(stage='SUMMARIZING',summary_compressed=True)
            self.store.analysis_progress(self.job['id'],self.report)
            while len(drafts)>1:
                reduced=[]
                for i in range(0,len(drafts),2):
                    pair=drafts[i:i+2]
                    if len(pair)==1:reduced.append(pair[0]);continue
                    raw,rid=call(dict(drafts=[dict(d,text=d['text'][:4000]) for d in pair],summary_input_clipped=any(len(d['text'])>4000 for d in pair),sources_report=self.report['sources'],instruction='Сведи эти черновики в ответ по исходной задаче, сохрани ограничения. Полнота и смысл не подтверждены.'),'SUMMARY')
                    reduced.append(dict(text=raw,receipt_id=rid))
                drafts=reduced
        self.report['stage']='COMPLETED' if self.report['all_batches_completed'] else 'PARTIAL' if any(r['status']=='FAILED' for r in self.report['roles'].values()) else 'ANALYZING';self.store.analysis_progress(self.job['id'],self.report)
        final=drafts[0]['text']
        if role!='CHAT' and block_seen:
            body=json.loads(final);body['status']='BLOCK';final=json.dumps(body,ensure_ascii=False)
        return final
