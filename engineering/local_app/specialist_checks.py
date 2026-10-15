"""Deterministic disclosure of domain prerequisites in the local draft path.

No artifact roles, verified norms or solver receipts are inferred from prose,
file names, a model response, or user-declared source confirmation.
"""
from engineering.calculation.model_intake import audit_calculation_model_intake


def report(job,domain_report=None):
    checks=[]
    if 'normative' in job['requested_checks']:
        checks.append(dict(agent='normative-agent',label='Нормативная проверка',status='BLOCK',
            scope='PREREQUISITES_ONLY',execution='NOT_VERIFIED',reasons=[
                'NORMATIVE_DOCUMENT_NOT_VERIFIED','NORMATIVE_EDITION_NOT_VERIFIED',
                'NORMATIVE_SCOPE_NOT_VERIFIED','NORMATIVE_CLAUSE_NOT_VERIFIED',
                'ACTUAL_CONDITION_NOT_VERIFIED','NORMATIVE_COMPARISON_NOT_VERIFIED'],
            note='Цитата и заполненная цепочка не подтверждают редакцию, применимость и сопоставление нормы с фактом.'))
    if 'calculation' in job['requested_checks']:
        intake=audit_calculation_model_intake(())
        checks.append(dict(agent='calculation-agent',label='Проверка расчёта',status='BLOCK',
            scope='PREREQUISITES_ONLY',execution='NOT_VERIFIED',
            missing_roles=[r.value for r in intake.missing_roles],
            reasons=['CALCULATION_ARTIFACT_ROLES_NOT_BOUND','CALCULATION_SEMANTICS_NOT_VERIFIED','SOLVER_NOT_RUN'],
            solver_execution='NOT_RUN',solver_access='NOT_CONFIGURED',
            note='Комплект с назначенными ролями, семантические проверки и протокол решателя в локальный маршрут ещё не подключены. Файл или ответ модели не подтверждает расчёт.'))
    for check in checks:
        kind='NORMATIVE' if check['agent']=='normative-agent' else 'CALCULATION'
        packet=next((p for p in (domain_report or {}).get('packets',[]) if p['kind']==kind),None)
        if packet:
            check.update(packet_id=packet['id'],packet_revision=packet['revision'],traceability=packet['traceability'],
                         reasons=packet['reasons'],arithmetic=packet['arithmetic'],scope='SOURCE_BOUND_INPUT_CHECK')
            if packet['intake']:check.update(missing_roles=packet['intake']['missing_roles'],intake_status=packet['intake']['status'],note='Роли назначены пользователем. Семантика модели, соответствие реальной конструкции и выполнение решателя не подтверждены.')
    return dict(status='BLOCK' if checks else 'NOT_REQUESTED',checks=checks,
                scope='DOMAIN_PREREQUISITES_ONLY',acceptance_granted=False,final_audit='NOT_RUN')
