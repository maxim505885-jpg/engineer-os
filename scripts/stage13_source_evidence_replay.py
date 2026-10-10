"""Source-level PDF/DOCX replay; does not claim semantic or pipeline acceptance."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def replay(pdf_path, docx_path, pages=(15,55,65,66)):
    import fitz
    pdf_path, docx_path=Path(pdf_path),Path(docx_path)
    result={'schema':'ENGINEER_OS_STAGE13_SOURCE_REPLAY_V1',
            'sources':{'pdf_sha256':sha_file(pdf_path),'docx_sha256':sha_file(docx_path)},
            'module_gate_status':'BLOCK',
            'limitations':['Table candidates require visual cell validation.',
                           'DOCX source hashes do not prove downstream preservation.',
                           'Source replay is not application integration regression.']}
    with fitz.open(pdf_path) as document:
        result['pdf_pages']=len(document)
        result['table_candidates']=[]
        for n in pages:
            if n<1 or n>len(document):
                raise ValueError('Invalid source page number')
            for i,table in enumerate(document[n-1].find_tables().tables):
                cells=table.extract()
                result['table_candidates'].append({'page':n,'candidate':i,
                    'bbox_pdf':[round(v,2) for v in table.bbox],
                    'rows':table.row_count,'cols':table.col_count,
                    'cells':cells,
                    'cells_sha256':digest(json.dumps(cells,ensure_ascii=False).encode()),
                    'status':'SOURCE_CANDIDATE_UNVERIFIED'})
    with zipfile.ZipFile(docx_path) as archive:
        bad=archive.testzip()
        if bad: raise ValueError('Invalid DOCX ZIP: '+bad)
        root=ET.fromstring(archive.read('word/document.xml'))
        namespace={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
        formulas=root.findall('.//m:oMath',namespace)
        names=sorted(n for n in archive.namelist() if n.startswith('word/media/') and not n.endswith('/'))
        result['docx']={'omml_count':len(formulas),
            'omml_sha256':[digest(ET.tostring(x)) for x in formulas],
            'media_count':len(names),
            'media_sha256':{n:digest(archive.read(n)) for n in names},
            'zip_integrity':'PASS','downstream_preservation_proven':False}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('pdf',type=Path)
    parser.add_argument('docx',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(replay(args.pdf,args.docx),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
