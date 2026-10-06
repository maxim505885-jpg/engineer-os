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
    packages=['PyMuPDF']+(['docling','docling-core','rapidocr','onnxruntime','torch'] if backend=='docling' else [])
    versions={}
    for name in packages:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]='NOT_INSTALLED'
    code=[Path(extraction.__file__)]
    artifacts=[]
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
    from . import automatic_analysis,core_run,worker,model as model_module,core_plan,coverage
    from engineering.model_gateway import openai_compatible
    files=[store.get_file(fid) for fid in job['file_ids']]
    from .core_plan import verify_originals
    if any(f['session_id']!=job['session_id'] for f in files):raise ValueError('Source isolation failure')
    verify_originals(files)
    backend=os.environ.get('ENGINEER_OS_ATTACHMENT_PARSER','native')
    if backend not in {'native','docling'}:raise ValueError('Unknown parser')
    selected=model.checkpoint_identity() if hasattr(model,'checkpoint_identity') else None
    implementation={Path(m.__file__).name:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (automatic_analysis,core_run,worker,model_module,core_plan,coverage,openai_compatible)}
    implementation['identity']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if job['mode']=='CORE_RUN':
        from engineering.core.skill_loader import SkillLoader
        from engineering.core.engineer_core import CHECK_REGISTRY
        loader=SkillLoader(Path(__file__).resolve().parents[2])
        implementation['skills']=[digest(loader.load(CHECK_REGISTRY[c][1])) for c in dict.fromkeys(job['requested_checks']+['final_audit'])]
    value=dict(schema=1,task_id=job['id'],session_id=job['session_id'],mode=job['mode'],prompt=job['prompt'],checks=job['requested_checks'],
               sources=[dict(id=f['id'],sha256=f['sha256'],name=f['name']) for f in files],parser=parser_identity(backend),model=selected,
               evidence_sha256=digest([r for r in store.snapshot(job['session_id'])['evidence'] if r['file_id'] in job['file_ids']]),
               implementation=implementation,budgets=dict(part_chars=automatic_analysis.PART_CHARS,source_chars=automatic_analysis.MAX_SOURCE_CHARS,
               max_calls=automatic_analysis.MAX_MODEL_CALLS,max_seconds=automatic_analysis.MAX_MODEL_SECONDS,summary_chars=automatic_analysis.SUMMARY_CHARS))
    return value,digest(value),selected is not None
