"""Fail-closed process-bounded PDF OCR batch runner.

Each PDF page is isolated in a child process. A hung vector rasterizer or OCR
engine cannot starve the entire run. Timeout is for page subprocess, not Tesseract.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def run_batch(source, output, pages, timeout=35, dpi=65):
    source=Path(source)
    if not source.is_file() or not 1<=timeout<=600:
        raise ValueError('Existing source PDF and bounded timeout required')
    if source.suffix.lower()!='.pdf':
        raise ValueError('Original PDF required')
    with source.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    worker=Path(__file__).resolve().with_name('vector_pdf_ocr_review.py')
    output=Path(output)
    tempdir=output.parent/(output.stem+'_pages')
    tempdir.mkdir(parents=True,exist_ok=True)
    records=[]
    for number in pages:
        if number<1:
            raise ValueError('Invalid PDF page')
        path=tempdir/f'page_{number:04d}.json'
        cmd=[sys.executable,str(worker),str(source),str(path),'--page',str(number),'--dpi',str(dpi)]
        try:
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
            if proc.returncode!=0 or not path.is_file():
                records.append(dict(page=number,status='ERROR',reason='CHILD_FAILED',
                                    detail=(proc.stderr or '')[-1000:]))
                continue
            data=json.loads(path.read_text(encoding='utf-8'))
            if data.get('source_sha256')!=digest or len(data.get('records',[]))!=1:
                records.append(dict(page=number,status='BLOCK',reason='SOURCE_IDENTITY_MISMATCH'))
                continue
            row=data['records'][0]
            records.append(dict(page=number,status='CANDIDATES_UNVERIFIED' if not row.get('ocr_failures') else 'PARTIAL',
                                candidates=len(row.get('candidates',[])),
                                ocr_failures=row.get('ocr_failures',[]),output=str(path)))
        except subprocess.TimeoutExpired:
            records.append(dict(page=number,status='BLOCK',reason='PROCESS_TIMEOUT'))
        except (OSError,ValueError,json.JSONDecodeError):
            records.append(dict(page=number,status='BLOCK',reason='INVALID_WORKER_RESULT'))
        output.write_text(json.dumps(dict(schema='ENGINEER_OS_PROCESS_BOUNDED_OCR_BATCH_V1',
            source_sha256=digest,requested_pages=list(pages),page_results=records,
            qualified=False,all_pages_completed=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    statuses=[row['status'] for row in records]
    result=dict(schema='ENGINEER_OS_PROCESS_BOUNDED_OCR_BATCH_V1',source_sha256=digest,
                requested_pages=list(pages),page_results=records,qualified=False,
                all_pages_completed=all(x=='CANDIDATES_UNVERIFIED' for x in statuses))
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--first',type=int,default=492);parser.add_argument('--last',type=int,default=531)
    parser.add_argument('--timeout',type=int,default=35);parser.add_argument('--dpi',type=int,default=65)
    args=parser.parse_args()
    if args.last<args.first:parser.error('Last page must not precede first')
    run_batch(args.source,args.output,list(range(args.first,args.last+1)),args.timeout,args.dpi)
