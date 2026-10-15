import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.verify_pdf_recovery import verify


class PdfRecoveryVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source.pdf'
        self.source.write_bytes(b'test source bytes')
        sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.fragment = dict(source_sha256=sha, source_page=2,
                             bbox=[1, 2, 10, 20], coordinate_origin='TOPLEFT', text='value')
        cells = [dict(column_index=i, text='value' if i == 1 else '',
                      source_fragments=[dict(self.fragment, text='value' if i == 1 else '',
                                             bbox=[1+i*10, 2, 11+i*10, 20])]) for i in range(6)]
        self.manifest = dict(source_sha256=sha, rows=[dict(candidate_id='row-1',
            source_pages=[2], header_source_page=1, section=dict(text='Header', source_page=1),
            status='UNCERTAINTY', evidentiary_status='NOT_EVIDENCE', acceptance_granted=False, cells=cells)],
            review=dict(reviewer='Source reviewer', reviewed_at='2026-10-03T20:00:00Z',
                        scope='Source binding only'),
            context_fragments=[dict(self.fragment, source_page=1, text='Header')])

    def read(self, page, bbox):
        return 'Header' if page == 1 else 'value' if bbox[0] == 11 else ''

    def test_source_bound_empty_cells_remain_candidates(self):
        result = verify(self.source, self.manifest, page_sizes={1:(100,100),2:(100,100)}, read_text=self.read)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['verified_cells'], 6)
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['evidentiary_status'], 'NOT_EVIDENCE')
        self.assertEqual(result['document_status'], 'BLOCK')

    def test_mismatched_source_or_cell_text_blocks(self):
        for mutation in ['hash', 'text', 'page', 'bbox', 'blank', 'duplicate', 'accepted', 'context']:
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(self.manifest)
                cell = bad['rows'][0]['cells'][1]
                if mutation == 'hash':bad['source_sha256'] = '0'*64
                elif mutation == 'text':cell['text'] = 'invented'
                elif mutation == 'page':cell['source_fragments'][0]['source_page'] = 999
                elif mutation == 'bbox':cell['source_fragments'][0]['bbox'][0] = float('nan')
                elif mutation == 'blank':bad['rows'][0]['cells'][0]['source_fragments'][0]['text'] = 'invented'
                elif mutation == 'duplicate':bad['rows'].append(copy.deepcopy(bad['rows'][0]))
                elif mutation == 'accepted':bad['rows'][0]['acceptance_granted'] = True
                else:bad['context_fragments'][0]['text'] = 'Wrong header'
                with self.assertRaises(ValueError):
                    verify(self.source, bad, page_sizes={1:(100,100),2:(100,100)}, read_text=self.read)

    def test_cross_page_join_preserves_both_fragments(self):
        row = self.manifest['rows'][0]
        row['source_pages'] = [2,3]
        for cell in row['cells']:
            tail = dict(cell['source_fragments'][0], source_page=3, text='continued' if cell['column_index']==1 else '')
            cell['source_fragments'].append(tail)
        row['cells'][1]['text'] = 'value continued'
        read = lambda page,bbox: ('continued' if bbox[0]==11 else '') if page==3 else self.read(page,bbox)
        result = verify(self.source, self.manifest, page_sizes={1:(100,100),2:(100,100),3:(100,100)}, read_text=read)
        self.assertEqual(result['verified_fragments'], 12)
        self.assertEqual(result['source_pages'], [2,3])

    def test_empty_header_context_cannot_pass_even_with_empty_source(self):
        self.manifest['context_fragments'][0]['text'] = ''
        self.manifest['rows'][0]['section']['text'] = ''
        with self.assertRaises(ValueError):
            verify(self.source, self.manifest, page_sizes={1:(100,100),2:(100,100)},
                   read_text=lambda page,box: '' if page==1 else self.read(page,box))

    def test_recovery_exports_all_cells_and_source_context_without_acceptance(self):
        from scripts.verify_pdf_recovery import recover
        row = self.manifest['rows'][0]
        row['source_pages'] = [2, 3]
        for cell in row['cells']:
            cell['source_fragments'].append(dict(cell['source_fragments'][0], source_page=3, text=''))
        result = recover(self.source, self.manifest, project_id='project', document_id='document',
                         page_sizes={1:(100,100),2:(100,100),3:(100,100)},
                         read_text=lambda page,box: '' if page==3 else self.read(page,box))
        self.assertEqual(result['status'], 'UNCERTAINTY')
        self.assertEqual(result['document_status'], 'BLOCK')
        self.assertFalse(result['complete_document'])
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['evidentiary_status'], 'NOT_EVIDENCE')
        self.assertEqual((result['page_start'], result['page_end']), (1,3))
        self.assertEqual(len(result['blocks']), 7)
        cells = [b for b in result['blocks'] if b['kind']=='table_cell']
        self.assertEqual(len(cells), 6)
        self.assertEqual(sum(b['text']=='' for b in cells), 5)
        self.assertEqual([p['page_no'] for p in cells[1]['provenance']], [2,3])
        self.assertEqual(cells[1]['provenance'][0]['bbox']['left'], 11)
        self.assertEqual(result['rows'][0], row)
        self.assertEqual(result['context_fragments'], self.manifest['context_fragments'])
        self.assertEqual(result['project_id'], 'project')
        self.assertEqual(result['document_id'], 'document')

    def test_recovery_cannot_export_stale_or_altered_manifest(self):
        from scripts.verify_pdf_recovery import recover
        self.manifest['rows'][0]['cells'][1]['source_fragments'][0]['text'] = 'invented'
        with self.assertRaises(ValueError):
            recover(self.source, self.manifest, project_id='project', document_id='document',
                    page_sizes={1:(100,100),2:(100,100)}, read_text=self.read)

    def test_cli_failed_rerun_invalidates_old_candidates(self):
        import io, json, sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts.verify_pdf_recovery import main
        manifest = Path(self.temp.name)/'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        output = Path(self.temp.name)/'audit.json'
        candidates = Path(self.temp.name)/'candidates.json'
        candidates.write_text(json.dumps({'status':'UNCERTAINTY', 'blocks':[{'text':'stale'}]}))
        def opening(*args): raise RuntimeError('invalid PDF structure')
        argv = ['verify', str(self.source), str(manifest), '--output', str(output),
                '--candidate-output', str(candidates), '--project-id','project','--document-id','doc']
        with patch.dict(sys.modules, {'fitz':SimpleNamespace(open=opening)}), patch.object(sys,'argv',argv), patch('sys.stdout',io.StringIO()):
            self.assertEqual(main(),2)
        failed = json.loads(candidates.read_text())
        self.assertEqual(failed['blocks'], [])
        self.assertEqual(failed['status'], 'BLOCK')
        self.assertFalse(failed['complete_document'])

    def test_cli_candidate_output_cannot_alias_inputs_or_audit(self):
        import io, json, os, sys
        from unittest.mock import patch
        from scripts.verify_pdf_recovery import main
        manifest = Path(self.temp.name)/'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        output = Path(self.temp.name)/'audit.json'
        output.write_text('existing audit')
        hardlink = Path(self.temp.name)/'hardlink.json'
        os.link(manifest, hardlink)
        for candidate in (self.source, manifest, output, hardlink):
            argv = ['verify', str(self.source), str(manifest), '--output', str(output),
                    '--candidate-output', str(candidate), '--project-id','project','--document-id','doc']
            with patch.object(sys,'argv',argv), patch('sys.stderr',io.StringIO()):
                with self.assertRaises(SystemExit) as exc: main()
            self.assertEqual(exc.exception.code,2)
        self.assertEqual(output.read_text(), 'existing audit')
        self.assertEqual(json.loads(manifest.read_text()), self.manifest)

    def test_cli_rejects_output_hardlinked_to_manifest(self):
        import io, json, os, sys
        from unittest.mock import patch
        from scripts.verify_pdf_recovery import main
        manifest = Path(self.temp.name)/'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        original = manifest.read_bytes()
        output = Path(self.temp.name)/'output.json'
        os.link(manifest, output)
        with patch.object(sys, 'argv', ['verify', str(self.source), str(manifest), '--output',str(output)]), patch('sys.stderr',io.StringIO()):
            with self.assertRaises(SystemExit) as exc: main()
        self.assertEqual(exc.exception.code,2)
        self.assertEqual(manifest.read_bytes(),original)

    def test_cli_reports_block_for_non_pdf_and_malformed_pdf(self):
        import contextlib, io, json, sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts.verify_pdf_recovery import main
        manifest = Path(self.temp.name)/'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        output = Path(self.temp.name)/'output.json'
        for mode in ['image','malformed']:
            def opening(*args):
                if mode=='malformed':raise RuntimeError('invalid PDF structure')
                return contextlib.nullcontext(SimpleNamespace(is_pdf=False))
            with patch.dict(sys.modules, {'fitz':SimpleNamespace(open=opening)}), patch.object(sys,'argv',['verify',str(self.source),str(manifest),'--output',str(output)]), patch('sys.stdout',io.StringIO()):
                self.assertEqual(main(),2)
            self.assertEqual(json.loads(output.read_text())['status'],'BLOCK')
