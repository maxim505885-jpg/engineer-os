"""Inspect a blocked-page export ZIP offline; never register or accept evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile


def _table(table: dict, page: int, candidates: list[dict]) -> dict:
    issues = []
    refs = table.get('provenance')
    if (not isinstance(refs, list) or not refs or
            any(not isinstance(ref, dict) or ref.get('page_no') != page for ref in refs)):
        issues.append('MISSING_OR_FOREIGN_TABLE_PROVENANCE')
    rows, cols = table.get('num_rows'), table.get('num_cols')
    result = {'rows': rows, 'columns': cols, 'issues': issues,
              'merged_cells': 0, 'missing_positions': None, 'overlapping_positions': None,
              'candidate_comparisons': []}
    if (type(rows) is not int or type(cols) is not int or rows <= 0 or cols <= 0
            or rows * cols > 1_000_000):
        issues.append('INVALID_DIMENSIONS')
        return result
    cells = table.get('cells')
    if not isinstance(cells, list):
        issues.append('INVALID_CELLS')
        return result
    coverage = Counter()
    texts = []
    for cell in cells:
        if not isinstance(cell, dict):
            issues.append('INVALID_CELL')
            continue
        span = [cell.get(k) for k in ('start_row_offset_idx', 'end_row_offset_idx',
                                      'start_col_offset_idx', 'end_col_offset_idx')]
        if (any(type(v) is not int for v in span) or
                not (0 <= span[0] < span[1] <= rows and 0 <= span[2] < span[3] <= cols)):
            issues.append('INVALID_CELL_SPAN')
            continue
        r0, r1, c0, c1 = span
        result['merged_cells'] += int(r1-r0 > 1 or c1-c0 > 1)
        coverage.update((r, c) for r in range(r0, r1) for c in range(c0, c1))
        value = cell.get('text')
        if not isinstance(value, str):
            issues.append('INVALID_CELL_TEXT')
        elif value.strip():
            texts.append(' '.join(value.split()))
        if isinstance(value, str) and any(label in value for label in ('№ док.', '№док', 'Инв. №', 'Подп. и дата')):
            issues.append('POSSIBLE_STAMP_IN_BODY_TABLE')
    result['missing_positions'] = rows * cols - len(coverage)
    result['overlapping_positions'] = sum(n > 1 for n in coverage.values())
    if result['missing_positions']: issues.append('MISSING_GRID_POSITIONS')
    if result['overlapping_positions']: issues.append('OVERLAPPING_GRID_POSITIONS')
    for index, candidate in enumerate(candidates):
        grid = candidate['raw_grid']
        other = Counter(' '.join(v.split()) for row in grid for v in row if isinstance(v, str) and v.strip())
        result['candidate_comparisons'].append({'candidate_index': index,
            'shape_matches': rows == candidate['rows'] and cols == candidate['columns'],
            'nonempty_text_matches': Counter(texts) == other,
            'candidate_only_text_count': sum((other - Counter(texts)).values()),
            'docling_only_text_count': sum((Counter(texts) - other).values()),
            'note': 'Text multiset and shape only; region location, cell assignment and image content remain unverified.'})
    result['issues'] = sorted(set(issues))
    return result


def inspect_archive(path: Path, review: dict, candidates: dict | None = None) -> dict:
    digest = review.get('source_sha256')
    if (review.get('status') != 'BLOCK' or not isinstance(digest, str) or len(digest) != 64
            or any(v not in '0123456789abcdef' for v in digest)):
        raise ValueError('invalid source review identity or status')
    reasons = {}
    for reason, pages in review['blocked_reasons'].items():
        for page in pages:
            if type(page) is not int or not 1 <= page <= review['page_count'] or page in reasons:
                raise ValueError('invalid or duplicate blocked page')
            reasons[page] = reason
    if not reasons: raise ValueError('no blocked pages in source review')
    by_page = {}
    if candidates is not None:
        if candidates.get('source_sha256') != digest or candidates.get('status') != 'BLOCK':
            raise ValueError('candidate source or status mismatch')
        for item in candidates['pages']:
            page = item['page']
            if page not in reasons or page in by_page: raise ValueError('foreign or duplicate candidate page')
            by_page[page] = item['candidates']
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or 'manifest.json' not in names:
            raise ValueError('duplicate archive members or missing manifest')
        if sum(info.file_size for info in archive.infolist()) > 100_000_000:
            raise ValueError('archive exceeds diagnostic size limit')
        manifest = json.loads(archive.read('manifest.json'))
        selected = manifest.get('selected_pages')
        if (manifest.get('source_sha256') != digest or manifest.get('status') != 'BLOCK'
                or not isinstance(selected, list) or any(type(p) is not int for p in selected)
                or len(selected) != len(set(selected)) or set(selected) != set(reasons)):
            raise ValueError('manifest source, status or selected pages mismatch')
        exported = manifest.get('exported_pages', [])
        failed = manifest.get('failed_pages', [])
        exported_ids = [e['page'] for e in exported]
        failed_ids = [e['page'] for e in failed]
        ids = exported_ids + failed_ids
        if (any(type(p) is not int for p in ids) or len(ids) != len(set(ids)) or set(ids) != set(reasons)
                or any(e.get('reason') != reasons.get(e['page']) for e in exported)):
            raise ValueError('manifest page outcomes or blocked reasons mismatch')
        expected = {'manifest.json'} | {f'page-{p:04d}.json' for p in exported_ids}
        if set(names) != expected: raise ValueError('missing, foreign or unsafe archive member')
        pages = []
        for page in sorted(exported_ids):
            data = json.loads(archive.read(f'page-{page:04d}.json'))
            issues = []
            tables = []
            if (not isinstance(data, dict) or data.get('source_sha256') != digest or
                    data.get('page_start') != page or data.get('page_end') != page):
                issues.append('EXPORT_IDENTITY_MISMATCH')
            elif not isinstance(data.get('tables'), list) or not isinstance(data.get('text_blocks'), list):
                issues.append('INVALID_EXPORT_STRUCTURE')
            else:
                for block in data['text_blocks']:
                    refs = block.get('provenance') if isinstance(block, dict) else None
                    if (not isinstance(refs, list) or not refs or any(not isinstance(r, dict)
                            or r.get('page_no') != page for r in refs)):
                        issues.append('MISSING_OR_FOREIGN_TEXT_PROVENANCE')
                for table in data['tables']:
                    if not isinstance(table, dict): issues.append('INVALID_TABLE')
                    else: tables.append(_table(table, page, by_page.get(page, [])))
            pages.append({'page': page, 'reason': reasons[page], 'page_status': 'BLOCK',
                          'issues': sorted(set(issues)), 'tables': tables,
                          'offline_candidate_count': len(by_page.get(page, []))})
    return {'source_sha256': digest, 'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'status': 'BLOCK', 'archive_complete': not failed,
            'selected_pages': sorted(reasons), 'failed_pages': failed, 'pages': pages,
            'note': 'Export completeness is not extraction validity or engineering acceptance. Verify every region against source images; original audit remains BLOCK.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'review', 'output'): parser.add_argument(name, type=Path)
    parser.add_argument('--candidates', type=Path)
    args = parser.parse_args()
    candidates = json.loads(args.candidates.read_text(encoding='utf-8')) if args.candidates else None
    result = inspect_archive(args.archive, json.loads(args.review.read_text(encoding='utf-8')), candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('EXPORTED:', len(result['pages']), 'FAILED:', len(result['failed_pages']))
    print('REPORT:', args.output)
    print('STATUS: BLOCK; visual verification required')
    return 0


if __name__ == '__main__': raise SystemExit(main())
