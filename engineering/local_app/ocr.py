"""Local bounded OCR. Recognized text and boxes remain unverified candidates."""
import csv
import hashlib
import io
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

MAX_PIXELS=9000000
MAX_OUTPUT=2*1024*1024
MAX_WORDS=20000
TIMEOUT=60
LANGUAGES=('rus','eng')


class OCRError(ValueError):pass


def _paths():
    configured=os.environ.get('ENGINEER_OS_TESSERACT_BIN')
    executable=Path(configured or shutil.which('tesseract') or '')
    if not executable.is_absolute() or not executable.is_file():raise OCRError('OCR_ENGINE_UNAVAILABLE')
    configured_data=os.environ.get('ENGINEER_OS_TESSDATA_DIR') or os.environ.get('TESSDATA_PREFIX')
    if configured_data:
        data=Path(configured_data)
    else:
        candidates=[executable.parent/'tessdata',Path('/usr/share/tesseract-ocr/5/tessdata'),Path('/usr/share/tessdata')]
        data=next((p for p in candidates if p.is_dir()),Path())
    if not data.is_absolute() or any(not (data/(language+'.traineddata')).is_file() for language in LANGUAGES):
        raise OCRError('OCR_LANGUAGE_MODELS_UNAVAILABLE: требуется локальная rus+eng')
    return executable.resolve(),data.resolve()


def _sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def identity():
    try:
        binary,data=_paths()
        return dict(available=True,engine='TESSERACT',binary_sha256=_sha(binary),
                    languages={language:_sha(data/(language+'.traineddata')) for language in LANGUAGES},
                    limits=[MAX_PIXELS,MAX_OUTPUT,MAX_WORDS,TIMEOUT],render_scale=2.5,psm=3)
    except (OSError,OCRError):return dict(available=False,engine='TESSERACT',languages=list(LANGUAGES),reason='OCR_ENGINE_OR_LANGUAGES_UNAVAILABLE')


class TesseractOCR:
    def __init__(self):self.binary,self.data=_paths()

    def page_blocks(self,page,page_no):
        import fitz
        rotation=page.rotation
        try:
            page.set_rotation(0)
            width,height=page.rect.width,page.rect.height
            if not all(math.isfinite(n) and n>0 for n in (width,height)):raise OCRError('OCR_INVALID_PAGE_GEOMETRY')
            scale=min(2.5,3000/max(width,height))
            pixels=page.get_pixmap(matrix=fitz.Matrix(scale,scale),colorspace=fitz.csRGB,alpha=False)
        finally:page.set_rotation(rotation)
        if pixels.width*pixels.height>MAX_PIXELS:raise OCRError('OCR_PIXEL_LIMIT')
        with tempfile.TemporaryDirectory(prefix='engineer-ocr-') as folder:
            root=Path(folder);source=root/'page.png';output=root/'result'
            pixels.save(source)
            command=[str(self.binary),str(source),str(output),'--tessdata-dir',str(self.data),'-l','rus+eng','--psm','3','-c','tessedit_create_tsv=1']
            environment={key:value for key,value in os.environ.items() if key in {'SYSTEMROOT','WINDIR','TEMP','TMP'}}
            environment.update(PATH=os.defpath,LANG='C.UTF-8',OMP_THREAD_LIMIT='2')
            try:result=subprocess.run(command,shell=False,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                      env=environment,timeout=TIMEOUT,check=False)
            except subprocess.TimeoutExpired:raise OCRError('OCR_TIMEOUT: текущая страница не распознана') from None
            except OSError:raise OCRError('OCR_ENGINE_UNAVAILABLE') from None
            path=output.with_suffix('.tsv')
            if result.returncode or not path.is_file():raise OCRError('OCR_FAILED: результат страницы недоступен')
            with path.open('rb') as stream:raw=stream.read(MAX_OUTPUT+1)
        if len(raw)>MAX_OUTPUT:raise OCRError('OCR_OUTPUT_LIMIT')
        try:return self._blocks(raw.decode('utf-8'),page_no,scale,pixels.width,pixels.height)
        except (UnicodeError,ValueError,KeyError,csv.Error):raise OCRError('OCR_INVALID_OUTPUT') from None

    @staticmethod
    def _blocks(tsv,page_no,scale,width,height):
        lines={};words=0
        for row in csv.DictReader(io.StringIO(tsv),delimiter='\t'):
            if row.get('level')!='5' or not (row.get('text') or '').strip():continue
            words+=1
            if words>MAX_WORDS:raise OCRError('OCR_WORD_LIMIT')
            x,y,w,h=[int(row[key]) for key in ('left','top','width','height')];confidence=float(row['conf'])
            if x<0 or y<0 or w<=0 or h<=0 or x+w>width+1 or y+h>height+1 or not math.isfinite(confidence) or not -1<=confidence<=100:
                raise ValueError('Invalid OCR geometry')
            key=tuple(row[name] for name in ('block_num','par_num','line_num'))
            group=lines.setdefault(key,dict(text=[],left=x,top=y,right=x+w,bottom=y+h,confidence=confidence))
            group['text'].append(row['text']);group['left']=min(group['left'],x);group['top']=min(group['top'],y)
            group['right']=max(group['right'],x+w);group['bottom']=max(group['bottom'],y+h);group['confidence']=min(group['confidence'],confidence)
        return [dict(block_id=f'ocr:page:{page_no}:line:{index}',kind='ocr_text',text=' '.join(group['text']),
                     ocr_confidence=group['confidence'],provenance=[dict(page_no=page_no,bbox={k:group[k]/scale for k in ('left','top','right','bottom')})])
                for index,group in enumerate(lines.values(),1)]


def page_blocks(page,page_no):return TesseractOCR().page_blocks(page,page_no)
