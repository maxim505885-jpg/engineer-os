import json
import unittest
from dataclasses import replace

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.codex_runtime import CodexAppServerClient, CodexRuntimeAdapter
from engineering.core.engineer_core import AgentRuntimeAdapter


class CoreIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.task = EngineerTask('integrity', 'Проверить только покрытия согласно ТЗ',
                                 (MaterialRef('m1', 'report', 'report.pdf'),), ('inspection',))
        self.gate_calls = []
        self.core = EngineerCore(acceptance_gate=lambda state: self.gate_calls.append(state) or True)

    def accepted_state(self):
        state = self.core.plan(self.task)
        self.core.collect(state, [
            AgentResult(self.task.task_id, 'inspection-agent', AgentStatus.PASS, evidence_ids=('e1',)),
            AgentResult(self.task.task_id, 'final-audit-agent', AgentStatus.PASS,
                        evidence_ids=('e1',), checked_agents=('inspection-agent',)),
        ])
        return state

    def test_invalid_status_never_reaches_gate(self):
        state = self.core.plan(self.task)
        for status in ('INVENTED_STATUS', 'PASS', None):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.core.collect(state, [AgentResult(self.task.task_id, 'inspection-agent', status,
                                                     evidence_ids=('e1',))])
        self.assertEqual(state.results, [])
        self.assertEqual(self.gate_calls, [])

    def test_string_proof_is_not_an_id_collection(self):
        state = self.core.plan(self.task)
        for fields in ({'evidence_ids': 'e1'}, {'evidence_ids': {'e1': True}},
                       {'checked_agents': 'inspection-agent'},
                       {'acceptance_basis': {'domain': 'proof-id'}}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.core.collect(state, [replace(self.accepted_state().results[0], **fields)])
        self.assertEqual(state.results, [])

    def test_final_status_revalidates_results_before_gate(self):
        changes = (
            {'task_id': 'another-task'}, {'agent': 'unplanned-agent'}, {'evidence_ids': ()},
            {'status': 'INVENTED_STATUS'}, {'acceptance_basis': None},
        )
        for change in changes:
            state = self.accepted_state()
            state.results[0] = replace(state.results[0], **change)
            with self.subTest(change=change):
                self.assertEqual(self.core.final_status(state), AgentStatus.BLOCK)
        self.assertEqual(self.gate_calls, [])

    def test_final_status_revalidates_plan_and_duplicate_results(self):
        for mutation in ('remove-specialist', 'alter-purpose', 'duplicate-result'):
            state = self.accepted_state()
            if mutation == 'remove-specialist':
                state.planned.pop(0)
            elif mutation == 'alter-purpose':
                state.planned[0] = replace(state.planned[0], tz='Подменённое ТЗ')
            else:
                state.results.append(state.results[0])
            with self.subTest(mutation=mutation):
                self.assertEqual(self.core.final_status(state), AgentStatus.BLOCK)
        self.assertEqual(self.gate_calls, [])

    def test_collect_rejects_preexisting_invalid_state_atomically(self):
        state = self.core.plan(self.task)
        state.results.append(AgentResult('wrong', 'inspection-agent', AgentStatus.UNCERTAINTY))
        before = list(state.results)
        with self.assertRaises(ValueError):
            self.core.collect(state, [AgentResult(self.task.task_id, 'final-audit-agent', AgentStatus.BLOCK)])
        self.assertEqual(state.results, before)

    def test_material_identity_is_required_and_unique(self):
        for materials in ((MaterialRef('', 'report', 'r'),),
                          (MaterialRef('m', '', 'r'),),
                          (MaterialRef('m', 'report', ''),),
                          (MaterialRef('m', 'report', 'r'), MaterialRef('m', 'report', 'r2'))):
            with self.subTest(materials=materials), self.assertRaises(ValueError):
                self.core.plan(replace(self.task, materials=materials))

    def test_accepting_audit_cannot_precede_specialist_results(self):
        complete = self.accepted_state()
        state = self.core.plan(self.task)
        with self.assertRaises(ValueError):
            self.core.collect(state, reversed(complete.results))
        self.assertEqual(state.results, [])
        complete.results.reverse()
        self.assertEqual(self.core.final_status(complete), AgentStatus.BLOCK)
        self.assertEqual(self.gate_calls, [])

    def test_old_results_cannot_be_rebound_to_new_scope_or_materials(self):
        for changes in ({'tz': 'Проверить фундамент'},
                        {'materials': (MaterialRef('m2', 'report', 'foundation.pdf'),)}):
            state = self.accepted_state()
            state.task = replace(state.task, **changes)
            state.planned = self.core.plan(state.task).planned
            with self.subTest(changes=changes):
                self.assertEqual(self.core.final_status(state), AgentStatus.BLOCK)
                with self.assertRaises(ValueError):
                    self.core.collect(state, [])
        self.assertEqual(self.gate_calls, [])

    def test_valid_complete_state_still_requires_explicit_gate(self):
        state = self.accepted_state()
        self.assertEqual(self.core.final_status(state), AgentStatus.ACCEPTED)
        self.assertEqual(EngineerCore().final_status(state), AgentStatus.UNCERTAINTY)


class CodexContextIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.task = EngineerTask('context', 'Проверять кровлю, не обследовать фундамент',
                                 (MaterialRef('m1', 'report', 'r.pdf'),), ('inspection',))
        self.planned = EngineerCore().plan(self.task).planned

    def test_specialist_prompt_contains_controlling_tz_as_data(self):
        requests = []

        class Client(CodexAppServerClient):
            def start(self):
                pass

            def request(self, method, params=None):
                requests.append((method, params))
                return {'threadId': 'th'} if method == 'thread/start' else {'turnId': 'tu'}

            def _collect_turn(self, thread_id, turn_id):
                return json.dumps(dict(status='UNCERTAINTY', findings=[], evidence_ids=[], message=None)), {'status': 'completed'}

        class Skills:
            def load(self, skill):
                return 'TRUSTED SKILL'

        client = Client(skill_loader=Skills())
        client.execute_specialist(self.planned[0])
        prompt = requests[-1][1]['input'][0]['text']
        self.assertIn(self.task.tz, prompt)
        self.assertIn('UNTRUSTED TASK DATA', prompt)
        self.assertIn('\n', prompt)

    def test_runtime_error_is_in_following_audit_context(self):
        seen = []

        class Client:
            def execute_specialist(self, task, prior_results):
                seen.append(prior_results)
                if task.agent == 'inspection-agent':
                    raise TimeoutError('model unavailable')
                return AgentResult(task.task_id, task.agent, AgentStatus.UNCERTAINTY)

        state = EngineerCore().run(self.task, CodexRuntimeAdapter(Client()))
        self.assertEqual(len(seen[-1]), 1)
        self.assertEqual(seen[-1][0].status, AgentStatus.ERROR)
        self.assertEqual(EngineerCore().final_status(state), AgentStatus.ERROR)

    def test_invalid_runtime_result_becomes_visible_error_for_audit(self):
        seen = []

        class Client:
            def execute_specialist(self, task, prior_results):
                seen.append(prior_results)
                if task.agent == 'inspection-agent':
                    return AgentResult('foreign', task.agent, AgentStatus.PASS)
                return AgentResult(task.task_id, task.agent, AgentStatus.UNCERTAINTY)

        state = EngineerCore().run(self.task, CodexRuntimeAdapter(Client()))
        self.assertEqual(state.results[0].status, AgentStatus.ERROR)
        self.assertEqual(seen[-1][0].status, AgentStatus.ERROR)


if __name__ == '__main__':
    unittest.main()
