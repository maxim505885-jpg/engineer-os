"""Recheck declared table-recovery candidates against original PDF text regions.

This is a local audit, not automatic recovery, evidence persistence or acceptance.
CLI uses optional PyMuPDF; the core verifier has no third-party dependencies.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def normalize(text):
    return ' '.join(text.split())


def verify_grids(manifest, fragment):
    """Check declared physical cells, including spans; no visual or semantic acceptance."""
    require(manifest.get('status') == 'UNCERTAINTY'
            and manifest.get('evidentiary_status') == 'NOT_EVIDENCE'
            and manifest.get('acceptance_granted') is False, 'candidate must remain unaccepted')
    tables = manifest.get('tables')
    require(isinstance(tables, list) and bool(tables), 'no recovery grids')
    ids, pages, count, slots = set(), set(), 0, 0
    for table in tables:
        require(isinstance(table, dict), 'invalid grid table')
        identity = table.get('table_id')
        require(isinstance(identity, str) and identity.strip() and identity not in ids,
                'duplicate or missing table ID')
        ids.add(identity)
        axes = [table.get('x_boundaries'), table.get('y_boundaries')]
        for axis in axes:
            require(isinstance(axis, list) and 2 <= len(axis) <= 10000 and all(
                type(v) in (int, float) and math.isfinite(v) for v in axis)
                and all(a < b for a, b in zip(axis, axis[1:])), 'invalid grid boundaries')
        x, y = axes
        require((len(x)-1)*(len(y)-1) <= 100000, 'grid exceeds audit size limit')
        require(type(table.get('source_page')) is int and any(
            f['source_page'] == table['source_page'] for f in manifest['context_fragments']),
            'missing source grid context')
        cells = table.get('cells')
        require(isinstance(cells, list) and bool(cells), 'missing grid cells')
        occupied, cell_ids = set(), set()
        for cell in cells:
            require(isinstance(cell, dict), 'invalid grid cell')
            identity = cell.get('cell_id')
            require(isinstance(identity, str) and identity.strip() and identity not in cell_ids,
                    'duplicate or missing cell ID')
            cell_ids.add(identity)
            span = [cell.get(k) for k in ('row_start','row_end','col_start','col_end')]
            require(all(type(v) is int for v in span), 'invalid cell span')
            rs, re_, cs, ce = span
            require(0 <= rs < re_ < len(y) and 0 <= cs < ce < len(x), 'cell span outside grid')
            f = cell.get('source_fragment')
            page = fragment(f)
            require(page == table['source_page'], 'grid source page mismatch')
            expected = [x[cs], y[rs], x[ce], y[re_]]
            require(max(abs(a-b) for a,b in zip(expected, f['bbox'])) <= .01,
                    'cell bbox differs from declared grid')
            for r in range(rs, re_):
                for c in range(cs, ce):
                    require((r,c) not in occupied, 'overlapping grid cells')
                    occupied.add((r,c))
            pages.add(page)
            count += 1
        total = (len(x)-1)*(len(y)-1)
        require(len(occupied) == total, 'grid has missing cells')
        slots += total
    return dict(status='PASS', scope='Declared grid coverage and original PDF text-region binding only; '
                'rulings, visual content, semantics and full extraction completeness not accepted',
                source_sha256=manifest['source_sha256'], verified_tables=len(tables),
                verified_cells=count, verified_fragments=count, verified_grid_slots=slots,
                source_pages=sorted(pages), document_status='BLOCK',
                evidentiary_status='NOT_EVIDENCE', acceptance_granted=False)


def verify(source: Path, manifest: dict, *, page_sizes: dict, read_text) -> dict:
    require(isinstance(manifest, dict), 'manifest must be an object')
    require('schema_version' not in manifest or
            (type(manifest['schema_version']) is int and manifest['schema_version'] in (1,2)),
            'unsupported recovery schema')
    sha = manifest.get('source_sha256')
    require(isinstance(sha, str) and re.fullmatch('[0-9a-f]{64}', sha), 'invalid source SHA256')
    with Path(source).open('rb') as handle:
        require(hashlib.file_digest(handle, 'sha256').hexdigest() == sha, 'source hash mismatch')
    review = manifest.get('review')
    require(isinstance(review, dict), 'declared source review required')
    require(all(isinstance(review.get(k), str) and review[k].strip()
                for k in ('reviewer', 'reviewed_at', 'scope')), 'incomplete source review')
    require(datetime.fromisoformat(review['reviewed_at'].replace('Z', '+00:00')).utcoffset() is not None,
            'review timestamp requires timezone')

    def fragment(f):
        require(isinstance(f, dict) and f.get('source_sha256') == sha, 'fragment source mismatch')
        page, box = f.get('source_page'), f.get('bbox')
        require(type(page) is int and page >= 1 and page in page_sizes, 'invalid source page')
        require(f.get('coordinate_origin') == 'TOPLEFT', 'coordinate origin must be TOPLEFT')
        require(isinstance(box, list) and len(box) == 4 and all(
            type(v) in (int, float) and math.isfinite(v) for v in box), 'invalid source bbox')
        width, height = page_sizes[page]
        require(0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height,
                'source bbox outside page')
        require(isinstance(f.get('text'), str), 'invalid fragment text')
        actual = read_text(page, box)
        require(isinstance(actual, str) and normalize(actual) == normalize(f['text']),
                'fragment text differs from original source')
        return page

    contexts = manifest.get('context_fragments')
    require(isinstance(contexts, list) and bool(contexts), 'source header/section context required')
    for f in contexts:
        require(isinstance(f, dict) and isinstance(f.get('text'), str) and f['text'].strip(),
                'source header/section context cannot be empty')
        fragment(f)
    if manifest.get('schema_version') == 2:
        return verify_grids(manifest, fragment)
    rows = manifest.get('rows')
    require(isinstance(rows, list) and bool(rows), 'no recovery candidates')
    ids, pages, count = set(), set(), 0
    for row in rows:
        require(isinstance(row, dict), 'invalid row candidate')
        identity = row.get('candidate_id')
        require(isinstance(identity, str) and identity.strip() and identity not in ids,
                'duplicate or missing candidate ID')
        ids.add(identity)
        require(row.get('status') == 'UNCERTAINTY' and row.get('evidentiary_status') == 'NOT_EVIDENCE'
                and row.get('acceptance_granted') is False, 'candidate must remain unaccepted')
        require(type(row.get('header_source_page')) is int and any(
            f['source_page'] == row['header_source_page'] for f in contexts), 'missing source header context')
        section = row.get('section')
        require(isinstance(section, dict) and isinstance(section.get('text'), str) and any(
            f['source_page'] == section.get('source_page') and normalize(f['text']) == normalize(section['text'])
            for f in contexts), 'missing source section context')
        declared_pages = row.get('source_pages')
        require(isinstance(declared_pages, list) and 1 <= len(declared_pages) <= 2
                and all(type(p) is int and p >= 1 for p in declared_pages)
                and (len(declared_pages) == 1 or declared_pages[1] == declared_pages[0] + 1),
                'invalid reviewed page relation')
        cells = row.get('cells')
        require(isinstance(cells, list) and len(cells) == 6, 'six source columns required')
        row_boxes = {}
        previous_right = {}
        for i, cell in enumerate(cells):
            require(isinstance(cell, dict) and type(cell.get('column_index')) is int
                    and cell['column_index'] == i and isinstance(cell.get('text'), str), 'invalid cell')
            fragments = cell.get('source_fragments')
            require(isinstance(fragments, list) and len(fragments) == len(declared_pages),
                    'missing cell source fragments')
            cell_pages = [fragment(f) for f in fragments]
            require(cell_pages == declared_pages, 'cell page relation mismatch')
            for f in fragments:
                page, box = f['source_page'], f['bbox']
                if page in row_boxes:
                    require(max(abs(box[j] - row_boxes[page][j]) for j in (1, 3)) <= .01,
                            'cell does not belong to source row band')
                else:
                    row_boxes[page] = box
                if page in previous_right:
                    require(abs(previous_right[page] - box[0]) <= .01, 'noncontiguous source columns')
                previous_right[page] = box[2]
            if len(fragments) == 2:
                require(max(abs(fragments[0]['bbox'][j] - fragments[1]['bbox'][j]) for j in (0,2)) <= .01,
                        'cross-page columns do not align')
            require(normalize(' '.join(f['text'] for f in fragments)) == normalize(cell['text']),
                    'joined cell text mismatch')
            pages.update(cell_pages)
            count += len(fragments)
    return dict(status='PASS', scope='Original PDF text-region binding only; semantics and completeness not accepted',
                source_sha256=sha, verified_rows=len(rows), verified_cells=len(rows)*6,
                verified_fragments=count, source_pages=sorted(pages),
                document_status='BLOCK', evidentiary_status='NOT_EVIDENCE', acceptance_granted=False)


def recover(source: Path, manifest: dict, *, project_id: str, document_id: str,
            page_sizes: dict, read_text) -> dict:
    """Export source-rechecked regions as candidates; never replace a full parse."""
    require(all(isinstance(value, str) and value.strip() for value in (project_id, document_id)),
            'candidate export requires project and document IDs')
    audit = verify(source, manifest, page_sizes=page_sizes, read_text=read_text)
    blocks = []

    def add_block(identity, kind, text, fragments):
        blocks.append(dict(block_id=identity, kind=kind, text=text, provenance=[
            dict(page_no=f['source_page'], bbox=dict(zip(('left','top','right','bottom'), f['bbox'])))
            for f in fragments]))

    for i, context in enumerate(manifest['context_fragments']):
        add_block(f'reviewed-context:{i}', 'table_context', context['text'], [context])
    schema = manifest.get('schema_version', 1)
    if schema == 2:
        for table in manifest['tables']:
            for cell in table['cells']:
                f = cell['source_fragment']
                identity = json.dumps([table['table_id'], cell['cell_id']],
                                      ensure_ascii=False, separators=(',', ':'))
                add_block(f'reviewed-cell:{identity}',
                          'table_cell', f['text'], [f])
                blocks[-1]['grid_span'] = {k:cell[k] for k in
                    ('row_start','row_end','col_start','col_end')}
                blocks[-1]['table_id'] = table['table_id']
                blocks[-1]['cell_id'] = cell['cell_id']
    else:
        for row in manifest['rows']:
            for cell in row['cells']:
                add_block(f"reviewed-cell:{row['candidate_id']}:{cell['column_index']}",
                          'table_cell', cell['text'], cell['source_fragments'])
    pages = [p['page_no'] for b in blocks for p in b['provenance']]
    result = dict(schema_version=schema, parser=f'reviewed_pdf_regions_v{schema}',
                project_id=project_id, document_id=document_id,
                source_sha256=audit['source_sha256'], source_path=str(source),
                page_start=min(pages), page_end=max(pages), coordinate_origin='TOPLEFT',
                status='UNCERTAINTY', document_status='BLOCK', evidentiary_status='NOT_EVIDENCE',
                complete_document=False, acceptance_granted=False,
                scope='Declared reviewed table regions only; not a full page or document extraction',
                source_binding_audit=audit, blocks=blocks,
                context_fragments=copy.deepcopy(manifest['context_fragments']),
                review=copy.deepcopy(manifest['review']))
    key = 'tables' if schema == 2 else 'rows'
    result[key] = copy.deepcopy(manifest[key])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate-output', type=Path,
                        help='Export only source-rechecked table candidates, retaining BLOCK document status')
    parser.add_argument('--project-id')
    parser.add_argument('--document-id')
    args = parser.parse_args()
    if args.candidate_output and not (args.project_id and args.document_id):
        parser.error('candidate output requires --project-id and --document-id')
    outputs = [args.output] + ([args.candidate_output] if args.candidate_output else [])
    checked = [args.source, args.manifest]
    for output in outputs:
        if any(output.resolve() == path.resolve() or
               (output.exists() and path.exists() and output.samefile(path)) for path in checked):
            parser.error('outputs must not overwrite inputs or each other')
        checked.append(output)
    candidates = None
    try:
        import fitz
        with fitz.open(args.source) as doc:
            require(doc.is_pdf, 'source must be a PDF document')
            page_sizes = {i+1: (p.rect.width, p.rect.height) for i,p in enumerate(doc)}
            words = {}
            def read_text(page, box):
                if page not in words:
                    words[page] = doc[page-1].get_text('words', sort=True)
                return ' '.join(w[4] for w in words[page] if
                    box[0] <= (w[0]+w[2])/2 < box[2] and box[1] <= (w[1]+w[3])/2 < box[3])
            manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
            if args.candidate_output:
                candidates = recover(args.source, manifest, project_id=args.project_id,
                                     document_id=args.document_id, page_sizes=page_sizes, read_text=read_text)
                result = candidates['source_binding_audit']
            else:
                result = verify(args.source, manifest, page_sizes=page_sizes, read_text=read_text)
    except (ImportError, ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
        result = dict(status='BLOCK', reason=str(exc), scope='Source-region audit failed',
                      document_status='BLOCK', evidentiary_status='NOT_EVIDENCE', acceptance_granted=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.candidate_output:
        # A failed rerun replaces old candidates with an explicit empty BLOCK, never stale success.
        payload = candidates if candidates is not None else dict(result, blocks=[], complete_document=False)
        args.candidate_output.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
