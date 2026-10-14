import unittest
import json
import tempfile
from pathlib import Path

from scripts.local_docling_batch import ranges, reusable_output, run_chunk


class LocalDoclingBatchTests(unittest.TestCase):
    def test_run_chunk_reports_partial_output_as_block(self):
        import io
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts.local_docling_batch import CHECK_VERSION
        from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);args=SimpleNamespace(source=root/'source.pdf',output_dir=root,
                sha256=SOURCE_SHA256,project_id=PROJECT_ID,document_id=DOCUMENT_ID)
            def run(command,**_):
                output=Path(command[command.index('--output-json')+1])
                output.write_text(json.dumps(dict(source_sha256=SOURCE_SHA256,project_id=PROJECT_ID,
                    document_id=DOCUMENT_ID,page_start=1,page_end=1,status='BLOCK',
                    document_status='BLOCK',evidentiary_status='NOT_EVIDENCE',
                    complete_document=False,acceptance_granted=False,
                    limitations=['TABLE_CAPTION_WITHOUT_VERIFIED_ROWS'],
                    blocks=[dict(text='Text',provenance=[dict(page_no=1)])])),encoding='utf-8')
                return SimpleNamespace(returncode=0,stdout='',stderr='')
            with patch('scripts.local_docling_batch.subprocess.run',side_effect=run),patch('sys.stdout',io.StringIO()) as output:
                self.assertEqual(run_chunk(args,1,1),0)
            self.assertIn('BLOCK (partial retained)',output.getvalue())
            audit=json.loads((root/'pages-0001-0001.audit.json').read_text(encoding='utf-8'))
            self.assertEqual(audit['check_version'],CHECK_VERSION)

    def test_resumable_partial_block_is_reviewable_but_never_complete(self):
        from scripts.local_docling_batch import CHECK_VERSION
        from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
        from scripts.v4_extraction_review import review
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stem='pages-0001-0001'
            output=dict(project_id=PROJECT_ID,document_id=DOCUMENT_ID,
                source_sha256=SOURCE_SHA256,page_start=1,page_end=1,parser='docling',
                status='BLOCK',document_status='BLOCK',evidentiary_status='NOT_EVIDENCE',
                complete_document=False,acceptance_granted=False,
                limitations=['TABLE_CAPTION_WITHOUT_VERIFIED_ROWS'],
                blocks=[dict(block_id='text-1',kind='text',text='Observed text',provenance=[dict(page_no=1)])])
            path=root/(stem+'.json');path.write_text(json.dumps(output),encoding='utf-8')
            self.assertTrue(reusable_output(path,first=1,last=1,sha256=SOURCE_SHA256,
                project_id=PROJECT_ID,document_id=DOCUMENT_ID))
            for changes in (dict(acceptance_granted=True),dict(complete_document=True),dict(limitations=[])):
                invalid=dict(output,**changes);path.write_text(json.dumps(invalid),encoding='utf-8')
                self.assertFalse(reusable_output(path,first=1,last=1,sha256=SOURCE_SHA256,
                    project_id=PROJECT_ID,document_id=DOCUMENT_ID))
            path.write_text(json.dumps(output),encoding='utf-8')
            (root/(stem+'.audit.json')).write_text(json.dumps(dict(
                source_sha256=SOURCE_SHA256,project_id=PROJECT_ID,document_id=DOCUMENT_ID,
                page_start=1,page_end=1,check_version=CHECK_VERSION,exit_code=0)),encoding='utf-8')
            result=review(root,1)
            self.assertEqual(result['partial_chunks'],1)
            self.assertEqual(result['pages_with_partial_extraction'],[1])
            self.assertEqual(result['review_queue'][0]['reason'],'EXTRACTION_BLOCKED')
            self.assertEqual(result['status'],'BLOCK')
            self.assertFalse(result['acceptance_granted'])

    def test_raw_recovery_outputs_cannot_alias_raw_input_or_docling_result(self):
        import sys
        from unittest.mock import patch
        from scripts.local_docling_batch import main
        for mode in ('raw-sidecar','combined-docling'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                out=Path(directory);raw=out/'raw.json'
                target=out/('reviewed-regions.candidates.json' if mode=='raw-sidecar' else 'pages-0001-0001.json')
                target.write_text('original')
                if mode=='raw-sidecar':raw=target
                else:(out/'combined-extraction.json').symlink_to(target)
                args=['batch','source.pdf','--start','1','--end','1','--sha256','a'*64,
                      '--project-id','p','--document-id','d','--output-dir',str(out),
                      '--raw-export',str(raw),'--reviewed-manifest','missing-map.json','--reviewed-only']
                with patch.object(sys,'argv',args):
                    try:main()
                    except SystemExit:pass
                self.assertEqual(target.read_text(),'original')

    def test_raw_recovery_requires_a_single_reviewed_only_page(self):
        import sys
        from unittest.mock import patch
        from scripts.local_docling_batch import main
        args=['batch','source.pdf','--start','1','--end','2','--sha256','a'*64,
              '--project-id','p','--document-id','d','--output-dir','out',
              '--raw-export','raw.json','--reviewed-manifest','map.json','--reviewed-only']
        with patch.object(sys,'argv',args):
            with self.assertRaises(SystemExit) as exit_result:main()
        self.assertEqual(exit_result.exception.code,2)

    def test_raw_recovery_failure_writes_a_blocked_combined_export(self):
        import sys
        from unittest.mock import patch
        from scripts.local_docling_batch import main
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'out'
            args=['batch','source.pdf','--start','1','--end','1','--sha256','a'*64,
                  '--project-id','p','--document-id','d','--output-dir',str(out),
                  '--raw-export','missing-raw.json','--reviewed-manifest','missing-map.json','--reviewed-only']
            with patch.object(sys,'argv',args):
                try:code=main()
                except SystemExit:self.fail('raw recovery is not integrated into the existing batch')
            self.assertEqual(code,2)
            result=json.loads((out/'combined-extraction.json').read_text())
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['blocks'],[])

    def test_reviewed_grid_scope_supports_schema2_without_accepting_other_pages(self):
        from scripts.local_docling_batch import reviewed_scope
        manifest = dict(schema_version=2, source_sha256='a'*64,
                        tables=[dict(source_page=259)])
        self.assertTrue(reviewed_scope(manifest, first=259, last=259, sha256='a'*64))
        for page in (258, 260, True):
            manifest['tables'][0]['source_page'] = page
            with self.assertRaises(ValueError):
                reviewed_scope(manifest, first=259, last=259, sha256='a'*64)
        manifest.update(schema_version=99, rows=[dict(source_pages=[259])])
        with self.assertRaises(ValueError):
            reviewed_scope(manifest, first=259, last=259, sha256='a'*64)

    def test_grid_export_reports_source_coverage_without_promoting_completeness(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts.local_docling_batch import export_reviewed_regions
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            manifest = dest/'map.json'
            manifest.write_text(json.dumps(dict(schema_version=2, source_sha256='a'*64,
                tables=[dict(source_page=259)])))
            args = SimpleNamespace(source=dest/'source.pdf', reviewed_manifest=manifest,
                output_dir=dest, start=259, end=259, sha256='a'*64,
                project_id='project', document_id='document')
            payload = dict(schema_version=2, source_sha256='a'*64,
                project_id='project', document_id='document', status='UNCERTAINTY',
                document_status='BLOCK', evidentiary_status='NOT_EVIDENCE',
                acceptance_granted=False, complete_document=False,
                tables=[dict(source_page=259, cells=[{},{}])],
                source_binding_audit=dict(status='PASS', source_sha256='a'*64,
                    verified_tables=1, verified_cells=2, verified_grid_slots=3,
                    source_pages=[259], document_status='BLOCK',
                    evidentiary_status='NOT_EVIDENCE', acceptance_granted=False))
            def subprocess(*_, **__):
                (dest/'reviewed-regions.candidates.json').write_text(json.dumps(payload))
                return SimpleNamespace(returncode=0)
            with patch('scripts.local_docling_batch.subprocess.run', side_effect=subprocess):
                result = export_reviewed_regions(args)
                self.assertEqual(result['source_binding_status'], 'PASS')
                self.assertEqual(result['coverage']['verified_cells'], 2)
                self.assertEqual(result['coverage']['verified_tables'], 1)
                self.assertEqual(result['coverage']['level'], 'DECLARED_REGIONS_ONLY')
                self.assertFalse(result['coverage']['complete_page'])
                for changes in [dict(acceptance_granted=True),dict(project_id='other'),
                                dict(complete_document=True),dict(document_status='ACCEPTED')]:
                    original = dict(payload)
                    payload.update(changes)
                    self.assertEqual(export_reviewed_regions(args)['status'], 'BLOCK')
                    self.assertEqual(json.loads((dest/'reviewed-regions.candidates.json').read_text())['blocks'], [])
                    payload.clear();payload.update(original)

    def test_reviewed_region_scope_requires_matching_hash_and_body_pages(self):
        from scripts.local_docling_batch import reviewed_scope
        manifest = {'source_sha256':'a'*64, 'rows':[{'source_pages':[396,397]}]}
        self.assertTrue(reviewed_scope(manifest, first=396, last=404, sha256='a'*64))
        for first,last,sha in [(397,404,'a'*64),(396,404,'b'*64)]:
            with self.assertRaises(ValueError):
                reviewed_scope(manifest,first=first,last=last,sha256=sha)

    def test_reviewed_only_never_reports_complete_extraction_or_calls_docling(self):
        import io,sys
        from unittest.mock import patch
        from scripts.local_docling_batch import main
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'out'
            argv=['batch','source.pdf','--start','396','--end','404','--sha256','a'*64,
                  '--project-id','project','--document-id','document','--output-dir',str(dest),
                  '--reviewed-manifest','manifest.json','--reviewed-only']
            with patch.object(sys,'argv',argv), patch('scripts.local_docling_batch.run_chunk',side_effect=AssertionError('must not parse')), patch('scripts.local_docling_batch.export_reviewed_regions',return_value={'status':'UNCERTAINTY','source_binding_status':'PASS'}), patch('sys.stdout',io.StringIO()):
                self.assertEqual(main(),2)
            result=json.loads((dest/'batch-review-summary.json').read_text())
            self.assertEqual(result['status'],'BLOCK')
            self.assertFalse(result['complete_document'])
            self.assertFalse(result['acceptance_granted'])
            self.assertEqual(result['reviewed_regions']['status'],'UNCERTAINTY')
            self.assertEqual(result['docling_status'],'NOT_RUN')

    def test_recovery_does_not_hide_failed_docling_chunks(self):
        import io,sys
        from unittest.mock import patch
        from scripts.local_docling_batch import main
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'out'
            argv=['batch','source.pdf','--start','396','--end','396','--sha256','a'*64,
                  '--project-id','project','--document-id','document','--output-dir',str(dest),
                  '--reviewed-manifest','manifest.json']
            with patch.object(sys,'argv',argv), patch('scripts.local_docling_batch.run_chunk',return_value=2), patch('scripts.local_docling_batch.export_reviewed_regions',return_value={'status':'UNCERTAINTY','source_binding_status':'PASS'}), patch('sys.stdout',io.StringIO()):
                self.assertEqual(main(),2)
            result=json.loads((dest/'batch-review-summary.json').read_text())
            self.assertEqual(result['docling_status'],'BLOCK')
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['blocked_ranges'],[[396,396]])

    def test_invalid_reviewed_scope_clears_stale_sidecars_only(self):
        from types import SimpleNamespace
        from scripts.local_docling_batch import export_reviewed_regions
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)
            manifest=dest/'map.json'
            manifest.write_text(json.dumps({'source_sha256':'a'*64,'rows':[{'source_pages':[405]}]}))
            existing=dest/'pages-0396-0404.audit.json';existing.write_text('original Docling BLOCK')
            for name in ('reviewed-regions.audit.json','reviewed-regions.candidates.json'):
                (dest/name).write_text('{"status":"UNCERTAINTY","blocks":["stale"]}')
            args=SimpleNamespace(source=dest/'source.pdf',reviewed_manifest=manifest,
                                 output_dir=dest,start=396,end=404,sha256='a'*64)
            self.assertEqual(export_reviewed_regions(args)['status'],'BLOCK')
            self.assertEqual(json.loads((dest/'reviewed-regions.candidates.json').read_text())['blocks'],[])
            self.assertEqual(existing.read_text(),'original Docling BLOCK')

    def test_batch_rejects_summary_hardlinked_to_source_before_writes(self):
        import io,os,sys
        from unittest.mock import patch
        from scripts.local_docling_batch import main
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory);source=dest/'source.pdf';source.write_bytes(b'original source')
            os.link(source,dest/'batch-review-summary.json')
            argv=['batch',str(source),'--start','396','--end','404','--sha256','a'*64,
                  '--project-id','project','--document-id','document','--output-dir',str(dest),
                  '--reviewed-manifest',str(dest/'map.json'),'--reviewed-only']
            with patch.object(sys,'argv',argv),patch('sys.stderr',io.StringIO()):
                with self.assertRaises(SystemExit) as exc:main()
            self.assertEqual(exc.exception.code,2)
            self.assertEqual(source.read_bytes(),b'original source')

    def test_review_sidecars_cannot_alias_original_docling_results(self):
        import os
        from types import SimpleNamespace
        from scripts.local_docling_batch import export_reviewed_regions
        for alias in ('hardlink','symlink'):
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as directory:
                dest=Path(directory)
                original=dest/'pages-0396-0404.audit.json';original.write_text('original Docling BLOCK')
                output=dest/'reviewed-regions.audit.json'
                if alias=='hardlink':os.link(original,output)
                else:output.symlink_to(original)
                args=SimpleNamespace(source=dest/'source.pdf',reviewed_manifest=dest/'map.json',
                                     output_dir=dest,start=396,end=404,sha256='a'*64)
                with self.assertRaises(ValueError):export_reviewed_regions(args)
                self.assertEqual(original.read_text(),'original Docling BLOCK')

    def test_ranges_are_bounded_and_cover_each_page_once(self):
        self.assertEqual(list(ranges(11, 16, 2)), [(11, 12), (13, 14), (15, 16)])
        with self.assertRaises(ValueError):
            list(ranges(1, 534, 2))

    def test_resume_rejects_corrupted_or_misbound_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pages-0015-0016.json"
            expected = dict(first=15, last=16, sha256="a" * 64,
                            project_id="project", document_id="document")
            payload = {"page_start": 15, "page_end": 16,
                       "source_sha256": "a" * 64, "project_id": "project",
                       "document_id": "document", "status": "UNCERTAINTY",
                       "blocks": [{"text": "sample", "provenance": [{"page_no": 15}]}]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertTrue(reusable_output(path, **expected))
            payload["blocks"][0]["provenance"][0]["page_no"] = 17
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertFalse(reusable_output(path, **expected))
            path.write_text("{bad", encoding="utf-8")
            self.assertFalse(reusable_output(path, **expected))


if __name__ == "__main__":
    unittest.main()
