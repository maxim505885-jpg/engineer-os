import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class LocalCoreRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name))
        self.session = self.store.create_session()['id']
        self.source = preserve_file(self.store, self.session, 'roof.txt', 'Высота 4 м'.encode())

    def queue(self, **kwargs):
        return self.store.enqueue(self.session, 'Проверить кровлю, не фундамент',
                                  [self.source['id']], mode='CORE_RUN', **kwargs)

    def reply(self, summary='Черновой анализ', **changes):
        data = dict(status='UNCERTAINTY', summary=summary,
                    observations=[dict(text='В источнике указана высота', source_ids=[self.source['id']])],
                    limitations=['Измерения не подтверждены'])
        data.update(changes)
        return json.dumps(data, ensure_ascii=False)

    def model(self, replies):
        calls = []

        class Model:
            def chat(inner, messages):
                calls.append(messages)
                value = replies[len(calls)-1]
                if isinstance(value, Exception):
                    raise value
                return value

        return Model(), calls

    def result(self):
        return self.store.snapshot(self.session)['jobs'][0]['result']

    def test_roles_execute_in_order_with_tz_sources_and_persist(self):
        self.queue(requested_checks=['inspection', 'report'])
        model, calls = self.model([self.reply('Обследование'), self.reply('Отчёт'), self.reply('Сверка')])
        self.assertTrue(Worker(self.store, model).run_once())
        result = self.result()
        run = result['core_run']
        self.assertEqual([r['agent'] for r in run['results']],
                         ['inspection-agent', 'report-audit-agent', 'final-audit-agent'])
        self.assertEqual(len(calls), 3)
        self.assertIn('Проверить кровлю, не фундамент', str(calls[0]))
        self.assertIn('Высота 4 м', str(calls[0]))
        self.assertIn('Обследование', str(calls[-1]))
        self.assertTrue(all(r['execution'] == 'COMPLETED' for r in run['results']))
        self.assertTrue(all(not r['evidence_ids'] for r in run['results']))
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['final_audit'], 'NOT_RUN')
        self.assertEqual(run['status'], 'UNCERTAINTY')
        saved = Store(Path(self.tmp.name)).snapshot(self.session)['jobs'][0]['result']
        self.assertEqual(saved, result)

    def test_model_acceptance_claim_is_not_an_accepted_result(self):
        self.queue(requested_checks=['inspection'])
        model, _ = self.model([self.reply(status='ACCEPTED', acceptance_granted=True), self.reply()])
        Worker(self.store, model).run_once()
        run = self.result()['core_run']
        self.assertEqual(run['results'][0]['status'], 'ERROR')
        self.assertEqual(run['status'], 'ERROR')
        self.assertFalse(self.result()['acceptance_granted'])

    def test_role_failure_and_invalid_json_are_visible_to_audit(self):
        self.queue(requested_checks=['inspection', 'calculation'])
        model, calls = self.model([RuntimeError('SECRET must not appear'), 'not-json', self.reply()])
        Worker(self.store, model).run_once()
        run = self.result()['core_run']
        self.assertEqual([r['status'] for r in run['results']], ['ERROR', 'ERROR', 'UNCERTAINTY'])
        self.assertIn('ERROR', str(calls[-1]))
        self.assertNotIn('SECRET', json.dumps(self.result()))

    def test_missing_role_skill_is_retained_and_audit_continues(self):
        from engineering.core.skill_loader import SkillLoader
        original = SkillLoader.load

        def load(loader, name):
            if name == 'report-review':
                raise FileNotFoundError('private path')
            return original(loader, name)

        self.queue(requested_checks=['inspection', 'report'])
        model, calls = self.model([self.reply('Inspection draft'), self.reply('Audit draft')])
        with patch.object(SkillLoader, 'load', load):
            Worker(self.store, model).run_once()
        run = self.result()['core_run']
        self.assertEqual(len(calls), 2)
        self.assertEqual(run['results'][1]['execution'], 'FAILED')
        self.assertEqual(run['results'][1]['status'], 'ERROR')
        self.assertIn('ERROR', str(calls[-1]))
        self.assertEqual(run['results'][-1]['execution'], 'COMPLETED')
        self.assertNotIn('private path', json.dumps(self.result()))

    def test_unknown_source_reference_is_rejected(self):
        self.queue(requested_checks=['inspection'])
        model, _ = self.model([self.reply(observations=[dict(text='Invented', source_ids=['foreign-file'])]), self.reply()])
        Worker(self.store, model).run_once()
        self.assertEqual(self.result()['core_run']['results'][0]['status'], 'ERROR')

    def test_changed_original_stops_before_model(self):
        self.queue(requested_checks=['inspection'])
        Path(self.store.get_file(self.source['id'])['path']).write_bytes(b'changed')
        model, calls = self.model([])
        Worker(self.store, model).run_once()
        self.assertEqual(calls, [])
        self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'], 'FAILED')

    def test_source_changed_during_call_stops_without_accepting_reply(self):
        self.queue(requested_checks=['inspection'])
        calls = []

        class Model:
            def chat(inner, messages):
                calls.append(messages)
                Path(self.store.get_file(self.source['id'])['path']).write_bytes(b'changed')
                return self.reply()

        Worker(self.store, Model()).run_once()
        saved = self.store.snapshot(self.session)['jobs'][0]
        self.assertEqual(saved['state'], 'FAILED')
        self.assertEqual(len(calls), 1)
        self.assertFalse(saved['result']['acceptance_granted'])
        self.assertFalse(any(r['execution'] == 'COMPLETED' for r in saved['result']['core_run']['results']))

    def test_progress_survives_interruption_without_future_role_calls(self):
        self.queue(requested_checks=['inspection', 'report'])
        worker = Worker(self.store, None)
        calls = []

        class Model:
            def chat(inner, messages):
                calls.append(messages)
                if len(calls) == 2:
                    worker.stop_event.set()
                return self.reply()

        worker.model = Model()
        worker.run_once()
        saved = Store(Path(self.tmp.name)).snapshot(self.session)['jobs'][0]
        self.assertEqual(saved['state'], 'FAILED')
        self.assertEqual(len(calls), 2)
        self.assertEqual(saved['result']['core_run']['results'][0]['execution'], 'COMPLETED')
        self.assertEqual(saved['result']['core_run']['results'][-1]['execution'], 'NOT_RUN')

    def test_context_is_bounded_and_foreign_conversation_excluded(self):
        other = self.store.create_session()['id']
        preserve_file(self.store, other, 'secret.txt', b'FOREIGN_SECRET')
        huge = preserve_file(self.store, self.session, 'huge.txt', b'x'*80000)
        self.store.enqueue(self.session, 'Scope', [huge['id']], mode='CORE_RUN', requested_checks=['inspection'])
        model, calls = self.model([self.reply(observations=[]), self.reply(observations=[])])
        Worker(self.store, model).run_once()
        self.assertNotIn('FOREIGN_SECRET', str(calls))
        self.assertLess(len(str(calls[0])), 40000)
        self.assertTrue(self.result()['context_truncated'])


if __name__ == '__main__':
    unittest.main()
