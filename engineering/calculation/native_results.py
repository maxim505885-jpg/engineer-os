"""Strict bounded observations of LIRA saved-result exports, without solver acceptance."""
import hashlib
import io
import json
import math
import re

from .native_tables import _object

KIND = 'ENGINEER_OS_LIRA_RESULTS_EXPORT'
HEADER = 'request_type subject_id load_case shape history section component value status hresult'.split()
MAX_ROWS = 200000
MAX_LINE = 4096
MAX_FILES = 40
MAX_SAMPLES = 100
METHODS = ['', 'LoadCaseDisplacements', 'LoadCaseForces', 'FragmLoads', 'PunchLoads',
           'LoadCombinationForces', 'LoadCombinationDisplacements', 'DesignCombinationForces',
           'PeriodsOfVibrations', 'SelectedReinforcement', 'MainData']
COMPONENTS = {
    1: set('GetNodeX GetNodeY GetNodeZ GetNodeUX GetNodeUY GetNodeUZ GetNodeW GetNodeT'.split()),
    2: set(('GetBarN GetBarMx GetBarMy GetBarQz GetBarMz GetBarQy GetBarRy GetBarRz GetBarBw GetBarTw '
            'GetPlateNx GetPlateNy GetPlateNz GetPlateTxy GetPlateTxz GetPlateMx GetPlateMy GetPlateMxy GetPlateQx GetPlateQy GetPlateRz '
            'GetSolidNx GetSolidNy GetSolidNz GetSolidTxy GetSolidTxz GetSolidTyz '
            'GetSpecElementN GetSpecElementNx GetSpecElementNy GetSpecElementNz GetSpecElementMx GetSpecElementMy GetSpecElementMz '
            'GetSpecElementQy GetSpecElementQz GetSpecElementRx GetSpecElementRy GetSpecElementRz GetSpecElementRux GetSpecElementRuy GetSpecElementRuz '
            'GetSpec_58_59_Qz GetSpec_58_59_Ny GetSpec_58_59_Qx GetSpec_310_N GetSpec_310_My GetSpec_310_Mx GetSpec_310_Qz GetSpec_310_Mz GetSpec_310_Qy '
            'GetSpec_264_N GetSpec_264_Qz GetSpec_264_Qy').split()),
    3: set('GetNodeRX GetNodeRY GetNodeRZ GetNodeRUX GetNodeRUY GetNodeRUZ GetNodeRBW'.split()),
    4: set('GetNodeN GetNodeMX GetNodeMY GetNodeQX GetNodeQY GetNodeMZ'.split()),
    8: set('GetFrequenciesHz GetPeriods GetFrequenciesRadPerSec GetEigenvalues GetParticipFactors GetModalMasses GetAccumulatedModalMasses'.split()),
}
_NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')
_HRESULT = re.compile(r'0x[0-9A-F]{8}')


def _count(value, maximum=50000000):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('Invalid bounded count')
    return value


def _integer(value, minimum=0):
    if not re.fullmatch(r'[0-9]{1,9}', value) or int(value) < minimum:
        raise ValueError('Invalid row identifier')
    return int(value)


