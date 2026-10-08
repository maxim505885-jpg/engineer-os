"""Reproducible preliminary requirement/role/source reconciliation; never acceptance."""
from .analysis_identity import digest


def report(requirements,records):
    rows=[];global_reasons=[];unmapped=[]
    declared={r['id'] for r in requirements['requirements']}
    for role in records:
        if role.get('intermediate_gates'):global_reasons.append('INTERMEDIATE_ANALYSIS_BLOCKED')
        if role.get('intermediate_gates_omitted'):global_reasons.append('INTERMEDIATE_GATE_DETAILS_TRUNCATED')
        for index,finding in enumerate(role.get('findings',[])):
            if not finding.get('requirement_ids'):
                unmapped.append(dict(agent=role['agent'],finding=index,text=finding['text']))
            elif any(rid not in declared for rid in finding['requirement_ids']):
                global_reasons.append('UNKNOWN_REQUIREMENT_REFERENCE')
    if unmapped:global_reasons.append('OBSERVATION_NOT_TZ_BOUND')
    for requirement in requirements['requirements']:
        observations=[];relations=set();addressed=False;reasons=[]
        if requirement['status']=='BLOCK':reasons.extend(requirement['reasons'])
        for role in records:
            for intermediate in role.get('intermediate_gates',[]):
                if requirement['id'] in intermediate['requirement_ids']:reasons.extend(intermediate['reasons'])
            gates=role.get('finding_gates',[])
            for index,finding in enumerate(role.get('findings',[])):
                if requirement['id'] not in finding.get('requirement_ids',[]):continue
                gate=gates[index] if index<len(gates) else dict(status='BLOCK',traceability='NOT_ESTABLISHED',sources=[],reasons=['FINDING_SOURCE_GATE_MISSING'])
                relation=finding.get('relation','UNKNOWN');relations.add(relation)
                if role['agent']!='final-audit-agent' and role['execution']=='COMPLETED':addressed=True
                observations.append(dict(agent=role['agent'],execution=role['execution'],finding=index,text=finding['text'],
                    relation=relation,source_ids=finding['source_ids'],sources=[{k:s.get(k) for k in ('candidate_id','file_id','source_sha256','review_event_id','review_revision','data_class','reviewer')} for s in gate['sources']],traceability=gate['traceability']))
                if gate['status']=='BLOCK':reasons.extend(gate['reasons'])
                if role['execution']!='COMPLETED':reasons.append('ROLE_EXECUTION_INCOMPLETE')
                if role['status'] in {'ERROR','BLOCK'}:reasons.append('ROLE_RESULT_BLOCKED')
        if not addressed:reasons.append('REQUIREMENT_NOT_ADDRESSED')
        if 'CONTRADICTS' in relations:reasons.append('ROLE_DECLARED_CONTRADICTION')
        if 'UNKNOWN' in relations:reasons.append('ROLE_RELATION_UNKNOWN')
        if len(relations)>1:reasons.append('ROLE_RELATION_CONFLICT')
        rows.append(dict(id=requirement['id'],text=requirement['text'],status='BLOCK' if reasons else 'UNCERTAINTY',
            traceability='SOURCE_LINKED' if observations and not reasons else 'NOT_ESTABLISHED',
            assessment_revision=requirement['revision'],assessment_conclusion=requirement['conclusion'],
            observations=observations,reasons=list(dict.fromkeys(reasons)) or ['ENGINEERING_VERIFICATION_REQUIRED','DATA_CLASS_NOT_VERIFIED'],
            engineering_verified=False,acceptance_granted=False))
    if not rows:global_reasons.extend(requirements.get('reasons',[]) or ['TZ_REQUIREMENTS_MISSING'])
    result=dict(set_id=requirements['set_id'],scope='PRELIMINARY_REQUIREMENT_ROLE_RECONCILIATION',
        status='BLOCK' if global_reasons or any(r['status']=='BLOCK' for r in rows) else 'UNCERTAINTY',
        requirements=rows,requirements_total=len(rows),unmapped_observations=unmapped,
        reasons=list(dict.fromkeys(global_reasons)),engineering_verified=False,acceptance_granted=False,final_audit='NOT_RUN')
    result['snapshot_sha256']=digest(dict(requirements=requirements,records=records,result=result))
    return result
