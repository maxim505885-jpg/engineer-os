"""Stage 13 separates software readiness from per-document evidence qualification.

Fail closed: unknown/unexecuted tests cannot certify module acceptance.
"""
import json
from pathlib import Path

MODULE_REQUIRED = (
    'pdf_ingestion',
    'docx_ingestion',
    'native_text_extraction',
    'table_source_mapping',
    'drawing_ocr_failure_handling',
    'formula_media_preservation',
    'source_identity',
    'uncertainty_isolation',
    'integration_regression',
)
DOCUMENT_REQUIRED = (
    'complete_scope',
    'table_cells_validated',
    'vector_labels_validated',
    'formulas_visually_validated',
    'embedded_graphics_validated',
    'source_provenance_complete',
)


def evaluate(checks, required, evidence=None):
    evidence = evidence or {}
    missing = [key for key in required if key not in checks]
    failed = [key for key in required if checks.get(key) != 'PASS' or not isinstance(evidence.get(key), str) or not evidence[key].strip()]
    return {
        'status': 'ACCEPTED' if not failed else 'BLOCK',
        'required': list(required),
        'missing': missing,
        'not_passed': failed,
        'results': {key: checks.get(key, 'NOT_RUN') for key in required},
        'missing_evidence': [key for key in required if not isinstance(evidence.get(key), str) or not evidence[key].strip()],
    }


def audit(module_checks, document_checks, module_evidence=None, document_evidence=None):
    module = evaluate(module_checks, MODULE_REQUIRED, module_evidence)
    document = evaluate(document_checks, DOCUMENT_REQUIRED, document_evidence)
    return {
        'schema': 'ENGINEER_OS_STAGE13_TWO_LEVEL_ACCEPTANCE_V1',
        'module': module,
        'document': document,
        'document_status_independent_from_module': True,
        'evidence_required_for_each_pass': True,
        'overall_status': 'ACCEPTED' if module['status']=='ACCEPTED' and document['status']=='ACCEPTED' else 'BLOCK',
    }


def write_audit(path, module_checks, document_checks, module_evidence=None, document_evidence=None):
    report = audit(module_checks, document_checks, module_evidence, document_evidence)
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report
