import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
import zipfile

from engineering.local_app.office import W, M, OfficeError
try:
    from engineering.local_app import word_formula_preview as preview
except ImportError:
    preview = None


def document(formula=None, extras=None, part='word/document.xml'):
    formula = formula or '<m:oMath><m:r><m:t>x</m:t></m:r></m:oMath>'
    root = f'<w:document xmlns:w="{W[1:-1]}" xmlns:m="{M[1:-1]}"><w:body><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t>SECRET</w:t></w:r>{formula}</w:p></w:body></w:document>'
    parts = {part: root}
    parts.update(extras or {})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for name, text in parts.items():
            z.writestr(name, text)
    return stream.getvalue()


class FormulaPreviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(preview, 'Formula preview implementation missing')

    def test_scaffold_contains_selected_exact_formula_and_properties_only(self):
        data = document('<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr><m:oMath><m:r><m:t>x</m:t></m:r></m:oMath><m:oMath><m:r><m:t>y</m:t></m:r></m:oMath></m:oMathPara>')
        scaffold, dossier = preview._scaffold(data, 'word/document.xml', 1)
        with zipfile.ZipFile(io.BytesIO(scaffold)) as z:
            root = ET.fromstring(z.read('word/document.xml'))
            selected = list(root.iter(M+'oMath'))
            self.assertEqual(len(selected), 1)
            self.assertEqual(list(selected[0].iter(M+'t'))[0].text, 'y')
            self.assertNotIn(b'SECRET', z.read('word/document.xml'))
            self.assertIsNotNone(root.find('.//'+W+'pPr/'+W+'jc'))
            self.assertIsNotNone(root.find('.//'+M+'oMathParaPr/'+M+'jc'))
        source = ET.fromstring(zipfile.ZipFile(io.BytesIO(data)).read('word/document.xml'))
        fragment = list(source.iter(M+'oMath'))[1]
        fragment.tail = None
        self.assertEqual(dossier['formula_sha256'], hashlib.sha256(ET.tostring(fragment, encoding='utf-8')).hexdigest())
        self.assertEqual(dossier['source_sha256'], hashlib.sha256(data).hexdigest())

    def test_passive_support_parts_retained_but_source_active_payloads_absent(self):
        styles = f'<w:styles xmlns:w="{W[1:-1]}"><w:style w:type="paragraph" w:styleId="Custom"><w:rPr><w:rFonts w:ascii="Source Font"/></w:rPr></w:style></w:styles>'
        data = document(extras={'word/styles.xml': styles, 'word/fontTable.xml': f'<w:fonts xmlns:w="{W[1:-1]}"><w:font w:name="Source Font"><w:family w:val="roman"/></w:font></w:fonts>', 'word/vbaProject.bin': b'BAD', 'word/embeddings/evil.bin': b'BAD', 'word/_rels/document.xml.rels': '<Relationships><Relationship TargetMode="External" Target="https://example.invalid"/></Relationships>'})
        scaffold, metadata = preview._scaffold(data, 'word/document.xml', 0)
        with zipfile.ZipFile(io.BytesIO(scaffold)) as z:
            self.assertIn('word/styles.xml', z.namelist())
            self.assertIn('word/fontTable.xml', z.namelist())
            self.assertNotIn('word/vbaProject.bin', z.namelist())
            self.assertNotIn('word/embeddings/evil.bin', z.namelist())
            self.assertNotIn(b'example.invalid', z.read('word/_rels/document.xml.rels'))
        self.assertIn('Source Font', metadata['fonts']['declared_families'])

    def test_rejects_unsafe_formula_and_relationship_attributes(self):
        for xml in ('<m:oMath><w:object/></m:oMath>', '<m:oMath xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:id="bad"/>', '<m:oMath><w:instrText>INCLUDETEXT https://bad</w:instrText></m:oMath>'):
            with self.subTest(xml=xml), self.assertRaises(OfficeError):
                preview._scaffold(document(xml), 'word/document.xml', 0)

    def test_invalid_inputs_are_bounded_before_converter(self):
        for part, ordinal in (('../word/document.xml', 1), ('word/document.xml', -1), ('word/document.xml', True), ('word/document.xml', 1), ('word/missing.xml', 1)):
            with self.subTest(part=part, ordinal=ordinal), self.assertRaises(OfficeError):
                preview.render_formula(document(), part, ordinal)
        with patch.object(preview, 'MAX_SOURCE_BYTES', 4), self.assertRaises(OfficeError):
            preview.render_formula(document(), 'word/document.xml', 0)

    def test_formula_identity_matches_source_asset_with_sibling_tail(self):
        data = document('<m:oMath><m:r><m:t>x</m:t></m:r></m:oMath>PRIVATE_SIBLING')
        scaffold, metadata = preview._scaffold(data, 'word/document.xml', 0)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            fragment = next(ET.fromstring(z.read('word/document.xml')).iter(M+'oMath'))
        self.assertEqual(metadata['formula_sha256'], hashlib.sha256(ET.tostring(fragment)).hexdigest())
        with zipfile.ZipFile(io.BytesIO(scaffold)) as z:
            self.assertNotIn(b'PRIVATE_SIBLING', z.read('word/document.xml'))

    def test_blank_pdf_does_not_masquerade_as_formula_preview(self):
        import fitz
        pdf = fitz.open(); pdf.new_page(width=200, height=200)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'blank.pdf'; path.write_bytes(pdf.tobytes()); pdf.close()
            with self.assertRaisesRegex(OfficeError, 'visible'):
                preview._raster_pdf(path)

    def test_nonstandard_auxiliary_part_can_render_source_bound_scaffold(self):
        part = 'word/notes/custom-note.xml'
        xml = f'<w:footnotes xmlns:w="{W[1:-1]}" xmlns:m="{M[1:-1]}"><w:footnote w:id="3"><w:p><m:oMath><m:r><m:t>n</m:t></m:r></m:oMath></w:p></w:footnote></w:footnotes>'
        scaffold, metadata = preview._scaffold(document(extras={part: xml}), part, 0)
        self.assertEqual(metadata['part'], part)
        with zipfile.ZipFile(io.BytesIO(scaffold)) as z:
            root = ET.fromstring(z.read('word/document.xml'))
            self.assertEqual(list(root.iter(M+'t'))[0].text, 'n')

    def test_font_embedding_links_and_styles_external_attrs_are_discarded(self):
        relationship_namespace = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        fonts = f'<w:fonts xmlns:w="{W[1:-1]}" xmlns:r="{relationship_namespace}"><w:font w:name="A"><w:embedRegular r:id="embed"/></w:font></w:fonts>'
        styles = f'<w:styles xmlns:w="{W[1:-1]}" xmlns:r="{relationship_namespace}"><w:style r:id="external" w:styleId="A"><w:rPr><w:rFonts w:ascii="A"/></w:rPr></w:style></w:styles>'
        scaffold, _ = preview._scaffold(document(extras={'word/fontTable.xml': fonts, 'word/styles.xml': styles, 'word/_rels/fontTable.xml.rels': '<external/>', 'word/fonts/evil.odttf': b'unsafe'}), 'word/document.xml', 0)
        with zipfile.ZipFile(io.BytesIO(scaffold)) as z:
            self.assertNotIn(b'embedRegular', z.read('word/fontTable.xml'))
            self.assertNotIn(relationship_namespace.encode(), z.read('word/styles.xml'))
            self.assertNotIn('word/fonts/evil.odttf', z.namelist())
            self.assertNotIn('word/_rels/fontTable.xml.rels', z.namelist())

    def test_entities_rejected(self):
        data = document(extras={'word/document.xml': '<!DOCTYPE x [<!ENTITY x SYSTEM "file:///tmp/secret">]><x>&x;</x>'})
        with self.assertRaises(OfficeError):
            preview._scaffold(data, 'word/document.xml', 0)

    def test_missing_converter_reports_block(self):
        with patch.object(preview, '_converter', return_value=None), self.assertRaisesRegex(OfficeError, 'unavailable'):
            preview.render_formula(document(), 'word/document.xml', 0)

    def test_pdf_pixel_budget_and_page_count_fail_closed(self):
        import fitz
        for pages, width in ((2, 200), (1, 100000)):
            pdf = fitz.open()
            for _ in range(pages):
                pdf.new_page(width=width, height=200)
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp)/'input.pdf'; path.write_bytes(pdf.tobytes()); pdf.close()
                with self.assertRaises(OfficeError):
                    preview._raster_pdf(path)

    @unittest.skipUnless(os.sys.platform == 'linux', 'Linux seccomp enforcement')
    def test_linux_converter_child_cannot_open_network_socket(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(OfficeError, 'failed'):
                preview._run([os.sys.executable, '-c', 'import socket; socket.socket()'], Path(temp), 5, 'network.log')
            self.assertIn('Operation not permitted', (Path(temp)/'network.log').read_text())

    @unittest.skipUnless(os.sys.platform == 'linux', 'Linux descendant process groups')
    def test_timeout_terminates_descendant_converter_process(self):
        import time
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = "import subprocess,sys,time; from pathlib import Path; child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);Path('child.pid').write_text(str(child.pid));time.sleep(30)"
            with self.assertRaisesRegex(OfficeError, 'timeout'):
                preview._run([os.sys.executable, '-c', code], root, 0.5, 'timeout.log')
            pid = int((root/'child.pid').read_text())
            # An unreaped zombie is terminated; it cannot continue work.
            path = Path('/proc')/str(pid)/'stat'
            self.assertTrue(not path.exists() or path.read_text().split(') ', 1)[1].startswith('Z'))

    @unittest.skipUnless(os.sys.platform == 'linux', 'Linux process cleanup')
    def test_converter_log_budget_terminates_without_waiting_for_timeout(self):
        with tempfile.TemporaryDirectory() as temp:
            code = "import os,time;os.write(1,b'x'*(17*1024*1024));time.sleep(30)"
            with self.assertRaisesRegex(OfficeError, 'log byte limit'):
                preview._run([os.sys.executable, '-c', code], Path(temp), 1, 'oversize.log')

    @unittest.skipUnless(os.sys.platform == 'linux', 'Linux process cleanup')
    def test_converter_success_does_not_leave_background_descendants(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = "import subprocess,sys;from pathlib import Path;child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);Path('child.pid').write_text(str(child.pid))"
            preview._run([os.sys.executable, '-c', code], root, 5, 'child.log')
            path = Path('/proc')/(root/'child.pid').read_text()/'stat'
            self.assertTrue(not path.exists() or path.read_text().split(') ', 1)[1].startswith('Z'))

    def test_formula_and_support_xml_limits_fail_before_launch(self):
        for setting, maximum in (('MAX_FORMULA_XML', 4), ('MAX_NODES', 1), ('MAX_PART_XML', 4), ('MAX_SCAFFOLD', 4)):
            with self.subTest(setting=setting), patch.object(preview, setting, maximum), patch.object(preview, '_run') as run:
                with self.assertRaises(OfficeError):
                    preview.render_formula(document(), 'word/document.xml', 0)
                run.assert_not_called()

    def test_windows_dossier_does_not_claim_network_enforcement(self):
        import fitz
        def controlled_run(command, root, timeout, log_name):
            if log_name == 'conversion.log':
                pdf = fitz.open(); page = pdf.new_page(width=200, height=200); page.insert_text((20, 30), 'x')
                (root/'out'/'formula.pdf').write_bytes(pdf.tobytes()); pdf.close()
            if log_name == 'raster.log':
                png, metadata = preview._raster_pdf(Path(command[-3]))
                Path(command[-2]).write_bytes(png)
                import json
                Path(command[-1]).write_text(json.dumps(metadata))
            return 'Controlled converter identity'
        with patch.object(preview.sys, 'platform', 'win32'), patch.object(preview, '_converter', return_value=Path(os.sys.executable)), patch.object(preview, '_run', side_effect=controlled_run):
            _, metadata = preview.render_formula(document(), 'word/document.xml', 0)
        self.assertFalse(metadata['network_denied'])
        self.assertIn('NETWORK_DENIAL_NOT_ENFORCED', metadata['limitations'])
        self.assertFalse(metadata['layout_verified'])

    @unittest.skipUnless(os.environ.get('ENGINEER_OS_TEST_FORMULA_RENDER') == '1', 'Explicit real converter integration')
    def test_real_fraction_render_has_pixels_bound_hashes_and_unverified_status(self):
        data = document('<m:oMath><m:f><m:num><m:r><m:t>12</m:t></m:r></m:num><m:den><m:r><m:t>3</m:t></m:r></m:den></m:f></m:oMath>')
        png, dossier = preview.render_formula(data, 'word/document.xml', 0)
        from PIL import Image, ImageChops
        image = Image.open(io.BytesIO(png)).convert('RGB')
        self.assertIsNotNone(ImageChops.difference(image, Image.new('RGB', image.size, 'white')).getbbox())
        self.assertEqual(dossier['preview_sha256'], hashlib.sha256(png).hexdigest())
        self.assertEqual(dossier['status'], 'UNCERTAINTY')
        self.assertFalse(dossier['layout_verified']); self.assertFalse(dossier['math_verified'])
        self.assertFalse(dossier['font_substitution_verified'])
        self.assertEqual(dossier['network_denied'], os.sys.platform == 'linux')
        self.assertTrue(dossier['converter']['executable_sha256'])
        self.assertTrue(dossier['converter']['version'])
        self.assertLessEqual(image.width*image.height, preview.MAX_PIXELS)
