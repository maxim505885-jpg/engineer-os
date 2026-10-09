"""Bounded observations of default LIRA input table exports, without acceptance."""
import hashlib
import json
import math
import re

KIND = 'ENGINEER_OS_LIRA_MODEL_TABLE_EXPORT'
MAX_ROWS = 200000


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key')
        value[key] = item
    return value


def _positive(value):
    if not re.fullmatch(r'[0-9]{1,9}', value) or int(value) < 1:
        raise ValueError('Invalid positive identifier')
    return int(value)


def _rows(data):
    text = data.decode('utf-8-sig')
    if '\x00' in text:
        raise ValueError('NUL in TSV')
    rows = text.splitlines()
    if len(rows) > MAX_ROWS:
        raise ValueError('Table row limit')
    return [row.split('\t') for row in rows]


def _indexed(rows, minimum):
    result = {}
    for row in rows:
        if len(row) < minimum:
            raise ValueError('Truncated table row')
        ident = _positive(row[0])
        if ident in result:
            raise ValueError('Duplicate table identifier')
        result[ident] = row
    return result


def observe_native_package(payloads):
    """Return None for generic packages; invalid native packages produce no counts."""
    raw = payloads.get('manifest.json')
    if raw is None:
        return None
    try:
        if len(raw) > 1024 * 1024:
            raise ValueError('Manifest limit')
        manifest = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_object)
        if not isinstance(manifest, dict) or manifest.get('kind') != KIND:
            return None
    except (ValueError, UnicodeDecodeError, RecursionError):
        if KIND.encode() not in raw:
            return None
        return dict(observations={}, reasons=['NATIVE_PACKAGE_INVALID'])
    try:
        if type(manifest.get('schema')) is not int or manifest['schema'] != 2:
            raise ValueError('Unsupported schema')
        source_hash = manifest.get('source_sha256')
        if not isinstance(source_hash, str) or not re.fullmatch('[0-9a-f]{64}', source_hash):
            raise ValueError('Invalid source hash')
        entries = manifest.get('tables')
        if not isinstance(entries, list) or not 1 <= len(entries) <= 31:
            raise ValueError('Invalid table inventory')
        tables = {}; inventory = []; failed = []; unavailable = []; seen = set(); files = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError('Invalid table metadata')
            ident = entry.get('type_id')
            if type(ident) is not int or not 2 <= ident <= 32 or ident in seen:
                raise ValueError('Invalid/duplicate type')
            seen.add(ident)
            if type(entry.get('model_part')) is not int or entry['model_part'] != 0:
                raise ValueError('Unsupported table scope')
            if entry.get('status') == 'FAILED':
                failed.append(ident)
                continue
            if entry.get('status') != 'EXPORTED':
                raise ValueError('Invalid table status')
            filename = entry.get('file')
            if filename != f'table_{ident:02}.tsv' or filename in files or filename not in payloads:
                raise ValueError('Missing or invalid table file')
            files.add(filename)
            data = payloads[filename]
            digest = hashlib.sha256(data).hexdigest()
            if type(entry.get('bytes')) is not int or entry['bytes'] != len(data) or entry.get('sha256') != digest:
                raise ValueError('Table hash/size mismatch')
            rows = _rows(data); tables[ident] = rows
            inventory.append(dict(type_id=ident, rows=len(rows), bytes=len(data), sha256=digest,
                nonblank_rows=sum(any(cell.strip() for cell in row) for row in rows)))
            if entry.get('parameter_status') != 'READ':
                unavailable.append(ident)
        if any(name.endswith('.tsv') and name not in files for name in payloads):
            raise ValueError('Unlisted table file')
        obs = dict(table_hashes_verified=bool(tables), exported_table_count=len(tables),
            tables=inventory, failed_table_types=sorted(failed),
            empty_table_types=sorted(i for i, rows in tables.items() if not rows),
            parameter_unavailable_types=sorted(unavailable),
            original_source_sha256_claim=source_hash, original_source_hash_verified=False)
        units = manifest.get('units')
        if isinstance(units, dict):
            obs['application_unit_codes_claim'] = {k:v for k,v in units.items()
                if len(k)<=64 and type(v) is int and 0<=v<=100}
        nodes = elements = stiffnesses = assignments = None
        if 2 in tables:
            nodes = {}
            for ident, row in _indexed(tables[2], 4).items():
                coordinates = [float(v.replace(',', '.')) for v in row[1:4]]
                if not all(math.isfinite(v) for v in coordinates):
                    raise ValueError('Nonfinite coordinate')
                nodes[ident] = coordinates
            obs['nodes'] = len(nodes)
            obs['node_bounds'] = {axis: [min(v[i] for v in nodes.values()), max(v[i] for v in nodes.values())]
                for i, axis in enumerate('XYZ')} if nodes else {}
        if 3 in tables:
            elements = {}; counts = {}
            for ident, row in _indexed(tables[3], 3).items():
                typ = _positive(row[1])
                if not re.fullmatch(r'[0-9]{1,9}(?:\s*,\s*[0-9]{1,9})*', row[2]):
                    raise ValueError('Invalid connectivity')
                refs = [_positive(v.strip()) for v in row[2].split(',')]
                elements[ident] = (typ, refs)
                counts[str(typ)] = counts.get(str(typ), 0) + 1
                if len(counts) > 100:
                    raise ValueError('Element type inventory limit')
            obs.update(elements=len(elements), element_types=counts)
            if nodes is not None:
                obs['invalid_node_references'] = sum(n not in nodes for _, refs in elements.values() for n in refs)
        if 9 in tables:
            stiffnesses = _indexed(tables[9], 2)
            obs['ordinary_stiffnesses'] = len(stiffnesses)
        if 10 in tables:
            assignments = {}
            for ident, row in _indexed(tables[10], 2).items():
                if not re.fullmatch(r'[0-9]{1,9}', row[1]):
                    raise ValueError('Invalid stiffness assignment')
                assignments[ident] = int(row[1])
        if elements is not None and assignments is not None and stiffnesses is not None:
            ordinary = special = 0
            for ident, (typ, _) in elements.items():
                if ident in assignments and assignments[ident] not in stiffnesses:
                    if typ == 57 and assignments[ident] == 0:
                        special += 1
                    else:
                        ordinary += 1
            obs.update(ke57_auxiliary_stiffness_not_extracted=special,
                ordinary_stiffness_references_not_in_table=ordinary,
                assignment_ids_equal_element_ids=set(elements)==set(assignments))
        if 25 in tables:
            loads = _indexed(tables[25], 2)
            obs.update(load_cases=len(loads), load_case_names=[dict(id=i, name=r[1][:240])
                for i, r in list(loads.items())[:100]], load_case_names_omitted=max(0,len(loads)-100))
        for ident, label in [(11,'rigid_bodies'),(13,'coupled_dof_groups'),(29,'construction_axes'),
                             (30,'elevation_marks'),(31,'structural_blocks')]:
            if ident in tables:
                obs[label] = sum(any(cell.strip() for cell in row) for row in tables[ident])
        reasons = ['DEFAULT_TABLE_COVERAGE_ONLY', 'ORIGINAL_SOURCE_BINDING_NOT_VERIFIED',
            'COMPLETE_LOADS_AND_COMBINATIONS_REQUIRED', 'RESULTS_REQUIRED', 'ENGINEERING_ACCEPTANCE_NOT_GRANTED']
        if failed: reasons.append('TABLE_EXPORT_INCOMPLETE')
        if unavailable: reasons.append('TABLE_PARAMETERS_UNAVAILABLE')
        if obs.get('ke57_auxiliary_stiffness_not_extracted'): reasons.append('KE57_AUXILIARY_STIFFNESS_NOT_EXTRACTED')
        if obs.get('invalid_node_references') or obs.get('ordinary_stiffness_references_not_in_table') or obs.get('assignment_ids_equal_element_ids') is False:
            reasons.append('LITERAL_REFERENCE_DISCREPANCIES')
        return dict(observations=obs, reasons=reasons)
    except (ValueError, TypeError, KeyError, OverflowError, UnicodeDecodeError, RecursionError):
        return dict(observations={}, reasons=['NATIVE_PACKAGE_INVALID'])
