"""Source-bound engineering adapters in the existing durable job queue.

User-entered numbers are ASSUMED. Calculating them never verifies measurements,
source interpretation, normative compliance, or the actual structure.
"""
import json
from pathlib import Path
from .analysis_identity import digest
from .core_plan import verify_originals
from .store import identifier,ReviewConflict

TOOLS=('BEAM','PLANAR','RECTANGLE','CAD_INVENTORY','CAD_DIFF','CAD_ANNOTATE',
       'DWG_CONVERT','IFC_INVENTORY','IFC_GEOMETRY','IFC_REQUIREMENTS','IFC_DIFF')
ENABLED=('BEAM','PLANAR','RECTANGLE')
MAX_REQUEST=65536


def revision(store,session_id):
    from .verification import verification_stamp
    snap=store.snapshot(session_id)
    return digest(dict(files=[[f['id'],f['sha256'],f['size']] for f in snap['files']],
        evidence=snap['evidence'],requirements=store.requirements_state(session_id),
        domains=store.domain_packets_state(session_id),verification=verification_stamp(store,session_id)))


def catalog(store,session_id):
    return dict(schema='ENGINEER_OS_ENGINEERING_TOOLS_V1',expected_revision=revision(store,session_id),
        tools=[dict(tool=tool,available=tool in ENABLED,reason=None if tool in ENABLED else 'BOUNDED_WORKER_OR_SOURCE_REVIEW_NOT_QUALIFIED') for tool in TOOLS],
        input_data_class='ASSUMED',acceptance_granted=False)


def validate_request(store,session_id,request,file_ids):
    if not isinstance(request,dict) or set(request)!={'tool','input_file_ids','options','expected_revision','sources','request_sha256'}:
        raise ValueError('ENGINEERING_REQUEST_REQUIRED')
    raw={k:v for k,v in request.items() if k!='request_sha256'}
    if digest(raw)!=request['request_sha256']:raise ValueError('ENGINEERING_REQUEST_CHANGED')
    if request['tool'] not in ENABLED or request['input_file_ids']!=file_ids:raise ValueError('ENGINEERING_REQUEST_INVALID')
    if request['expected_revision']!=revision(store,session_id):raise ReviewConflict('Engineering context changed; reopen inputs')
    files=[store.get_file(fid) for fid in file_ids]
    if any(f['session_id']!=session_id for f in files):raise ValueError('Foreign engineering input')
    if request['sources']!=[[f['id'],f['sha256']] for f in files]:raise ValueError('ENGINEERING_SOURCE_CHANGED')
    verify_originals(files)
    return files


def enqueue_engineering(store,session_id,*,tool,input_file_ids,options,expected_revision):
    identifier(session_id)
    if tool not in ENABLED:raise ValueError('ENGINEERING_TOOL_NOT_QUALIFIED')
    if not isinstance(input_file_ids,list) or not 1<=len(input_file_ids)<=2 or any(not isinstance(fid,str) for fid in input_file_ids) or len(set(input_file_ids))!=len(input_file_ids):raise ValueError('One or two distinct input files required')
    if not isinstance(expected_revision,str) or len(expected_revision)!=64:raise ValueError('Exact engineering revision required')
    for fid in input_file_ids:identifier(fid)
    expected_count=2 if tool.endswith('_DIFF') else 1
    if len(input_file_ids)!=expected_count:raise ValueError('Wrong input file count')
    if not isinstance(options,dict):raise ValueError('Engineering options required')
    if any(k in options for k in ('source_sha256','evidence_ids','engineering_verified','acceptance_granted')):raise ValueError('Server-owned input identity cannot be supplied')
    if tool not in ('BEAM','PLANAR','RECTANGLE') and options:raise ValueError('This tool takes no options')
    try:encoded=json.dumps(options,allow_nan=False,ensure_ascii=False)
    except (ValueError,TypeError,RecursionError):raise ValueError('Finite JSON options required') from None
    if len(encoded.encode('utf-8'))>MAX_REQUEST:raise ValueError('Engineering request size limit')
    options=json.loads(encoded)
    files=[store.get_file(fid) for fid in input_file_ids]
    request=dict(tool=tool,input_file_ids=input_file_ids,options=options,expected_revision=expected_revision,
        sources=[[f['id'],f['sha256']] for f in files])
    request['request_sha256']=digest(request)
    validate_request(store,session_id,request,input_file_ids)
    return store.enqueue(session_id,'Engineering: '+tool,input_file_ids,mode='ENGINEERING_RUN',engineering_request=request)


