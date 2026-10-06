"""Immutable user-authored domain inputs with source review snapshots.

Source traceability and arithmetic do not verify facts, normative applicability,
model semantics, or execution of a solver.
"""
import json
import re
import time
import uuid
from .analysis_identity import digest
from .requirements import source_check
from engineering.normative.verification import NormativeVerificationRecord,gate_normative_verification
from engineering.normative.numeric_comparison import compare_quantity
from engineering.calculation.model_intake import CalculationArtifact,CalculationArtifactRole,audit_calculation_model_intake
from engineering.normative.authority import NormativeAuthorityReview,audit_normative_authority
from engineering.calculation.semantic_review import CalculationSemanticReview,audit_calculation_semantics
from engineering.calculation.exchange_manifest import parse_exchange_manifest,audit_exchange_manifest
from engineering.calculation.solver_receipt import SolverReceipt,audit_solver_receipt
from engineering.calculation.execution_identity import SolverExecutionIdentity,audit_execution_identity
from engineering.calculation.result_verification import SolverResultVerification,audit_solver_results
from engineering.calculation.structure_correlation import StructureCorrelationItem,audit_structure_correlation
from engineering.normative.source_verification import NormativeSourceVerification,audit_normative_source
from .data_classification import DataClassReview,audit_data_classes

CHAIN=('document','edition','scope','clause','requirement','actual_condition','comparison','conclusion')
ALIASES={'м':'m','мм':'mm','см':'cm','Н':'N','кН':'kN','Па':'Pa','кПа':'kPa','МПа':'MPa','м2':'m2','мм2':'mm2'}


def ids(values):
    if not isinstance(values,list) or not 1<=len(values)<=20 or any(not isinstance(v,str) for v in values) or len(set(values))!=len(values):
        raise ValueError('Select 1–20 distinct source candidates')
    return values


def complete_fragment(fragment,text):
    start=text.find(fragment)
    if start<0 or start!=text.rfind(fragment):return False
    before=text[:start];after=text[start+len(fragment):]
    if re.search(r'[\w.,+\-−/]$',before) or re.search(r'\d\s+$',before):return False
    if re.match(r'[\w^/\-+−]',after):return False
    return True


def quantity(value,allowed,candidates,field_text):
    if not isinstance(value,dict) or set(value)!={'candidate_id','value','unit','fragment'}:
        raise ValueError('Quantity requires candidate, value, unit and exact fragment')
    if value['candidate_id'] not in allowed:raise ValueError('Quantity candidate does not belong to this field')
    if any(not isinstance(value[k],str) or not value[k].strip() or len(value[k])>120 for k in ('value','unit','fragment')):
        raise ValueError('Invalid quantity fields')
    fragment=value['fragment'];quote=candidates[value['candidate_id']]['quote']
    if not re.fullmatch(re.escape(value['value'])+r'\s*'+re.escape(value['unit']),fragment) or not complete_fragment(fragment,quote) or field_text not in quote or not complete_fragment(fragment,field_text):
        raise ValueError('Value and unit must occur together in a unique exact quoted fragment')
    return value


