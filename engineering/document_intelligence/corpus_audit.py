"""Complete source-file census using existing readers; never content acceptance."""
from collections import Counter
import hashlib
from pathlib import Path

MAX_FILES=500
MAX_FILE_BYTES=256*1024*1024
MAX_CORPUS_BYTES=2*1024*1024*1024


def _files(root):
    return sorted(p for p in root.rglob('*') if p.is_file())


def _sha(path):
    digest=hashlib.sha256();size=0
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):
            size+=len(data)
            if size>MAX_FILE_BYTES:raise ValueError('SOURCE_SIZE_LIMIT')
            digest.update(data)
    return digest.hexdigest()


def audit_corpus(root,*,expected_manifest=None):
    root=Path(root).resolve()
    base=dict(status='BLOCK',scope='SOURCE_INVENTORY_NOT_CONTENT_QUALIFICATION',
              acceptance_granted=False,complete_document_set=False,
              files=[],file_count=0,pdf_pages=0,docx_logical_units=0,reasons=[])
    if not root.is_dir():return dict(base,reasons=['SOURCE_DIRECTORY_REQUIRED'])
    if expected_manifest is not None and (not isinstance(expected_manifest,dict) or
            any(not isinstance(k,str) or not isinstance(v,str) or len(v)!=64 or
                any(c not in '0123456789abcdef' for c in v) for k,v in expected_manifest.items())):
        return dict(base,reasons=['EXPECTED_MANIFEST_INVALID'])
    paths=_files(root)
    if not paths or len(paths)>MAX_FILES:return dict(base,reasons=['SOURCE_COUNT_LIMIT_OR_EMPTY'])
    if sum(p.stat().st_size for p in paths)>MAX_CORPUS_BYTES:
        return dict(base,reasons=['CORPUS_SIZE_LIMIT'])
    records=[]
    for path in paths:
        row=dict(relative=path.relative_to(root).as_posix(),extension=path.suffix.lower(),
                 bytes=path.stat().st_size,status='UNCERTAINTY',role='SOURCE',
                 acceptance_granted=False,completeness='NOT_VERIFIED',reasons=[])
        try:
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p!=root):
                raise ValueError('SOURCE_SYMLINK_UNSUPPORTED')
            sha=_sha(path);row['source_sha256']=sha
            if expected_manifest is not None and expected_manifest.get(row['relative'])!=sha:
                raise ValueError('SOURCE_IDENTITY_MISMATCH')
            if path.name.startswith('~$'):
                row.update(role='TEMPORARY_OWNER_FILE',status='EXCLUDED')
            elif path.suffix.lower()=='.pdf':
                from scripts.pdf_layer_census import inventory
                census=inventory(path)
                if census['sha256']!=sha:raise ValueError('SOURCE_CHANGED_DURING_AUDIT')
                row.update(pages=census['page_count'],native_empty_pages=census['native_empty_pages'],
                           pages_with_images=census['pages_with_embedded_images'],
                           page_inventory=census['pages'],limitations=['VISUAL_CONTENT_NOT_VERIFIED'])
            elif path.suffix.lower() in ('.docx','.xlsx'):
                from engineering.local_app.office import read
                units,limits=read(path.read_bytes(),path.suffix.lower()[1:])
                row.update(logical_units=len(units),units_with_limits=sum(bool(x['limitations']) for x in units),
                           limitations=limits,limitation_counts=dict(Counter(r for u in units for r in u['limitations'])))
            elif path.suffix.lower()=='.dwg':
                row.update(role='CAD_SOURCE',limitations=['DWG_CONVERSION_AND_SOURCE_EQUIVALENCE_REQUIRED'])
            elif path.suffix.lower() in ('.lir','.~lir'):
                row.update(role='CALCULATION_BACKUP' if path.suffix.lower()=='.~lir' else 'CALCULATION_SOURCE',
                           limitations=['VENDOR_MODEL_SEMANTICS_AND_RUN_NOT_VERIFIED'])
            else:row.update(status='BLOCK',reasons=['FORMAT_NOT_AUDITED'])
            row['original_unchanged']=_sha(path)==sha
            if not row['original_unchanged']:raise ValueError('SOURCE_CHANGED_DURING_AUDIT')
        except Exception as exc:
            known={'SOURCE_SIZE_LIMIT','SOURCE_SYMLINK_UNSUPPORTED','SOURCE_IDENTITY_MISMATCH','SOURCE_CHANGED_DURING_AUDIT'}
            row.update(status='BLOCK',reasons=[str(exc) if str(exc) in known else 'SOURCE_INSPECTION_FAILED'],
                       error_type=type(exc).__name__)
        records.append(row)
    current=_files(root)
    unchanged=paths==current
    reasons=['CONTENT_COMPLETENESS_NOT_QUALIFIED']
    if not unchanged:reasons.append('SOURCE_TREE_CHANGED')
    content_changed=False
    for path,row in zip(paths,records):
        if 'source_sha256' not in row:continue
        try:
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p!=root):
                raise ValueError('SOURCE_SYMLINK_UNSUPPORTED')
            preserved=_sha(path)==row['source_sha256']
        except (OSError,ValueError):
            preserved=False
        row['original_unchanged']=preserved
        if not preserved:
            content_changed=True
            row['status']='BLOCK'
            if 'SOURCE_CHANGED_DURING_AUDIT' not in row['reasons']:
                row['reasons'].append('SOURCE_CHANGED_DURING_AUDIT')
    if content_changed:reasons.append('SOURCE_CONTENT_CHANGED')
    if expected_manifest is not None and set(expected_manifest)!={x['relative'] for x in records}:
        reasons.append('EXPECTED_MANIFEST_FILE_SET_MISMATCH')
    return dict(base,files=records,file_count=len(records),extensions=dict(Counter(x['extension'] for x in records)),
                pdf_pages=sum(x.get('pages',0) for x in records),
                docx_logical_units=sum(x.get('logical_units',0) for x in records if x['extension']=='.docx'),
                source_tree_unchanged=unchanged,originals_unchanged=all(x.get('original_unchanged',False) for x in records),
                reasons=reasons)