def observe_native_results(payloads):
    """None means unrelated package; recognized invalid packages never fall back."""
    raw = payloads.get('manifest.json')
    if raw is None:
        return None
    invalid = dict(observations={}, reasons=['NATIVE_RESULT_PACKAGE_INVALID'], results_exported=False,
                   full_information_extracted=False, source_result_binding_verified=False,
                   completed_solver_run_verified=False, model_result_association='UNVERIFIED')
    try:
        if len(raw) > 1024 * 1024:
            raise ValueError('Manifest limit')
        manifest = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_object,
                              parse_constant=lambda value: (_ for _ in ()).throw(ValueError('JSON nonfinite')))
        if not isinstance(manifest, dict) or manifest.get('kind') != KIND:
            return None
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid if KIND.encode() in raw else None
    try:
        if type(manifest.get('schema')) is not int or manifest['schema'] != 1:
            raise ValueError('Unsupported schema')
        if manifest.get('scope') != 'PRIMARY_SHAPE0_HISTORY0_AND_REQUEST_AVAILABILITY':
            raise ValueError('Unsupported result scope')
        if manifest.get('status') not in {'BUDGET_EXHAUSTED', 'PARTIAL_RESULT_EXPORT', 'RESULT_ACCESS_UNAVAILABLE', 'NO_NUMERICAL_VALUES_EXPORTED', 'SOURCE_CHANGED'}:
            raise ValueError('Invalid export status')
        source_hash = manifest.get('source_sha256')
        if not isinstance(source_hash, str) or not re.fullmatch('[0-9a-fA-F]{64}', source_hash):
            raise ValueError('Invalid source hash')
        if manifest.get('counts_scope') != 'WHOLE_RUN_NOT_PART':
            raise ValueError('Unsupported count scope')
        claims = {key: _count(manifest.get(key)) for key in ['attempted_values', 'value_rows', 'unavailable_values']}
        if claims['attempted_values'] < claims['value_rows'] + claims['unavailable_values']:
            raise ValueError('Contradictory whole run claims')
        parts = _count(manifest.get('parts'), 100000)
        part = manifest.get('part_number')
        # Exporter emits a manifest-only diagnostic directory when no TSV was written.
        if parts and (type(part) is not int or not 1 <= part <= parts):
            raise ValueError('Invalid part number')
        if not parts and part is not None:
            raise ValueError('Unexpected diagnostic part number')
        entries = manifest.get('files')
        if not isinstance(entries, list) or len(entries) > MAX_FILES or (parts and not entries) or (not parts and entries):
            raise ValueError('Invalid file inventory')
        requests = manifest.get('requests')
        if not isinstance(requests, list) or len(requests) != 10:
            raise ValueError('Invalid request inventory')
        diagnostics = []; types = set(); request_claims = {}
        statuses = {'NOT_ATTEMPTED', 'NO_SUBJECTS', 'UNAVAILABLE', 'BUDGET_EXHAUSTED', 'AVAILABILITY_ONLY', 'PRIMARY_VALUES_PARTIAL'}
        for request in requests:
            if not isinstance(request, dict):
                raise ValueError('Invalid request')
            typ = request.get('type_id')
            if type(typ) is not int or not 1 <= typ <= 10 or typ in types or request.get('method') != METHODS[typ]:
                raise ValueError('Invalid request type/method')
            types.add(typ); status = request.get('status')
            if status not in statuses or (status == 'AVAILABILITY_ONLY' and typ in COMPONENTS) or (status == 'PRIMARY_VALUES_PARTIAL' and typ not in COMPONENTS):
                raise ValueError('Invalid request status')
            diag = dict(type_id=typ, method=METHODS[typ], status=status,
                        scope='PRIMARY_VALUES_PARTIAL' if typ in COMPONENTS else 'AVAILABILITY_ONLY')
            for key in ['attempted_values', 'value_rows', 'nodes', 'elements', 'histories']:
                if key in request: diag[key + '_whole_run_claim'] = _count(request[key])
            for key in ['error', 'reason', 'hresult']:
                if key in request:
                    if not isinstance(request[key], str) or len(request[key]) > 240:
                        raise ValueError('Invalid diagnostic')
                    diag[key] = request[key]
            if status in {'NOT_ATTEMPTED', 'NO_SUBJECTS'}:
                attempted = _count(request.get('attempted_values', 0))
                exported = _count(request.get('value_rows', 0))
                if attempted or exported:
                    raise ValueError('Unattempted request claims values')
            else:
                attempted = _count(request.get('attempted_values'))
                exported = _count(request.get('value_rows'))
            if exported > attempted:
                raise ValueError('Request exports exceed attempts')
            request_claims[typ] = (attempted, exported)
            if typ not in COMPONENTS and any(request.get(key, 0) != 0 for key in ['attempted_values', 'value_rows']):
                raise ValueError('Probe cannot export values')
            if typ == 8:
                errors = {}
                for method in COMPONENTS[8]:
                    key = method + '_error'
                    if key in request:
                        if not isinstance(request[key], str) or not _HRESULT.fullmatch(request[key]):
                            raise ValueError('Invalid period diagnostic')
                        errors[method] = request[key]
                if errors: diag['component_errors'] = errors
            diagnostics.append(diag)
        files = []; names = set(); values = unavailable = total_rows = 0
        samples = []; summaries = {}; seen = set(); request_rows = {}
        for entry in entries:
            if not isinstance(entry, dict): raise ValueError('Invalid file entry')
            name = entry.get('file')
            if not isinstance(name, str) or not re.fullmatch(r'values_[0-9]{5}\.tsv', name) or name in names or name not in payloads:
                raise ValueError('Invalid result filename')
            names.add(name); data = payloads[name]; digest = hashlib.sha256(data).hexdigest()
            if type(entry.get('bytes')) is not int or entry['bytes'] != len(data) or entry.get('sha256') != digest:
                raise ValueError('Result hash/size mismatch')
            expected_rows = _count(entry.get('rows'), 50000)
            if not expected_rows: raise ValueError('Empty value file')
            file_values = file_unavailable = rows = 0
            with io.TextIOWrapper(io.BytesIO(data), encoding='utf-8-sig', newline='') as stream:
                header = stream.readline(MAX_LINE + 1)
                if not header.endswith('\n') or header.rstrip('\r\n').split('\t') != HEADER:
                    raise ValueError('Invalid TSV header')
                while True:
                    line = stream.readline(MAX_LINE + 1)
                    if not line: break
                    if len(line) > MAX_LINE or not line.endswith('\n') or '\x00' in line or total_rows >= MAX_ROWS:
                        raise ValueError('TSV framing/limit')
                    row = line.rstrip('\r\n').split('\t')
                    if len(row) != 10 or any('\r' in cell or '\n' in cell for cell in row):
                        raise ValueError('Invalid TSV columns')
                    typ = _integer(row[0], 1)
                    if typ not in COMPONENTS or typ not in types or row[6] not in COMPONENTS[typ]:
                        raise ValueError('Unknown numerical request/component')
                    ident = _integer(row[1], 0 if typ == 8 else 1); lc = _integer(row[2], 1)
                    shape = _integer(row[3]); history = _integer(row[4]); section = _integer(row[5])
                    if shape or history or (typ == 2 and not 1 <= section <= 1000) or (typ != 2 and section):
                        raise ValueError('Unsupported result context')
                    key = (typ, ident, lc, shape, history, section, row[6])
                    if key in seen: raise ValueError('Duplicate result coordinate')
                    seen.add(key)
                    label = f'{typ}:{row[6]}'
                    summary = summaries.setdefault(label, dict(request_type=typ, component=row[6], value_rows=0, unavailable_rows=0, minimum=None, maximum=None))
                    if row[8] == 'EXPORTED':
                        if row[9] or not _NUMBER.fullmatch(row[7]): raise ValueError('Invalid exported value')
                        value = float(row[7])
                        if not math.isfinite(value): raise ValueError('Nonfinite result')
                        values += 1; file_values += 1; summary['value_rows'] += 1
                        summary['minimum'] = value if summary['minimum'] is None else min(summary['minimum'], value)
                        summary['maximum'] = value if summary['maximum'] is None else max(summary['maximum'], value)
                        if len(samples) < MAX_SAMPLES:
                            samples.append(dict(zip(HEADER[:7], [typ, ident, lc, shape, history, section, row[6]]), value=value))
                    elif row[8] == 'UNAVAILABLE' and not row[7] and _HRESULT.fullmatch(row[9]):
                        unavailable += 1; file_unavailable += 1; summary['unavailable_rows'] += 1
                    else: raise ValueError('Invalid unavailable diagnostic')
                    observed = request_rows.setdefault(typ, [0, 0])
                    observed[0 if row[8] == 'EXPORTED' else 1] += 1
                    total_rows += 1; rows += 1
                    if rows > expected_rows: raise ValueError('Too many rows')
            if rows != expected_rows: raise ValueError('Manifest row mismatch')
            files.append(dict(file=name, bytes=len(data), sha256=digest, rows=rows,
                              part_value_rows=file_values, part_unavailable_rows=file_unavailable))
        if set(payloads) - names - {'manifest.json', 'api-contract.json'}:
            raise ValueError('Unexpected package member')
        if values > claims['value_rows'] or unavailable > claims['unavailable_values']:
            raise ValueError('Part exceeds whole-run claims')
        for typ, (observed_values, observed_unavailable) in request_rows.items():
            attempted, exported = request_claims[typ]
            # UNAVAILABLE may follow earlier successful chunks. Its counters, not
            # its final status alone, bound the values already written by exporter.
            if observed_values > exported or observed_unavailable > attempted - exported:
                raise ValueError('Part exceeds request whole-run claims')
        obs = dict(part_number=part, part_value_rows=values, part_unavailable_rows=unavailable,
                   result_values_available=values > 0, value_samples=samples,
                   value_samples_omitted=max(0, values-len(samples)), component_summaries=list(summaries.values()),
                   files=files, request_diagnostics=diagnostics, file_hashes_verified=bool(files),
                   original_source_sha256_claim=source_hash, original_source_hash_verified=False,
                   model_result_association='UNVERIFIED', whole_run_parts_claim=parts,
                   whole_run_status_claim=manifest.get('status'))
        obs.update({'whole_run_' + key + '_claim': value for key, value in claims.items()})
        reasons = ['PRIMARY_RESULT_COVERAGE_ONLY', 'MODEL_RESULT_ASSOCIATION_UNVERIFIED',
                   'COMPLETED_SOLVER_RUN_NOT_VERIFIED', 'ENGINEERING_ACCEPTANCE_NOT_GRANTED']
        if not values: reasons.append('NO_NUMERICAL_VALUES_EXPORTED')
        if unavailable: reasons.append('RESULT_VALUES_UNAVAILABLE')
        return dict(observations=obs, reasons=reasons, results_exported=values > 0,
                    full_information_extracted=False, source_result_binding_verified=False,
                    completed_solver_run_verified=False, model_result_association='UNVERIFIED')
    except (ValueError, TypeError, KeyError, OverflowError, UnicodeDecodeError, RecursionError):
        return invalid
