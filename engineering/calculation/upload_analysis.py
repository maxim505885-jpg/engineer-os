"""Source-hashed, bounded observations of LIRA exports; never engineering acceptance."""
import configparser
import hashlib
import io
from itertools import islice
import math
from pathlib import Path, PurePosixPath
import re
import struct
import zipfile
import zlib
from xml.etree import ElementTree as ET

MAX_BYTES = 100 * 1024 * 1024
MAX_MEMBERS = 64
MAX_EXPANDED = 100 * 1024 * 1024
_HEADER = re.compile(r'\(\s*(\d+)\s*/')


class RejectDTD(ET.TreeBuilder):
    """Parser-level rejection also covers Expat's encoding autodetection."""

    def doctype(self, name, pubid, system):
        raise ValueError('XML DTD forbidden')


def _base(data, kind):
    return dict(schema=1, kind=kind, source_sha256=hashlib.sha256(data).hexdigest(),
                scope='SOURCE_OBSERVATIONS_ONLY', status='BLOCK', observations={}, reasons=[],
                solver_execution='NOT_RUN_BY_ENGINEER_OS', acceptance_granted=False,
                engineering_verified=False)


def analyze_upload(name, data):
    """Return observations only for recognizable content or explicit vendor suffixes."""
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        raise ValueError('Calculation original exceeds byte limit')
    suffix = Path(name).suffix.lower()
    if suffix == '.zip':
        return _archive(data)
    if suffix == '.lir':
        from .native_source import inspect_lir
        report = _base(data, 'LIRA_BINARY_IDENTITY')
        report['observations'] = inspect_lir(data)
        report['reasons'] = report['observations']['reasons']
        return report
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        if suffix not in {'.ald', '.cop', '.log'}:
            return None
        report = _base(data, 'UNREADABLE_VENDOR_EXPORT')
        report['reasons'] = ['UTF8_REQUIRED']
        return report
    if 'Протокол расчета' in text[:1024] or 'Протокол расчёта' in text[:1024]:
        report = _base(data, 'LIRA_SOLVER_LOG')
        report['solver_execution'] = 'INTERRUPTED_BY_USER' if re.search(r'Расч[её]т прерван пользователем', text, re.I) else 'NOT_CONFIRMED'
        for label, pattern in [('nodes', r'Количество узлов\s*=\s*(\d+)'), ('elements', r'Количество элементов\s*=\s*(\d+)'), ('solver_version', r'FESolver\.exe\s+([\d.]+)')]:
            match = re.search(pattern, text)
            if match: report['observations'][label] = int(match[1]) if label != 'solver_version' else match[1]
        report['reasons'] = ['FULL_RUN_NOT_CONFIRMED', 'RESULTS_REQUIRED', 'INPUT_RUN_BINDING_NOT_VERIFIED']
        return report
    if suffix == '.ald':
        report = _base(data, 'LIRA_XML_METADATA')
        if '\x00' in text:
            report['reasons'] = ['XML_ENCODING_UNSUPPORTED']; return report
        # No DTD/entities, even when the standard parser would accept them.
        if re.search(r'<!\s*(DOCTYPE|ENTITY)', text, re.I):
            report['reasons'] = ['XML_DECLARATIONS_NOT_ALLOWED']; return report
        try:
            root = ET.fromstring(text, parser=ET.XMLParser(target=RejectDTD()))
            if root.tag != 'LIRA_Project': raise ValueError('Unknown root')
            report['observations'] = dict(title=root.get('Title', '')[:240],
                rigid_metadata_records=sum(1 for _ in root.iter('Rigid')),
                element_block_metadata_records=sum(1 for _ in root.iter('ElemBlock')),
                dynamic_metadata_records=sum(1 for _ in root.iter('DynTableLine')))
            report['reasons'] = ['METADATA_NOT_MODEL_SEMANTICS', 'RESULTS_REQUIRED']
        except (ET.ParseError, ValueError): report['reasons'] = ['INVALID_LIRA_XML']
        return report
    if suffix == '.cop':
        report = _base(data, 'LIRA_PILE_CAPACITY')
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        try:
            parser.read_string(text)
            sections = []
            for section in parser.sections():
                values = []
                for key, raw in parser[section].items():
                    if not key.isdigit(): raise ValueError('Noninteger pile reference')
                    value = float(raw)
                    if not math.isfinite(value) or value <= 0: raise ValueError('Invalid capacity')
                    values.append(value)
                sections.append(dict(name=section[:200], records=len(values), minimum=min(values) if values else None, maximum=max(values) if values else None))
            if not sections: raise ValueError('Missing tables')
            report['observations'] = dict(sections=sections[:16], sections_omitted=max(0,len(sections)-16), units='NOT_VERIFIED')
            report['reasons'] = ['CAPACITY_METHOD_NOT_VERIFIED', 'ACTUAL_PILE_FORCES_NOT_PROVIDED']
        except (configparser.Error, ValueError): report['reasons'] = ['INVALID_CAPACITY_TABLE']
        return report
    if re.match(r'^\s*\(\s*0\s*/', text) and _HEADER.search(text) and re.search(r'\(\s*4\s*/', text):
        return _model(data, text)
    return None