def request_for(store,session_id,job_id):
    identifier(session_id);identifier(job_id)
    with store.connection() as db:
        row=db.execute('SELECT e.record FROM engineering_inputs e JOIN jobs j ON j.id=e.job_id WHERE j.id=? AND j.session_id=?',(job_id,session_id)).fetchone()
    if row is None:raise ValueError('Engineering request not found in this conversation')
    value=json.loads(row['record'])
    if not isinstance(value,dict) or value.get('request_sha256')!=digest({k:v for k,v in value.items() if k!='request_sha256'}):raise ValueError('ENGINEERING_REQUEST_CHANGED')
    return value


def execute_engineering(store,job,stop):
    request=request_for(store,job['session_id'],job['id'])
    files=validate_request(store,job['session_id'],request,job['file_ids'])
    run=dict(schema='ENGINEER_OS_ENGINEERING_RUN_V1',tool=request['tool'],
        request_sha256=request['request_sha256'],sources=request['sources'],
        input_data_class='ASSUMED',acceptance_granted=False,actual_structure_verified=False,
        normative_verification='NOT_RUN',result=None)
    envelope=dict(text='Инженерная задача: исходники связаны; расчёт ещё не завершён.',engineering_run=run,acceptance_granted=False)
    store.checkpoint(job['id'],envelope)
    if stop.is_set():return envelope
    tool=request['tool'];data=dict(request['options']);path=Path(files[0]['path']);sha=files[0]['sha256']
    if tool in ('BEAM','PLANAR','RECTANGLE'):
        data.update(source_sha256=sha,evidence_ids=tuple('unverified-file:'+f['id'] for f in files))
        try:
            if tool=='BEAM':
                from .calculation_process import run_calculation
                result=run_calculation(tool,data,stop)
            elif tool=='RECTANGLE':
                from engineering.calculation.section_control import RectangleInput,calculate_rectangle
                result=calculate_rectangle(RectangleInput(**data))
            else:
                if not all(isinstance(data.get(key),list) for key in ('nodes','members','loads')):raise ValueError('Typed planar lists required')
                from .calculation_process import run_calculation
                result=run_calculation(tool,data,stop)
        except (TypeError,KeyError,ValueError):raise ValueError('ENGINEERING_INPUT_FIELDS_INVALID') from None
    elif tool=='CAD_INVENTORY':
        from .cad import inventory
        result=inventory(store,job['session_id'],files[0]['id'])
    elif tool=='CAD_DIFF':
        from engineering.cad.roundtrip import compare_dxf
        result=compare_dxf(path,Path(files[1]['path']),source_sha256=sha)
    elif tool=='IFC_INVENTORY':
        from engineering.bim.ifc_adapter import inspect_ifc
        result=inspect_ifc(path,expected_sha256=sha)
    else:
        from engineering.bim.ifc_adapter import compare_ifc
        result=compare_ifc(path,Path(files[1]['path']),source_sha256=sha)
    validate_request(store,job['session_id'],request,job['file_ids'])
    run['result']=result
    labels={'area_m2':'Площадь, м²','iy_m4':'Iy, м⁴','iz_m4':'Iz, м⁴','wy_m3':'Wy, м³','wz_m3':'Wz, м³',
        'reaction_left_n':'Левая реакция, Н','reaction_right_n':'Правая реакция, Н','midspan_moment_nm':'Момент в середине, Н·м','midspan_deflection_m':'Прогиб в середине, м','left_shear_n':'Поперечная сила слева, Н'}
    numbers=result.get('results') or {}
    readable='\n'.join(labels[key]+': '+format(value,'.9g') for key,value in numbers.items() if key in labels and type(value) in (int,float))
    if not readable:readable='Подробные результаты и ограничения сохранены в квитанции задачи.'
    envelope['text']='Инженерная задача '+tool+': '+result['status']+'. Введённые значения — ASSUMED; фактическая конструкция и нормы не приняты.\n'+readable
    if len(envelope['text'])>24000:envelope['text']=envelope['text'][:24000]+'\n[Показана часть результата; полный receipt в задаче.]'
    if len(json.dumps(envelope,ensure_ascii=False,allow_nan=False).encode('utf-8'))>2*1024*1024:raise ValueError('ENGINEERING_RESULT_LIMIT')
    store.checkpoint(job['id'],envelope)
    return envelope