def save(store,session_id,*,packet,expected_revision):
    if type(expected_revision) is not int or expected_revision<0:raise ValueError('Packet revision required')
    if not isinstance(packet,dict) or len(json.dumps(packet,ensure_ascii=False))>32000:raise ValueError('Bounded domain packet required')
    candidates={r['id']:r for r in store.snapshot(session_id)['evidence']}
    kind=packet.get('kind');refs=[];files=[]
    if kind=='NORMATIVE':
        if not {'kind','chain','norm_ids','actual_ids','quantities'}<=set(packet) or not set(packet)<= {'kind','chain','norm_ids','actual_ids','quantities','authority_review','authority_source','data_class_reviews'}:
            raise ValueError('Invalid normative packet fields')
        chain=packet['chain']
        if not isinstance(chain,dict) or set(chain)!=set(CHAIN) or any(not isinstance(v,str) or not v.strip() or len(v)>1000 for v in chain.values()):raise ValueError('Complete bounded normative chain required')
        norm=ids(packet['norm_ids']);actual=ids(packet['actual_ids']);refs=norm+actual
        for eid in refs:
            if eid not in candidates:raise ValueError('Source candidate not found in this conversation')
        q=packet['quantities']
        if q is not None:
            if not isinstance(q,dict) or set(q)!={'actual','limit','operator'}:raise ValueError('Invalid comparison fields')
            quantity(q['actual'],actual,candidates,chain['actual_condition']);quantity(q['limit'],norm,candidates,chain['requirement'])
            numeric=compare_quantity(actual=q['actual']['value'].replace(',','.'),actual_unit=ALIASES.get(q['actual']['unit'],q['actual']['unit']),limit=q['limit']['value'].replace(',','.'),limit_unit=ALIASES.get(q['limit']['unit'],q['limit']['unit']),operator=q['operator'])
            if numeric['status']=='BLOCK':raise ValueError('Invalid numeric comparison: '+','.join(numeric['reasons']))
        gate_normative_verification(NormativeVerificationRecord(**chain,evidence_ids=tuple(dict.fromkeys(refs))))
        if 'authority_review' in packet:
            a=packet['authority_review']
            if not isinstance(a,dict) or set(a)!={'document','edition','clause','authority','source_ref','applicability_basis','decision'}:
                raise ValueError('Invalid normative authority review')
            if any(a[k]!=chain[k] for k in ('document','edition','clause')):
                raise ValueError('Authority review must match normative chain identity')
            audit_normative_authority(NormativeAuthorityReview(**a))
        if 'authority_source' in packet:
            a=packet['authority_source']
            expected={'candidate_id','document','edition','authority','source_ref','source_sha256','verification_method','decision'}
            if not isinstance(a,dict) or set(a)!=expected:raise ValueError('Invalid normative source verification')
            if a['candidate_id'] not in norm or a['candidate_id'] not in candidates:raise ValueError('Normative authority source must belong to norm sources')
            source_file=store.get_file(candidates[a['candidate_id']]['file_id'])
            if a['source_sha256']!=source_file['sha256']:raise ValueError('Normative authority source hash mismatch')
            if a['document']!=chain['document'] or a['edition']!=chain['edition']:raise ValueError('Normative source identity must match chain')
            audit_normative_source(NormativeSourceVerification(**a))
    elif kind=='CALCULATION':
        if not isinstance(packet,dict) or packet.get('kind')!='CALCULATION' or not set(packet)<= {'kind','bindings','semantic_reviews','exchange_manifest','solver_receipt','execution_identity','result_verification','structure_correlation','data_class_reviews'} or not {'kind','bindings'}<=set(packet) or not isinstance(packet['bindings'],list) or not 1<=len(packet['bindings'])<=9:raise ValueError('Select at most nine calculation roles')
        roles=[]
        for binding in packet['bindings']:
            if not isinstance(binding,dict) or set(binding)!={'role','file_id','candidate_ids'}:raise ValueError('Invalid calculation binding')
            role=CalculationArtifactRole(binding['role']);roles.append(role)
            f=store.get_file(binding['file_id'])
            if f['session_id']!=session_id:raise ValueError('Calculation source belongs to another conversation')
            files.append(f)
            for eid in ids(binding['candidate_ids']):
                if eid not in candidates or candidates[eid]['file_id']!=f['id']:raise ValueError('Calculation candidate/file mismatch')
                refs.append(eid)
        if len(set(roles))!=len(roles):raise ValueError('Calculation roles must be distinct')
        if 'semantic_reviews' in packet:
            semantic=packet['semantic_reviews']
            if not isinstance(semantic,list) or len(semantic)>9:raise ValueError('Invalid calculation semantic reviews')
            allowed_by_role={b['role']:set(b['candidate_ids']) for b in packet['bindings']}
            reviews=[]
            for item in semantic:
                if not isinstance(item,dict) or set(item)!={'role','statement','candidate_ids','decision','basis'}:
                    raise ValueError('Invalid calculation semantic review')
                role=CalculationArtifactRole(item['role'])
                source_ids=ids(item['candidate_ids'])
                if role.value not in allowed_by_role or not set(source_ids)<=allowed_by_role[role.value]:
                    raise ValueError('Semantic review sources must belong to the same calculation role')
                reviews.append(CalculationSemanticReview(role,item['statement'],tuple(source_ids),item['decision'],item['basis']))
            audit_calculation_semantics(tuple(reviews))
        if 'exchange_manifest' in packet:
            raw=json.dumps(packet['exchange_manifest'],ensure_ascii=False,separators=(',',':'))
            parse_exchange_manifest(raw)
        if 'solver_receipt' in packet:
            sr=packet['solver_receipt']
            if not isinstance(sr,dict) or set(sr)!={'solver_name','solver_version','input_sha256','output_sha256','log_sha256','exit_code','started_at','finished_at'}:
                raise ValueError('Invalid solver receipt')
            receipt=SolverReceipt(**sr);audit_solver_receipt(receipt)
        else:
            receipt=None
        if 'execution_identity' in packet:
            if receipt is None:raise ValueError('Execution identity requires solver receipt')
            x=packet['execution_identity']
            expected={'solver_name','solver_version','executable_sha256','command_sha256','input_sha256','output_sha256','log_sha256'}
            if not isinstance(x,dict) or set(x)!=expected:raise ValueError('Invalid solver execution identity')
            audit_execution_identity(SolverExecutionIdentity(**x),receipt)
        if 'result_verification' in packet:
            if receipt is None:raise ValueError('Result verification requires solver receipt')
            x=packet['result_verification']
            expected={'input_sha256','output_sha256','log_sha256','output_source_ref','log_source_ref','completeness','consistency','log_review','critical_findings'}
            if not isinstance(x,dict) or set(x)!=expected:raise ValueError('Invalid solver result verification')
            audit_solver_results(SolverResultVerification(**dict(x,critical_findings=tuple(x['critical_findings']))),receipt)
        if 'structure_correlation' in packet:
            if not isinstance(packet['structure_correlation'],list) or len(packet['structure_correlation'])>4:raise ValueError('Invalid structure correlation')
            by_role={b['role']:set(b['candidate_ids']) for b in packet['bindings']}
            actual=by_role.get('ACTUAL_STRUCTURE_REFERENCE',set())
            reviews=[]
            for x in packet['structure_correlation']:
                expected={'role','calculation_source_ids','actual_source_ids','statement','basis','decision'}
                if not isinstance(x,dict) or set(x)!=expected:raise ValueError('Invalid structure correlation item')
                calc=ids(x['calculation_source_ids']);actual_ids=ids(x['actual_source_ids'])
                if x['role'] not in by_role or not set(calc)<=by_role[x['role']] or not set(actual_ids)<=actual:
                    raise ValueError('Structure correlation sources must match calculation and actual-structure roles')
                reviews.append(StructureCorrelationItem(x['role'],tuple(calc),tuple(actual_ids),x['statement'],x['basis'],x['decision']))
            audit_structure_correlation(tuple(reviews))
    else:raise ValueError('Unknown domain packet kind')
    if 'data_class_reviews' in packet:
        if not isinstance(packet['data_class_reviews'],list) or len(packet['data_class_reviews'])>100:raise ValueError('Invalid data-class reviews')
        reviews=[]
        for x in packet['data_class_reviews']:
            if not isinstance(x,dict) or set(x)!={'candidate_id','data_class','decision','basis'}:raise ValueError('Invalid data-class review')
            if x['candidate_id'] not in refs or x['candidate_id'] not in candidates:raise ValueError('Data-class review candidate outside packet')
            if candidates[x['candidate_id']]['data_class']!=x['data_class']:raise ValueError('Data-class review does not match candidate declaration')
            reviews.append(DataClassReview(**x))
        audit_data_classes(tuple(reviews),tuple(dict.fromkeys(refs)))
    snapshots=[]
    for eid in dict.fromkeys(refs):
        r=candidates[eid];base=store.get_evidence(session_id,eid)
        files.append(store.get_file(r['file_id']))
        snapshots.append(dict(candidate_id=eid,candidate_sha256=digest(base),review_revision=r['review_revision'],review_event_id=(r['latest_review'] or {}).get('id')))
    event=dict(id=str(uuid.uuid4()),session_id=session_id,kind=kind,packet=packet,sources=snapshots,
        files=[dict(id=f['id'],sha256=f['sha256']) for f in {f['id']:f for f in files}.values()],
        origin='USER_AUTHORED_DOMAIN_PACKET',created=time.time(),acceptance_granted=False)
    return store.add_domain_packet(event,expected_revision)