def _model(data, text):
    report = _base(data, 'LIRA_TEXT_MODEL')
    headers = list(islice(_HEADER.finditer(text), 257))
    if len(headers)>256:
        report['reasons'] = ['DOCUMENT_INVENTORY_LIMIT']; return report
    docs = {}
    valid = not text[:headers[0].start()].strip()
    for i, header in enumerate(headers):
        body = text[header.end():headers[i+1].start() if i+1<len(headers) else len(text)].strip()
        if len(header[1]) > 8:
            valid = False; break
        ident = int(header[1])
        if ident in docs or not body.endswith(')') or '(' in body or ')' in body[:-1]:
            valid = False; break
        docs[ident] = body[:-1]
    if not valid or '\x00' in text:
        report['reasons'] = ['INVALID_DOCUMENT_FRAMING']; return report
    def records(ident):
        for raw in docs.get(ident, '').split('/'):
            if raw.strip(): yield raw.split()
    try:
        count = 0
        for row in records(4):
            if len(row)!=3 or any(not math.isfinite(float(v)) for v in row): raise ValueError('Invalid coordinate')
            count += 1
        stiffness = {int(row[0]) for row in records(3) if row[0].isdigit() and int(row[0])>0}
        elements = invalid_nodes = invalid_rigid = repeated_nodes = 0
        types = {}
        for row in records(1):
            if len(row)<3: raise ValueError('Invalid element record')
            values = [int(v) for v in row]
            elements += 1
            types[str(values[0])] = types.get(str(values[0]), 0)+1
            invalid_nodes += sum(not 1<=v<=count for v in values[2:])
            invalid_rigid += values[1] not in stiffness
            repeated_nodes += len(set(values[2:]))!=len(values[2:])
        report['observations'] = dict(nodes=count, elements=elements, document_ids=sorted(docs),
            element_types=dict(sorted(types.items())[:100]), element_types_omitted=max(0,len(types)-100), invalid_node_references=invalid_nodes,
            missing_stiffness_references=invalid_rigid, elements_with_repeated_nodes=repeated_nodes,
            node_reference_convention='DOCUMENT4_RECORD_ORDINAL_NOT_VENDOR_QUALIFIED',
            load_records=sum(1 for _ in records(6)), load_value_records=sum(1 for _ in records(7)))
        report['reasons'] = ['VENDOR_GRAMMAR_NOT_QUALIFIED', 'MODEL_SEMANTICS_NOT_VERIFIED',
            'SOLVER_LOG_REQUIRED', 'RESULTS_REQUIRED', 'ACTUAL_STRUCTURE_REFERENCE_REQUIRED']
        if invalid_nodes or invalid_rigid or repeated_nodes:
            report['reasons'].append('LITERAL_REFERENCE_DISCREPANCIES')
    except (ValueError, OverflowError): report['reasons'] = ['INVALID_NUMERIC_RECORD']
    return report


