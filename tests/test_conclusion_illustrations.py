import base64
import hashlib
import inspect
import io
import json
import unittest
import zipfile

import fitz
from PIL import Image
from tests import test_conclusion_drafts as draft_tests
from engineering.local_app import conclusions
from engineering.local_app.files import preserve_file
from engineering.local_app.real_case import build as build_case
from engineering.local_app.worker import Worker
from engineering.local_app.analysis_identity import digest


class IllustrationTests(unittest.TestCase):
    setUp=draft_tests.ConclusionTests.setUp
    module=draft_tests.ConclusionTests.module
    build=draft_tests.ConclusionTests.build

    def pdf_case(self):
        with fitz.open() as pdf:
            page=pdf.new_page(width=300,height=200)
            page.draw_rect(fitz.Rect(30,30,150,120),color=(1,0,0),fill=(1,0,0))
            self.source=preserve_file(self.store,self.sid,'inspection.pdf',pdf.tobytes())
        job=self.store.enqueue(self.sid,'Review',[self.source['id']],mode='CORE_RUN',requested_checks=['report'])
        Worker(self.store,draft_tests.Model()).run_once()
        self.case=build_case(self.store,self.sid,job_id=job['id'],expected_revision=1,manifest={'TOR':[self.source['id']],'REPORT':[self.source['id']]})

    def require_api(self):
        self.assertIn('template_id',inspect.signature(conclusions.build).parameters,'draft templates are missing')
        self.assertIn('illustration_requests',inspect.signature(conclusions.build).parameters,'draft illustrations are missing')

    def test_builtin_templates_and_unknown_template_rejection(self):
        self.require_api()
        a=self.build(template_id='inspection')
        b=self.build(expected_revision=1,template_id='report-review')
        self.assertNotEqual(a['content']['title'],b['content']['title'])
        self.assertEqual(a['template_id'],'inspection')
        self.assertFalse(a['acceptance_granted'])
        with self.assertRaises(ValueError):self.build(expected_revision=2,template_id='accepted-report')

    def test_same_source_bound_image_is_embedded_in_both_formats(self):
        self.require_api();self.pdf_case()
        d=self.build(template_id='inspection',illustration_requests=[{'file_id':self.source['id'],'page':1}])
        asset=d['illustration_assets'][0];png=base64.b64decode(asset['data_base64'])
        descriptor=d['content']['illustrations'][0]
        self.assertEqual(hashlib.sha256(png).hexdigest(),descriptor['image_sha256'])
        self.assertEqual(descriptor['source_sha256'],self.source['sha256'])
        self.assertIn('НЕПРОВЕРЕННАЯ ИЛЛЮСТРАЦИЯ',descriptor['caption'])
        docx,_=conclusions.export(self.store,self.sid,revision=1,format='docx')
        with zipfile.ZipFile(io.BytesIO(docx)) as z:
            images=[z.read(n) for n in z.namelist() if n.startswith('word/media/')]
            self.assertEqual(images,[png])
            self.assertIn(b'image',z.read('word/_rels/document.xml.rels'))
        output,_=conclusions.export(self.store,self.sid,revision=1,format='pdf')
        with fitz.open(stream=output,filetype='pdf') as pdf:
            image_ids={im[0] for page in pdf for im in page.get_images()}
            self.assertEqual(len(image_ids),1)
            image_page=next(page for page in pdf if page.get_image_info())
            self.assertIn('НЕПРОВЕРЕННАЯИЛЛЮСТРАЦИЯ',''.join(image_page.get_text().split()))
            extracted=pdf.extract_image(next(iter(image_ids)))['image']
        with Image.open(io.BytesIO(png)) as expected,Image.open(io.BytesIO(extracted)) as actual:
            self.assertEqual(actual.convert('RGB').tobytes(),expected.convert('RGB').tobytes())

    def test_illustration_request_guards(self):
        self.require_api();self.pdf_case()
        other=self.store.create_session()['id']
        foreign=preserve_file(self.store,other,'other.pdf',self.source_pdf())
        for requests in ([{'file_id':foreign['id'],'page':1}],
                         [{'file_id':self.source['id'],'page':False}],
                         [{'file_id':self.source['id'],'page':2}],
                         [{'file_id':self.source['id'],'page':1}]*4,
                         [{'file_id':self.source['id'],'page':1,'caption':'Invented fact'}]):
            with self.assertRaises(ValueError):self.build(illustration_requests=requests)

    def source_pdf(self):
        from pathlib import Path
        return Path(self.store.get_file(self.source['id'])['path']).read_bytes()

    def test_resealed_image_tampering_still_blocks_export(self):
        self.require_api();self.pdf_case()
        d=self.build(illustration_requests=[{'file_id':self.source['id'],'page':1}])
        d['illustration_assets'][0]['data_base64']=base64.b64encode(b'Changed image').decode()
        d['record_sha256']=digest({k:v for k,v in d.items() if k!='record_sha256'})
        with self.store.connection() as db:
            db.execute('UPDATE conclusion_drafts SET record=? WHERE id=?',(json.dumps(d),d['id']))
        with self.assertRaises(ValueError):conclusions.export(self.store,self.sid,revision=1,format='docx')

    def test_resealed_source_page_change_is_rechecked_at_export(self):
        self.require_api();self.pdf_case()
        d=self.build(illustration_requests=[{'file_id':self.source['id'],'page':1}])
        d['content']['illustrations'][0]['page']=2
        d['content_sha256']=digest(d['content'])
        d['record_sha256']=digest({k:v for k,v in d.items() if k!='record_sha256'})
        with self.store.connection() as db:
            db.execute('UPDATE conclusion_drafts SET record=? WHERE id=?',(json.dumps(d),d['id']))
        with self.assertRaises(ValueError):conclusions.export(self.store,self.sid,revision=1,format='pdf')