def latest(state):
    out={}
    for event in state:out[event['kind']]=event
    return list(out.values())


def report(store,session_id,*,selected_files=None):
    state=store.domain_packets_state(session_id)
    candidates={r['id']:r for r in store.snapshot(session_id)['evidence']};rows=[]
    for event in latest(state):
        p=event['packet'];sources=[];reasons=[];authority_review=None;authority_source=None;data_class_review=None;semantic_review=None;exchange_review=None;solver_review=None;execution_review=None;result_review=None;structure_review=None
        for expected in event['sources']:
            r=candidates.get(expected['candidate_id'])
            if not r:reasons.append('CANDIDATE_MISSING');continue
            checked=source_check(store,session_id,r,expected,selected_files);sources.append(checked);reasons.extend(checked['reasons'])
        linked=bool(sources and not reasons);numeric=None;intake=None
        if p['kind']=='NORMATIVE':
            normative_text='\n'.join(candidates[e]['quote'] for e in p['norm_ids'] if e in candidates)
            actual_text='\n'.join(candidates[e]['quote'] for e in p['actual_ids'] if e in candidates)
            if any(p['chain'][k] not in normative_text for k in ('document','edition','clause','requirement')) or p['chain']['actual_condition'] not in actual_text:
                reasons.append('CHAIN_TEXT_NOT_MATCHED');linked=False
            if linked and p['quantities']:
                q=p['quantities']
                try:
                    quantity(q['actual'],p['actual_ids'],candidates,p['chain']['actual_condition'])
                    quantity(q['limit'],p['norm_ids'],candidates,p['chain']['requirement'])
                    numeric=compare_quantity(actual=q['actual']['value'].replace(',','.'),actual_unit=ALIASES.get(q['actual']['unit'],q['actual']['unit']),limit=q['limit']['value'].replace(',','.'),limit_unit=ALIASES.get(q['limit']['unit'],q['limit']['unit']),operator=q['operator'])
                except (ValueError,KeyError):
                    reasons.append('QUANTITY_BINDING_INVALID');linked=False
            if p.get('authority_review'):
                try:
                    authority_review=audit_normative_authority(NormativeAuthorityReview(**p['authority_review']))
                    reasons.extend(authority_review['reasons'])
                except (ValueError,TypeError):
                    reasons.append('NORMATIVE_AUTHORITY_REVIEW_INVALID')
            else:
                reasons.append('NORMATIVE_AUTHORITY_REVIEW_MISSING')
            if p.get('authority_source'):
                try:
                    x=p['authority_source'];candidate=candidates.get(x['candidate_id'])
                    if not candidate:raise ValueError('candidate missing')
                    f=store.get_file(candidate['file_id'])
                    if f['sha256']!=x['source_sha256'] or x['document']!=p['chain']['document'] or x['edition']!=p['chain']['edition']:
                        raise ValueError('normative source identity changed')
                    authority_source=audit_normative_source(NormativeSourceVerification(**x))
                    reasons.extend(authority_source['reasons'])
                except (ValueError,TypeError,KeyError):
                    reasons.append('NORMATIVE_SOURCE_VERIFICATION_INVALID')
            else:
                reasons.append('NORMATIVE_EDITION_NOT_VERIFIED')
            reasons.extend(['NORMATIVE_APPLICABILITY_NOT_VERIFIED','INPUT_TRUTH_NOT_VERIFIED'])
        else:
            artifacts=[]
            for b in p['bindings']:
                f=store.get_file(b['file_id'])
                artifacts.append(CalculationArtifact(b['role'],CalculationArtifactRole(b['role']),f['sha256'],'file:'+f['id']))
            checked=audit_calculation_model_intake(tuple(artifacts))
            intake=dict(status=checked.status,missing_roles=[r.value for r in checked.missing_roles])
            if checked.missing_roles:reasons.append('CALCULATION_ARTIFACT_ROLES_MISSING')
            if p.get('semantic_reviews'):
                try:
                    semantic_review=audit_calculation_semantics(tuple(
                        CalculationSemanticReview(CalculationArtifactRole(x['role']),x['statement'],tuple(x['candidate_ids']),x['decision'],x['basis'])
                        for x in p['semantic_reviews']))
                    reasons.extend(semantic_review['reasons'])
                except (ValueError,TypeError,KeyError):
                    reasons.append('CALCULATION_SEMANTIC_REVIEW_INVALID')
            else:
                reasons.append('CALCULATION_SEMANTIC_REVIEW_MISSING')
            if p.get('exchange_manifest'):
                try:
                    exchange_review=audit_exchange_manifest(parse_exchange_manifest(json.dumps(p['exchange_manifest'],ensure_ascii=False,separators=(',',':'))))
                    reasons.extend(exchange_review['reasons'])
                except (ValueError,TypeError,KeyError):
                    reasons.append('CALCULATION_EXCHANGE_MANIFEST_INVALID')
            else:
                reasons.append('CALCULATION_EXCHANGE_MANIFEST_MISSING')
            if p.get('solver_receipt'):
                try:
                    solver_review=audit_solver_receipt(SolverReceipt(**p['solver_receipt']))
                    reasons.extend(solver_review['reasons'])
                except (ValueError,TypeError,KeyError):
                    reasons.append('SOLVER_RECEIPT_INVALID')
            else:
                reasons.append('SOLVER_RECEIPT_MISSING')
            receipt=None
            if p.get('solver_receipt'):
                try:receipt=SolverReceipt(**p['solver_receipt'])
                except (ValueError,TypeError,KeyError):receipt=None
            if p.get('execution_identity') and receipt is not None:
                try:
                    execution_review=audit_execution_identity(SolverExecutionIdentity(**p['execution_identity']),receipt)
                    reasons.extend(execution_review['reasons'])
                except (ValueError,TypeError,KeyError):reasons.append('SOLVER_EXECUTION_IDENTITY_INVALID')
            else:
                reasons.append('SOLVER_EXECUTION_IDENTITY_MISSING')
            if p.get('result_verification') and receipt is not None:
                try:
                    x=p['result_verification']
                    result_review=audit_solver_results(SolverResultVerification(**dict(x,critical_findings=tuple(x['critical_findings']))),receipt)
                    reasons.extend(result_review['reasons'])
                except (ValueError,TypeError,KeyError):reasons.append('SOLVER_RESULT_VERIFICATION_INVALID')
            else:
                reasons.append('SOLVER_RESULT_VERIFICATION_MISSING')
            if p.get('structure_correlation'):
                try:
                    structure_review=audit_structure_correlation(tuple(
                        StructureCorrelationItem(x['role'],tuple(x['calculation_source_ids']),tuple(x['actual_source_ids']),x['statement'],x['basis'],x['decision'])
                        for x in p['structure_correlation']))
                    reasons.extend(structure_review['reasons'])
                except (ValueError,TypeError,KeyError):reasons.append('ACTUAL_STRUCTURE_CORRELATION_INVALID')
            else:
                reasons.append('ACTUAL_STRUCTURE_NOT_VERIFIED')
            if semantic_review is None or semantic_review['status']!='READY_FOR_SOLVER_VERIFICATION':
                reasons.append('CALCULATION_SEMANTICS_NOT_VERIFIED')
            reasons.append('SOLVER_NOT_RUN' if solver_review is None else 'SOLVER_EXECUTION_NOT_ACCEPTED')
        if p.get('data_class_reviews'):
            try:
                reviewed=[]
                for x in p['data_class_reviews']:
                    if x['candidate_id'] not in candidates or candidates[x['candidate_id']]['data_class']!=x['data_class']:
                        raise ValueError('data class changed')
                    reviewed.append(DataClassReview(**x))
                data_class_review=audit_data_classes(tuple(reviewed),tuple(dict.fromkeys(
                    list(p.get('norm_ids',[]))+list(p.get('actual_ids',[]))+
                    [eid for b in p.get('bindings',[]) for eid in b['candidate_ids']]))))
                reasons.extend(data_class_review['reasons'])
            except (ValueError,TypeError,KeyError):reasons.append('DATA_CLASS_REVIEW_INVALID')
        else:
            reasons.append('DATA_CLASS_NOT_VERIFIED')
        rows.append(dict(id=event['id'],kind=p['kind'],revision=event['revision'],packet=p,sources=sources,
            status='BLOCK',traceability='SOURCE_LINKED' if linked else 'NOT_ESTABLISHED',
            reasons=list(dict.fromkeys(reasons)),arithmetic=numeric,intake=intake,
            authority_review=authority_review,authority_source=authority_source,data_class_review=data_class_review,
            semantic_review=semantic_review,exchange_review=exchange_review,solver_review=solver_review,
            execution_review=execution_review,result_review=result_review,structure_review=structure_review,
            point6_readiness=(
                'READY_FOR_ENGINEERING_DECISION'
                if (
                    data_class_review and data_class_review['status']=='READY_FOR_DOMAIN_REVIEW' and
                    ((p['kind']=='NORMATIVE' and authority_review and authority_review['status']=='READY_FOR_EXPERT_APPLICABILITY_REVIEW' and authority_source and authority_source['status']=='READY_FOR_APPLICABILITY_REVIEW')
                     or
                     (p['kind']=='CALCULATION' and intake and intake['status']=='READY_FOR_SEMANTIC_REVIEW' and semantic_review and semantic_review['status']=='READY_FOR_SOLVER_VERIFICATION' and exchange_review and exchange_review['status']=='READY_FOR_SEMANTIC_CROSSCHECK' and solver_review and solver_review['status']=='READY_FOR_RESULT_VERIFICATION' and execution_review and execution_review['status']=='READY_FOR_RESULT_INTEGRITY_REVIEW' and result_review and result_review['status']=='READY_FOR_STRUCTURE_CORRELATION' and structure_review and structure_review['status']=='READY_FOR_ENGINEERING_REVIEW'))
                ) else 'BLOCKED_PREREQUISITES'),
            origin=event['origin'],acceptance_granted=False,engineering_verified=False))
    return dict(packets=rows,revision=state[-1]['revision'] if state else 0,status='BLOCK' if rows else 'NOT_PROVIDED',
                scope='SOURCE_BOUND_DOMAIN_INPUTS',acceptance_granted=False,final_audit='NOT_RUN')


def context(report):
    rows=[];budget=14000
    for row in report['packets']:
        cost=len(json.dumps(row,ensure_ascii=False))
        if cost>budget:break
        rows.append(row);budget-=cost
    return dict(report,packets=rows,total_packets=len(report['packets']),context_truncated=len(rows)<len(report['packets']))
