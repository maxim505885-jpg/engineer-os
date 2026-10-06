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
        if set(packet) not in ({'kind','chain','norm_ids','actual_ids','quantities'},{'kind','chain','norm_ids','actual_ids','quantities','authority_review'}):raise ValueError('Invalid normative packet fields')
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
    elif kind=='CALCULATION':
        if set(packet) not in ({'kind','bindings'},{'kind','bindings','semantic_reviews'}) or not isinstance(packet['bindings'],list) or not 1<=len(packet['bindings'])<=9:raise ValueError('Select at most nine calculation roles')
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
    else:raise ValueError('Unknown domain packet kind')
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
        p=event['packet'];sources=[];reasons=[];authority_review=None;semantic_review=None
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
            reasons.extend(['NORMATIVE_APPLICABILITY_NOT_VERIFIED','NORMATIVE_EDITION_NOT_VERIFIED','DATA_CLASS_NOT_VERIFIED','INPUT_TRUTH_NOT_VERIFIED'])
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
            reasons.extend(['CALCULATION_SEMANTICS_NOT_VERIFIED','SOLVER_NOT_RUN','ACTUAL_STRUCTURE_NOT_VERIFIED'])
        rows.append(dict(id=event['id'],kind=p['kind'],revision=event['revision'],packet=p,sources=sources,
            status='BLOCK',traceability='SOURCE_LINKED' if linked else 'NOT_ESTABLISHED',
            reasons=list(dict.fromkeys(reasons)),arithmetic=numeric,intake=intake,authority_review=authority_review,semantic_review=semantic_review,
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
