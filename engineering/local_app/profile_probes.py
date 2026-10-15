"""Only fixed synthetic inputs; no user paths, model download, or arbitrary commands."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def execute(name):
    receipt=dict(schema='ENGINEER_OS_FIXED_PROBE_V1',name=name,passed=False,
        acceptance_granted=False,scope='FIXED_SYNTHETIC_PROBE_ONLY')
    if name=='pdf':
        import fitz
        with fitz.open() as document:
            page=document.new_page();page.insert_text((72,72),'ENGINEER OS 123.45')
            data=document.tobytes()
        with fitz.open(stream=data,filetype='pdf') as document:
            text=document[0].get_text();pix=document[0].get_pixmap()
            receipt.update(passed='123.45' in text and pix.width>0 and pix.height>0,source_sha256=hashlib.sha256(data).hexdigest(),engine_version=fitz.VersionBind)
    elif name=='ocr':
        import fitz
        from PIL import Image,ImageDraw,ImageFont
        from .ocr import TesseractOCR,identity
        fonts=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
        font=next((p for p in fonts if p.is_file()),None)
        if font is None:raise ValueError('PROBE_FONT_UNAVAILABLE')
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'scan.png';image=Image.new('RGB',(1700,260),'white')
            ImageDraw.Draw(image).text((40,60),'Высота 4 метра. Height 4 metres.',font=ImageFont.truetype(str(font),65),fill='black');image.save(target)
            with fitz.open(target) as image_doc:pdf=image_doc.convert_to_pdf()
            with fitz.open(stream=pdf,filetype='pdf') as document:blocks=TesseractOCR().page_blocks(document[0],1)
            text=' '.join(b['text'] for b in blocks)
            receipt.update(passed='Высота' in text and 'Height' in text and all(b['provenance'][0]['bbox'] for b in blocks),
                source_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),font_sha256=hashlib.sha256(font.read_bytes()).hexdigest(),engine_identity=identity(),recognized_text=text)
    elif name=='beam':
        from engineering.calculation.control_beam import BeamInput,calculate_beam
        inputs=BeamInput(6.,210e9,8e-6,.003,1000.,hashlib.sha256(b'FIXED_SYNTHETIC_BEAM_V1').hexdigest(),('synthetic-benchmark',))
        result=calculate_beam(inputs)
        receipt.update(passed=result['status']=='PASS' and abs(result['results']['reaction_left_n']-3000.)<1e-5,comparison=result)
    elif name=='ifc':
        from engineering.bim.ifc_adapter import inspect_ifc
        fixture=Path(__file__).resolve().parents[2]/'tests/fixtures/bim/reference.ifc'
        sha=hashlib.sha256(fixture.read_bytes()).hexdigest()
        result=inspect_ifc(fixture,expected_sha256=sha)
        receipt.update(passed=result['status']=='UNCERTAINTY' and result['length_to_m']==.001 and len(result['elements'])==4,source_sha256=sha,
            checks=dict(element_count=len(result['elements']),length_to_m=result.get('length_to_m')))
    else:raise ValueError('PROBE_NOT_SUPPORTED')
    return receipt


if __name__=='__main__':
    print(json.dumps(execute(sys.argv[1]),ensure_ascii=True,allow_nan=False))
