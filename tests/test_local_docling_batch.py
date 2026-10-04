import unittest
import json
import tempfile
from pathlib import Path

from scripts.local_docling_batch import ranges, reusable_output


class LocalDoclingBatchTests(unittest.TestCase):
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
