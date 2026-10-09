"""Fail-closed identities for persisted extraction and model drafts."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def parser_identity(backend):
    from . import extraction
    if backend in {'docx','xlsx','doc'}:
        import sys
        from . import office
        value=dict(schema=1,backend=backend,python=sys.version.split()[0],implementation=hashlib.sha256(Path(office.__file__).read_bytes()).hexdigest(),
                    limits=[office.MAX_XML,office.MAX_EXPANDED,office.MAX_ENTRIES,office.MAX_UNITS,extraction.MAX_PAGE_TEXT,extraction.MAX_TOTAL_TEXT,office.MAX_PACKAGE_EXPANDED])
        if backend=='doc':
            from .doc_conversion import converter_identity
            value['converter']=converter_identity()
        return value
    packages=['PyMuPDF']+(['Pillow'] if backend=='ocr' else [])+(['docling','docling-core','rapidocr','onnxruntime','torch'] if backend=='docling' else [])
    versions={}
    for name in packages:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]='NOT_INSTALLED'
    code=[Path(extraction.__file__)]
    artifacts=[]
    if backend=='ocr':
        from . import ocr,files
        code.extend([Path(ocr.__file__),Path(files.__file__)])
        artifacts=ocr.identity()
    if backend=='docling':
        from engineering.document_intelligence import docling_adapter
        code.append(Path(docling_adapter.__file__))
        folder=os.environ.get('ENGINEER_OS_DOCLING_ARTIFACTS_PATH','')
        root=Path(folder) if folder else None
        if root and root.is_dir():
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    h=hashlib.sha256()
                    with path.open('rb') as f:
                        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                    artifacts.append([str(path.relative_to(root)),h.hexdigest()])
    return dict(schema=1,backend=backend,versions=versions,
                implementation={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in code},
                budgets=[extraction.MAX_PAGES,extraction.MAX_PAGE_TEXT,extraction.MAX_BLOCKS,extraction.MAX_TOTAL_TEXT],
                artifacts=artifacts,document_intelligence=os.environ.get('ENGINEER_OS_DOCUMENT_INTELLIGENCE','false') if backend=='docling' else None,
                table_mode='accurate',ocr_languages=['iso:ru','iso:en'] if backend=='docling' else [])


def identity(store,job,model):
    from . import automatic_analysis,core_run,worker,model as model_module,core_plan,coverage,requirements,source_binding,specialist_checks,domain_packets,engineering_review,provenance
    from engineering.normative import verification,numeric_comparison,substantive_review
    from engineering.calculation import model_intake
    from engineering.model_gateway import openai_compatible
    files=[store.get_file(fid) for fid in job['file_ids']]
    from .core_plan import verify_originals
    if any(f['session_id']!=job['session_id'] for f in files):raise ValueError('Source isolation failure')
    verify_originals(files)
    backend=os.environ.get('ENGINEER_OS_ATTACHMENT_PARSER','native')
    if backend not in {'native','docling','ocr'}:raise ValueError('Unknown parser')
    selected=model.checkpoint_identity() if hasattr(model,'checkpoint_identity') else None
    implementation={Path(m.__file__).name:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (automatic_analysis,core_run,worker,model_module,core_plan,coverage,openai_compatible,requirements,source_binding,specialist_checks,domain_packets,engineering_review,verification,numeric_comparison,model_intake,provenance)}
    implementation['identity']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    implementation['substantive_review']=hashlib.sha256(Path(substantive_review.__file__).read_bytes()).hexdigest()
    if job['mode']=='CORE_RUN':
        from engineering.core.skill_loader import SkillLoader
        from engineering.core.engineer_core import CHECK_REGISTRY
        loader=SkillLoader(Path(__file__).resolve().parents[2])
        implementation['skills']=[digest(loader.load(CHECK_REGISTRY[c][1])) for c in dict.fromkeys(job['requested_checks']+['final_audit'])]
    value=dict(schema=1,task_id=job['id'],session_id=job['session_id'],mode=job['mode'],prompt=job['prompt'],checks=job['requested_checks'],
               sources=[dict(id=f['id'],sha256=f['sha256'],name=f['name']) for f in files],parser=parser_identity(backend),model=selected,
               evidence_sha256=context_identity(store,job)['evidence_sha256'],
               domain_packets_sha256=context_identity(store,job)['domain_packets_sha256'],
               requirements_sha256=digest(store.requirements_state(job['session_id'])),
               parsers={f['id']:parser_identity('ocr' if Path(f['name']).suffix.lower() in {'.png','.jpg','.jpeg'} else Path(f['name']).suffix.lower()[1:]) for f in files if Path(f['name']).suffix.lower() in {'.docx','.xlsx','.doc','.png','.jpg','.jpeg'}},
               implementation=implementation,budgets=dict(part_chars=automatic_analysis.PART_CHARS,source_chars=automatic_analysis.MAX_SOURCE_CHARS,
               max_calls=automatic_analysis.MAX_MODEL_CALLS,max_seconds=automatic_analysis.MAX_MODEL_SECONDS,summary_chars=automatic_analysis.SUMMARY_CHARS))
    return value,digest(value),selected is not None


def context_identity(store,job):
    from .domain_packets import latest
    packets=store.domain_packets_state(job['session_id'])
    current_packets=latest(packets)
    domain_linked={s['candidate_id'] for e in current_packets for s in e['sources']}
    live_sources=[]
    for fid in sorted({f['id'] for e in current_packets for f in e['files']}):
        f=store.get_file(fid)
        try:
            with Path(f['path']).open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        except OSError:actual='UNAVAILABLE'
        live_sources.append([fid,actual])
    state=store.requirements_state(job['session_id']);current=state['sets'][-1]['id'] if state['sets'] else None
    linked={s['candidate_id'] for e in state['assessments'] if e['set_id']==current for s in e['sources']}
    return dict(requirements_sha256=digest(state),domain_packets_sha256=digest([packets,live_sources]),
        evidence_sha256=digest([r for r in store.snapshot(job['session_id'])['evidence'] if r['file_id'] in job['file_ids'] or r['id'] in linked or r['id'] in domain_linked]))