def _archive(data):
    report = _base(data, 'LIRA_EXPORT_PACKAGE'); report['members'] = []
    # Bound the central directory before ZipFile allocates entries. No ZIP64.
    offset = data.rfind(b'PK\x05\x06', max(0,len(data)-65557))
    try:
        fields = struct.unpack('<4s4H2LH', data[offset:offset+22]) if offset>=0 and len(data[offset:offset+22])==22 else None
        if not fields or fields[1]!=0 or fields[2]!=0 or fields[3]!=fields[4] or fields[4]>MAX_MEMBERS or fields[5]>65536 or data[max(0,offset-20):offset-16]==b'PK\x06\x07':
            report['reasons'] = ['ARCHIVE_INVENTORY_LIMIT_OR_INVALID']; return report
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist(); names = set(); total = 0
            if len(entries) != fields[4] or len(entries) > MAX_MEMBERS:
                report['reasons'] = ['ARCHIVE_INVENTORY_LIMIT_OR_INVALID']; return report
            for info in entries:
                name = info.filename.replace('\\', '/')
                path = PurePosixPath(name)
                if path.is_absolute() or '..' in path.parts or ':' in name or ((info.external_attr>>16)&0o170000)==0o120000:
                    report['reasons'] = ['UNSAFE_ARCHIVE_MEMBER']; return report
                if name in names or len(name)>240: raise ValueError('Duplicate or long member')
                names.add(name); total += info.file_size
                if info.flag_bits & 1 or total>MAX_EXPANDED or info.file_size>MAX_BYTES:
                    report['reasons'] = ['ARCHIVE_EXPANSION_LIMIT_OR_ENCRYPTED']; return report
            for info in entries:
                if info.is_dir(): continue
                with archive.open(info) as stream: member = stream.read(info.file_size+1)
                if len(member)!=info.file_size: raise ValueError('Member size mismatch')
                if not member or Path(info.filename).suffix.lower()=='.zip':
                    analysis = None  # Never recurse into packages.
                else: analysis = analyze_upload(info.filename, member)
                report['members'].append(dict(name=info.filename,source_sha256=hashlib.sha256(member).hexdigest(),
                    bytes=len(member),report=analysis, status='OBSERVATIONS_RECORDED' if analysis else 'NOT_ANALYZED'))
        report['observations'] = dict(member_count=len(report['members']), expanded_bytes=total)
        report['reasons'] = ['PACKAGE_LINKAGE_NOT_VERIFIED', 'ENGINEERING_ACCEPTANCE_NOT_GRANTED']
    except (zipfile.BadZipFile, RuntimeError, ValueError, NotImplementedError, OSError, zlib.error, EOFError):
        report['members'] = []; report['reasons'] = ['ARCHIVE_UNREADABLE']
    return report


def report_note(report):
    kind = report['kind']; obs = report['observations']
    if kind == 'LIRA_TEXT_MODEL':
        message = f"ЛИРА: разобран полный текстовый источник. Узлов: {obs.get('nodes', 'не определено')}; КЭ: {obs.get('elements', 'не определено')}. Ссылок вне диапазона: {obs.get('invalid_node_references', 'не определено')}."
    elif kind == 'LIRA_SOLVER_LOG':
        message = 'ЛИРА: журнал прочитан. '+('Расчёт прерван пользователем.' if report['solver_execution']=='INTERRUPTED_BY_USER' else 'Завершение полного расчёта не подтверждено.')
    elif kind == 'LIRA_EXPORT_PACKAGE':
        message = f"Комплект ЛИРА: просмотрено файлов {len(report['members'])}; распознано {sum(m['report'] is not None for m in report['members'])}."
    else: message = 'ЛИРА: записаны наблюдения источника '+kind+'.'
    return message+' Инженерная корректность и принятие не подтверждены.'
