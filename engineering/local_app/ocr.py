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
import time

MAX_PIXELS=9000000
MAX_PAGE_PIXELS=5*MAX_PIXELS
MAX_OUTPUT=2*1024*1024
MAX_WORDS=20000
TIMEOUT=60
LANGUAGES=('rus','eng')
REGION_OVERLAP=32.0


class OCRError(ValueError):pass


def _layout():
    layout=os.environ.get('ENGINEER_OS_OCR_LAYOUT','whole')
    if layout not in {'whole','regions'}:raise OCRError('OCR_INVALID_LAYOUT')
    return layout


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
                    limits=[MAX_PIXELS,MAX_OUTPUT,MAX_WORDS,TIMEOUT,MAX_PAGE_PIXELS],render_scale=2.5,psm=3,
                    layout=_layout(),region_grid=[2,2],region_overlap=REGION_OVERLAP)
    except (OSError,OCRError):return dict(available=False,engine='TESSERACT',languages=list(LANGUAGES),reason='OCR_ENGINE_OR_LANGUAGES_UNAVAILABLE')


class TesseractOCR:
    def __init__(self):
        self.binary,self.data=_paths();self.layout=_layout();self.last_page_dossier=None

    def page_blocks(self,page,page_no):
        import fitz
        rotation=page.rotation
        self.last_page_dossier=None
        try:
            page.set_rotation(0)
            width,height=page.rect.width,page.rect.height
            if not all(math.isfinite(n) and n>0 for n in (width,height)):raise OCRError('OCR_INVALID_PAGE_GEOMETRY')
            regions=[('whole',fitz.Rect(0,0,width,height))]
            if self.layout=='regions':
                overlap=min(REGION_OVERLAP,width/10,height/10)
                for y in range(2):
                    for x in range(2):
                        regions.append((f'r{y*2+x+1}',fitz.Rect(max(0,x*width/2-overlap),max(0,y*height/2-overlap),
                            min(width,(x+1)*width/2+overlap),min(height,(y+1)*height/2+overlap))))
            dossier=dict(layout=self.layout,page_no=page_no,scope='UNVERIFIED_OCR_CANDIDATES',coverage='INCOMPLETE',
                page_bbox=dict(left=0,top=0,right=width,bottom=height),coordinate_space='UNROTATED_CROP_RELATIVE',
                planned_passes=len(regions),completed_passes=0,pixels=0,output_bytes=0,words=0,
                regions=[],quality_verified=False,acceptance_granted=False,
                limits=dict(page_pixels=MAX_PAGE_PIXELS,pass_pixels=MAX_PIXELS,output_bytes=MAX_OUTPUT,words=MAX_WORDS,seconds=TIMEOUT))
            self.last_page_dossier=dossier
            deadline=time.monotonic()+TIMEOUT;blocks=[]
            for region_id,clip in regions:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise OCRError('OCR_TIMEOUT: текущая страница не распознана')
                scale=min(2.5,3000/max(clip.width,clip.height))
                pixels=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip,colorspace=fitz.csRGB,alpha=False)
                count=pixels.width*pixels.height
                if count>MAX_PIXELS or dossier['pixels']+count>MAX_PAGE_PIXELS:raise OCRError('OCR_PIXEL_LIMIT')
                dossier['pixels']+=count
                remaining=deadline-time.monotonic()
                if remaining<=0:raise OCRError('OCR_TIMEOUT: текущая страница не распознана')
                raw=self._recognize(pixels,deadline,MAX_OUTPUT-dossier['output_bytes'])
                if time.monotonic()>=deadline:raise OCRError('OCR_TIMEOUT: текущая страница не распознана')
                dossier['output_bytes']+=len(raw)
                try:
                    found=self._blocks(raw.decode('utf-8'),page_no,scale,pixels.width,pixels.height,
                        word_limit=MAX_WORDS-dossier['words'])
                except (UnicodeError,ValueError,KeyError,csv.Error) as exc:
                    if isinstance(exc,OCRError):raise
                    raise OCRError('OCR_INVALID_OUTPUT') from None
                dossier['words']+=sum(b['ocr_word_count'] for b in found)
                for block in found:
                    box=block['provenance'][0]['bbox']
                    for key in ('left','right'):box[key]+=pixels.x/scale
                    for key in ('top','bottom'):box[key]+=pixels.y/scale
                    # Pixmap rounding can extend an edge by at most a pixel.
                    box.update(left=max(0,box['left']),top=max(0,box['top']),right=min(width,box['right']),bottom=min(height,box['bottom']))
                    if box['right']<=box['left'] or box['bottom']<=box['top']:raise OCRError('OCR_INVALID_OUTPUT')
                    block['ocr_region']=region_id
                    if region_id!='whole':block['block_id']=block['block_id'].replace(':line:',f':region:{region_id}:line:')
                if time.monotonic()>=deadline:raise OCRError('OCR_TIMEOUT: текущая страница не распознана')
                blocks.extend(found)
                dossier['regions'].append(dict(id=region_id,bbox=dict(zip(('left','top','right','bottom'),clip)),
                    execution='COMPLETED',blocks=len(found),characters=sum(len(b['text']) for b in found)))
                dossier['completed_passes']+=1
            dossier['coverage']='WHOLE_PAGE_AND_REGIONS_EXECUTED' if self.layout=='regions' else 'WHOLE_PAGE_EXECUTED'
            return blocks
        finally:page.set_rotation(rotation)

    def _recognize(self,pixels,deadline,output_budget):
        with tempfile.TemporaryDirectory(prefix='engineer-ocr-') as folder:
            root=Path(folder);source=root/'page.png';output=root/'result'
            pixels.save(source)
            timeout=deadline-time.monotonic()
            if timeout<=0:raise OCRError('OCR_TIMEOUT: текущая страница не распознана')
            command=[str(self.binary),str(source),str(output),'--tessdata-dir',str(self.data),'-l','rus+eng','--psm','3','-c','tessedit_create_tsv=1']
            environment={key:value for key,value in os.environ.items() if key in {'SYSTEMROOT','WINDIR','TEMP','TMP'}}
            environment.update(PATH=os.defpath,LANG='C.UTF-8',OMP_THREAD_LIMIT='2')
            try:result=subprocess.run(command,shell=False,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                      env=environment,timeout=timeout,check=False)
            except subprocess.TimeoutExpired:raise OCRError('OCR_TIMEOUT: текущая страница не распознана') from None
            except OSError:raise OCRError('OCR_ENGINE_UNAVAILABLE') from None
            path=output.with_suffix('.tsv')
            if result.returncode or not path.is_file():raise OCRError('OCR_FAILED: результат страницы недоступен')
            with path.open('rb') as stream:raw=stream.read(output_budget+1)
        if len(raw)>output_budget:raise OCRError('OCR_OUTPUT_LIMIT')
        return raw

    @staticmethod
    def _blocks(tsv,page_no,scale,width,height,*,word_limit=None):
        if word_limit is None:word_limit=MAX_WORDS
        lines={};words=0
        for row in csv.DictReader(io.StringIO(tsv),delimiter='\t',quoting=csv.QUOTE_NONE):
            if row.get('level')!='5' or not (row.get('text') or '').strip():continue
            words+=1
            if words>word_limit:raise OCRError('OCR_WORD_LIMIT')
            x,y,w,h=[int(row[key]) for key in ('left','top','width','height')];confidence=float(row['conf'])
            if x<0 or y<0 or w<=0 or h<=0 or x+w>width+1 or y+h>height+1 or not math.isfinite(confidence) or not -1<=confidence<=100:
                raise ValueError('Invalid OCR geometry')
            key=tuple(row[name] for name in ('block_num','par_num','line_num'))
            group=lines.setdefault(key,dict(text=[],left=x,top=y,right=x+w,bottom=y+h,confidence=confidence))
            group['text'].append(row['text']);group['left']=min(group['left'],x);group['top']=min(group['top'],y)
            group['right']=max(group['right'],x+w);group['bottom']=max(group['bottom'],y+h);group['confidence']=min(group['confidence'],confidence)
        return [dict(block_id=f'ocr:page:{page_no}:line:{index}',kind='ocr_text',text=' '.join(group['text']),
                     ocr_confidence=group['confidence'],ocr_word_count=len(group['text']),provenance=[dict(page_no=page_no,bbox={k:group[k]/scale for k in ('left','top','right','bottom')})])
                for index,group in enumerate(lines.values(),1)]


def page_blocks(page,page_no):return TesseractOCR().page_blocks(page,page_no)
