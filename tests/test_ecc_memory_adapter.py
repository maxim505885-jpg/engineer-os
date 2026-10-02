import copy
import unittest

from engineering.memory.ecc_memory_adapter import ECCMemoryAdapter
from engineering.memory.external_memory import MemoryBoundaryError, MemoryTrust, memory_context


def fixture():
    return {'schema': 'ecc.memory.v1', 'id': 'mem_checkpoint', 'title': 'Checkpoint',
            'kind': 'handoff', 'scope': 'project', 'trust': 'unreviewed', 'status': 'active',
            'sourceHarness': 'codex', 'targetHarnesses': ['all'], 'tags': [], 'links': [],
            'createdAt': '2026-10-02T00:00:00.000Z', 'updatedAt': '2026-10-02T00:00:00.000Z',
            'body': 'Состояние: BLOCK. Не проверенный контекст.'}


class ECCMemoryAdapterTests(unittest.TestCase):
    def adapter(self, records=None, diagnostics=None, read_mutation=None):
        records = records if records is not None else [fixture()]
        summaries = [{k: v for k, v in m.items() if k != 'body'} for m in records]
        result = {'results': [{'memory': m, 'score': 1, 'excerpt': 'preview'} for m in summaries],
                  'diagnostics': diagnostics or {'invalidFileCount': 0, 'skippedSymlinkCount': 0,
                      'truncated': False, 'diagnosticsTruncated': False}}
        def read(memory_id, scope):
            record = copy.deepcopy(next(m for m in records if m['id'] == memory_id))
            if read_mutation: read_mutation(record)
            return {'memory': record}
        return ECCMemoryAdapter(lambda query: result, read, harness='codex')

    def test_full_body_is_context_with_digest_and_unverified_trust(self):
        record = self.adapter().search('checkpoint')[0]
        self.assertEqual(record.text, fixture()['body'])
        self.assertEqual(record.trust, MemoryTrust.UNVERIFIED)
        self.assertIn('sha256:', record.source_ref)
        self.assertEqual(memory_context((record,))[0]['evidentiary_status'], 'NOT_EVIDENCE')

    def test_empty_valid_search_is_empty_context(self):
        self.assertEqual(self.adapter(records=[]).search('none'), ())

    def test_bad_trust_scope_status_target_or_schema_is_rejected(self):
        for change in ({'trust': 'verified'}, {'scope': 'user'}, {'status': 'superseded'},
                       {'targetHarnesses': ['claude']}, {'schema': 'unknown'}, {'id': '../escape'},
                       {'sourceHarness': 'bad:name'}, {'createdAt': '2026-02-30T00:00:00.000Z'},
                       {'body': 'abc\x00def'}, {'body': '   '}):
            with self.subTest(change=change):
                record = fixture(); record.update(change)
                with self.assertRaises(MemoryBoundaryError): self.adapter([record]).search('test')

    def test_partial_scan_is_never_success(self):
        for key, value in (('truncated', True), ('diagnosticsTruncated', True),
                           ('invalidFileCount', 1), ('skippedSymlinkCount', 1)):
            d = {'invalidFileCount': 0, 'skippedSymlinkCount': 0,
                 'truncated': False, 'diagnosticsTruncated': False}; d[key] = value
            with self.subTest(key=key), self.assertRaises(MemoryBoundaryError):
                self.adapter(diagnostics=d).search('test')

    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(MemoryBoundaryError): self.adapter([fixture(), fixture()]).search('test')

    def test_changed_read_metadata_rejects_batch(self):
        with self.assertRaises(MemoryBoundaryError):
            self.adapter(read_mutation=lambda m: m.update(title='Changed')).search('test')

    def test_missing_read_and_transport_failure_do_not_leak_raw_error(self):
        def fail(*args): raise RuntimeError('PRIVATE-SYNTHETIC-MARKER')
        for adapter in (ECCMemoryAdapter(fail, fail, harness='codex'),
                        ECCMemoryAdapter(lambda q: {'results': [], 'diagnostics': {}}, fail, harness='codex')):
            with self.assertRaises(MemoryBoundaryError) as caught: adapter.search('test')
            self.assertNotIn('PRIVATE-SYNTHETIC-MARKER', str(caught.exception))

    def test_invalid_second_record_rejects_entire_batch(self):
        good = fixture(); bad = fixture(); bad.update(id='mem_invalid', trust='verified')
        with self.assertRaises(MemoryBoundaryError): self.adapter([good, bad]).search('test')

    def test_surrogate_query_fails_with_boundary_error(self):
        with self.assertRaises(MemoryBoundaryError): self.adapter().search('bad\ud800')

    def test_unknown_fields_and_missing_body_rejected(self):
        for change in ('unknown', 'body'):
            def mutate(record):
                if change == 'unknown': record['evidence_ids'] = ['fake']
                else: record.pop('body')
            with self.assertRaises(MemoryBoundaryError):
                self.adapter(read_mutation=mutate).search('test')


if __name__ == '__main__': unittest.main()
