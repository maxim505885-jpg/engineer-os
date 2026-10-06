import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register

class LocalPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name);self.session=self.store.create_session()['id']

    def source(self,rotation=0,large=False):
        import fitz
        with fitz.open() as pdf:
            p=pdf.new_page(width=4000 if large else 595,height=5000 if large else 842)
            p.insert_text((40,40),'height 4m');p.set_rotation(rotation);data=pdf.tobytes()
        f=preserve_file(self.store,self.session,'original.pdf',data)
        r=register(self.store,self.session,file_id=f['id'],page=1,quote='height 4m',statement='Unverified source')
        return f,r,data

    def preview(self,r,session=None):
        try:from engineering.local_app.preview import render_preview
        except ImportError:self.fail('Source page preview missing')
        return render_preview(self.store,session or self.session,r['id'])

    def test_preview_is_bounded_png_and_original_unchanged(self):
        from PIL import Image
        f,r,data=self.source(large=True);png=self.preview(r)
        self.assertTrue(png.startswith(b'\x89PNG\r\n\x1a\n'))
        with Image.open(io.BytesIO(png)) as im:self.assertLessEqual(max(im.size),1601)
        self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),data)
        self.assertEqual(hashlib.sha256(data).hexdigest(),f['sha256'])

    def test_rotated_preview_has_highlight_at_rotated_location(self):
        import fitz
        from PIL import Image
        f,r,data=self.source(rotation=90);png=self.preview(r)
        with fitz.open(stream=data,filetype='pdf') as pdf:
            page=pdf[0];box=fitz.Rect(*r['provenance']['regions'][0].values())*page.rotation_matrix
            scale=min(1.5,1600/max(page.rect.width,page.rect.height))
        with Image.open(io.BytesIO(png)) as im:
            rgb=im.convert('RGB');red=[(x,y) for y in range(rgb.height) for x in range(rgb.width) if (lambda c:c[0]>180 and c[1]<100 and c[2]<100)(rgb.getpixel((x,y)))]
            self.assertTrue(red,'Native quote should be outlined')
            self.assertTrue(all(box.x0*scale-4<=x<=box.x1*scale+4 and box.y0*scale-4<=y<=box.y1*scale+4 for x,y in red))

    def test_foreign_session_and_changed_original_cannot_preview(self):
        f,r,_=self.source();other=self.store.create_session()['id']
        with self.assertRaises(ValueError):self.preview(r,other)
        Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.preview(r)

    def test_non_pdf_and_unreadable_source_return_visible_errors(self):
        for name,data,page in [('source.txt',b'123',None),('broken.pdf',b'broken',1)]:
            f=preserve_file(self.store,self.session,name,data)
            r=register(self.store,self.session,file_id=f['id'],page=page,quote='123',statement='Unknown')
            with self.assertRaises(ValueError):self.preview(r)

    def test_rotated_cropped_pages_keep_source_outline_in_all_orientations(self):
        import fitz
        from PIL import Image
        for rotation in (90,180,270):
            with self.subTest(rotation=rotation),fitz.open() as pdf:
                p=pdf.new_page(width=600,height=800);p.insert_text((150,200),'height 4m')
                p.set_cropbox(fitz.Rect(100,100,500,700));p.set_rotation(rotation);data=pdf.tobytes()
                f=preserve_file(self.store,self.session,'cropped.pdf',data)
                r=register(self.store,self.session,file_id=f['id'],page=1,quote='height 4m',statement='Unknown')
                raw=r['provenance']['regions'][0]
                box=fitz.Rect(raw['left'],raw['top'],raw['right'],raw['bottom'])*p.rotation_matrix
                scale=min(1.5,1600/max(p.rect.width,p.rect.height))
                with Image.open(io.BytesIO(self.preview(r))) as im:
                    rgb=im.convert('RGB');red=[(x,y) for y in range(rgb.height) for x in range(rgb.width) if (lambda c:c[0]>180 and c[1]<100 and c[2]<100)(rgb.getpixel((x,y)))]
                    self.assertTrue(red,'CropBox plus rotation must not lose outline')
                    self.assertTrue(all(box.x0*scale-4<=x<=box.x1*scale+4 and box.y0*scale-4<=y<=box.y1*scale+4 for x,y in red))
                self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),data)
