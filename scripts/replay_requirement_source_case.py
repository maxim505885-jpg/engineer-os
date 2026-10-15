"""Controlled requirement/role replay, not inference or full PDF analysis.

Input: private source dossier with requirements and source SHA256. Original PDF
is preserved unchanged. A fresh output directory is required. This exercises
CORE reconciliation directly; automatic document analysis is NOT_RUN here.
"""
import argparse,json,math,threading
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review
from engineering.local_app.requirements import create_set,assess
from engineering.local_app.core_run import execute
from engineering.local_app.real_case import build
from engineering.local_app.analysis_identity import digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--dossier',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 data=json.loads(args.dossier.read_text());args.output.mkdir(parents=True,exist_ok=False)
 store=Store(args.output/'data');sid=store.create_session()['id'];file=preserve_file(store,sid,'V4-original.pdf',args.pdf.read_bytes())
 if file['sha256']!=data['sources'][0]['sha256']:raise ValueError('Source dossier identity mismatch')
 tor=[]
 for page,quote in [(5,'Техническое задание'),(6,'ОСК-ССК-22/0526-1')]:
  c=register(store,sid,file_id=file['id'],page=page,quote=quote,statement='Native page heading/frame only; scanned condition body is not authenticated')
  record_review(store,sid,c['id'],expected_revision=0,decision='NEEDS_DATA',note='Visual page inspected; no authenticated transcription or automatic geometry proof',actor='Codex source review: identity and qualification unverified');tor.append(c)
 native=register(store,sid,file_id=file['id'],page=13,quote='Высота первого этажа - 5,4 м;',statement='Author report claim, not actual measured height')
 record_review(store,sid,native['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Unique native quote geometry only',actor='Codex source reader: qualification unverified')
 tz=create_set(store,sid,text='\n'.join(r['clause']+' '+r['requirement'] for r in data['requirements']),source_evidence_ids=[c['id'] for c in tor])
 mapping={}
 for req,row in zip(tz['requirements'],data['requirements']):
  mapping[req['id']]=row
  assess(store,sid,set_id=tz['id'],requirement_id=req['id'],expected_revision=0,conclusion=row['finding'][:2000],evidence_ids=[tor[0 if row['original_page']==5 else 1]['id']],relation='UNKNOWN',actor='Codex: controlled source-analysis replay; qualification unverified')
 calls=[]
 class ControlledReplay:
  def chat(self,messages):
   payload=json.loads(messages[-1]['content'].split('\n',1)[1]);ctx=payload['sources']['requirements'];index=ctx.get('requirement_index',ctx['requirements']);ids=[r['id'] for r in index];role=messages[0]['content'].split('\n',1)[0].split(': ',1)[1];calls.append(dict(role=role,indexed_requirements=len(ids),context_truncated=ctx['context_truncated']))
   scopes={'normative-agent':{'9.1','11.3','11.10','13.7','14.4 (безопасность)'},'calculation-agent':{'8.1','11.7'},'inspection-agent':{'8.1','10.1','11.3','11.4','11.5','11.6','11.8','11.9','13.1','13.9','15.1.4','15.1.5','15.2.6'}}
   if role in scopes:ids=[rid for rid in ids if mapping[rid]['clause'] in scopes[role]]
   calls[-1]['observed_requirements']=len(ids)
   chunk=max(1,math.ceil(len(ids)/12));obs=[]
   for start in range(0,len(ids),chunk):
    refs=ids[start:start+chunk];source_ids=list(dict.fromkeys(tor[0 if mapping[r]['original_page']==5 else 1]['id'] for r in refs))
    text='; '.join(mapping[r]['clause']+': '+mapping[r]['finding'] for r in refs)
    obs.append(dict(text=text[:1800],source_ids=source_ids,requirement_ids=refs,relation='UNKNOWN'))
   return json.dumps(dict(status='BLOCK',summary='Controlled replay of human-authored source findings; no independent model expertise',observations=obs,limitations=['Scanned ToR not authenticated','No normative or solver execution','No field verification or qualified sign-off','Compact index/details do not establish full source analysis']),ensure_ascii=False)
 job=store.enqueue(sid,'Controlled replay of all source-dossier conditions',[file['id']],mode='CORE_RUN',requested_checks=['report','inspection','normative','calculation']);claimed=store.claim();assert claimed['id']==job['id']
 result=execute(store,claimed,ControlledReplay(),threading.Event());store.finish(job['id'],result)
 persisted=store.snapshot(sid)['jobs'][0]['result'];saved=Store(store.root).snapshot(sid)['jobs'][0]['result'];assert saved==persisted
 assert saved['core_run']==json.loads(json.dumps(result['core_run']))
 review=saved['core_run']['engineering_review'];qc=build(store,sid,job_id=job['id'],expected_revision=0,manifest={'TOR':[file['id']],'REPORT':[file['id']]})
 artifact=dict(scope='CONTROLLED_SOURCE_ANALYSIS_REPLAY_NOT_LIVE_MODEL_EXPERTISE',source_sha256=file['sha256'],dossier_sha256=digest(dict(sources=data['sources'],requirements=data['requirements'])),dossier_digest_scope='SOURCE_IDENTITIES_AND_CONDITIONS_ONLY',condition_count=len(mapping),calls=calls,result=saved,real_case=qc,automatic_pdf_analysis='NOT_RUN',live_model='NOT_RUN',normative_execution='NOT_RUN',solver='NOT_RUN',engineering_verified=False,acceptance_granted=False,final_audit='NOT_RUN')
 (args.output/'ENGINEER_OS_STAGE7_REQUIREMENT_CASE.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
 addressed=sum(bool(r['observations']) for r in review['requirements'])
 summary=dict(conditions=len(mapping),addressed=addressed,roles=len(calls),all_roles_see_full_index=all(c['indexed_requirements']==len(mapping) for c in calls),status=review['status'],source_status='BLOCK',saved_reload_equal=True,native_quote_status=native['provenance']['status'],automatic_pdf_analysis='NOT_RUN',live_model='NOT_RUN',acceptance_granted=False,final_audit='NOT_RUN',qc_status=qc['stages']['specialists']['status'])
 assert addressed==len(mapping) and summary['all_roles_see_full_index'] and review['status']=='BLOCK' and not review['acceptance_granted']
 (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
