"""Prepare a bounded PDF region and restore Docling locations to its original.

A crop is a diagnostic derivative, never proof of page completeness. Run the
source-grid verifier against the original PDF after remapping an export.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def region_geometry(page, bbox):
    if page.rotation or page.cropbox.x0 or page.cropbox.y0:
        raise ValueError('rotated or offset-crop pages require a separate transform')
    if (not isinstance(bbox, list) or len(bbox) != 4
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in bbox)
            or not 0 <= bbox[0] < bbox[2] <= page.rect.width
            or not 0 <= bbox[1] < bbox[3] <= page.rect.height):
        raise ValueError('invalid original region bbox')
    return bbox[2]-bbox[0], bbox[3]-bbox[1]


def prepare_region(source, output, *, page_no, bbox, expected_sha256):
    import fitz
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve() or (output.exists() and source.samefile(output)):
        raise ValueError('region must not overwrite the source PDF')
    original_sha = sha256(source)
    if original_sha != expected_sha256:
        raise ValueError('original source checksum mismatch')
    with fitz.open(source) as pdf:
        if type(page_no) is not int or not 1 <= page_no <= len(pdf):
            raise ValueError('invalid original source page')
        page = pdf[page_no-1]
        width, height = region_geometry(page, bbox)
        original_size = dict(width=page.rect.width, height=page.rect.height)
        with fitz.open() as cropped:
            target = cropped.new_page(width=width, height=height)
            target.show_pdf_page(target.rect, pdf, page_no-1, clip=fitz.Rect(bbox))
            output.parent.mkdir(parents=True, exist_ok=True)
            cropped.save(output)
    with fitz.open(output) as derivative:
        serialized_size = dict(width=derivative[0].rect.width, height=derivative[0].rect.height)
    return dict(schema_version=1, source_sha256=original_sha,
                derived_sha256=sha256(output), source_page=page_no,
                source_bbox=bbox, source_size=original_size,
                derived_size=serialized_size,
                coordinate_origin='TOPLEFT', complete_page=False,
                complete_document=False, acceptance_granted=False,
                evidentiary_status='NOT_EVIDENCE',
                scope='One PDF content region; annotations and surrounding page excluded')


def remap_export(source, derivative, mapping, exported):
    """Check both files, then convert every local bbox and page reference."""
    import fitz
    if (mapping.get('schema_version') != 1
            or mapping.get('coordinate_origin') != 'TOPLEFT'
            or sha256(source) != mapping.get('source_sha256')
            or sha256(derivative) != mapping.get('derived_sha256')):
        raise ValueError('region/source mapping or checksum mismatch')
    with fitz.open(source) as pdf:
        number = mapping.get('source_page')
        if type(number) is not int or not 1 <= number <= len(pdf):
            raise ValueError('invalid source page')
        page = pdf[number-1]
        width, height = region_geometry(page, mapping.get('source_bbox'))
        source_size = dict(width=page.rect.width, height=page.rect.height)
        if source_size != mapping.get('source_size'):
            raise ValueError('original page geometry changed')
    size = mapping.get('derived_size')
    # PDF coordinates serialize to single precision. This is a bounded
    # roundoff allowance in points, not permission to resize a region.
    if (not isinstance(size, dict) or any(type(size.get(k)) not in (int,float)
            or not math.isclose(size[k], value, rel_tol=0, abs_tol=1e-4)
            for k,value in [('width',width),('height',height)])):
        raise ValueError('derived region geometry mismatch')
    with fitz.open(derivative) as pdf:
        if len(pdf) != 1 or any(not math.isclose(size[k], value, rel_tol=0, abs_tol=1e-4)
                for k,value in [('width',pdf[0].rect.width),('height',pdf[0].rect.height)]):
            raise ValueError('derivative is not the declared single region')
        width, height = pdf[0].rect.width, pdf[0].rect.height
        size = dict(width=width, height=height)
    pages = exported.get('pages') if isinstance(exported,dict) else None
    exported_size = pages.get('1', {}).get('size') if isinstance(pages,dict) and isinstance(pages.get('1'),dict) else None
    if (not isinstance(pages,dict) or set(pages) != {'1'} or not isinstance(exported_size,dict)
            or any(type(exported_size.get(k)) not in (int,float)
                or not math.isclose(exported_size[k],value,rel_tol=0,abs_tol=1e-4)
                for k,value in size.items())):
        raise ValueError('export does not match derivative page geometry')
    result = copy.deepcopy(exported)
    x0, y0, _, _ = mapping['source_bbox']

    def convert_box(b):
        if not isinstance(b, dict) or any(type(b.get(k)) not in (int, float)
                or not math.isfinite(b[k]) for k in ('l', 'r', 't', 'b')):
            raise ValueError('invalid region bbox')
        l, r, t, bottom = (b[k] for k in ('l', 'r', 't', 'b'))
        if b.get('coord_origin') == 'BOTTOMLEFT':
            t, bottom = height-t, height-bottom
        elif b.get('coord_origin') != 'TOPLEFT':
            raise ValueError('unknown region coordinate origin')
        if not -1e-4 <= l < r <= width+1e-4 or not -1e-4 <= t < bottom <= height+1e-4:
            raise ValueError('export bbox outside derivative region')
        l,r,t,bottom = max(0,l),min(width,r),max(0,t),min(height,bottom)
        if l >= r or t >= bottom:
            raise ValueError('empty region bbox after roundoff correction')
        b.update(l=x0+l, r=x0+r, t=y0+t, b=y0+bottom, coord_origin='TOPLEFT')

    def visit(node):
        if isinstance(node, list):
            for child in node: visit(child)
        elif isinstance(node, dict):
            if 'page_no' in node:
                if type(node['page_no']) is not int or node['page_no'] != 1:
                    raise ValueError('export reference outside derivative page')
                node['page_no'] = number
            for key, value in node.items():
                if key == 'bbox': convert_box(value)
                else: visit(value)

    visit(result)
    result['pages'] = {str(number): dict(page_no=number, size=source_size)}
    result['region_provenance'] = dict(mapping, complete_page=False,
                                      complete_document=False, acceptance_granted=False,
                                      evidentiary_status='NOT_EVIDENCE')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--page', type=int, required=True)
    parser.add_argument('--bbox', type=float, nargs=4, required=True, metavar=('L','T','R','B'))
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    mapping_path = args.output.with_suffix('.mapping.json')
    if mapping_path.resolve() == args.source.resolve() or (mapping_path.exists() and mapping_path.samefile(args.source)):
        parser.error('mapping must not overwrite source')
    mapping = prepare_region(args.source, args.output, page_no=args.page,
                             bbox=args.bbox, expected_sha256=args.sha256)
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    print('REGION_PREPARED; NOT_EVIDENCE; original page', mapping['source_page'])


if __name__ == '__main__':
    main()
