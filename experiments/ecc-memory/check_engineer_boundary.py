"""Synthetic experiment only. Does not install a backend or register evidence."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engineering.memory.external_memory import (
    ExternalMemoryAdapter, MemoryRecord, MemoryTrust, memory_context,
)
from engineering.core.contracts import AgentResult, AgentStatus
from engineering.core.engineer_core import EngineerCore


def check():
    checks = []
    for trust in MemoryTrust:
        record = MemoryRecord('synthetic-checkpoint',
                              'Synthetic handoff: original extraction status is BLOCK.',
                              'synthetic:checkpoint', trust)
        adapter = ExternalMemoryAdapter(lambda query: (record,))
        recalled = adapter.search('checkpoint')
        assert recalled == (record,)
        context = memory_context(recalled)
        assert context[0]['evidentiary_status'] == 'NOT_EVIDENCE'
        assert context[0]['source_ref'] == 'synthetic:checkpoint'
        checks.append({'name': f'{trust.value} memory stays non-evidentiary', 'passed': True})
    for status in (AgentStatus.PASS, AgentStatus.ACCEPTED):
        try:
            EngineerCore._validate_result_contract(AgentResult(
                task_id='synthetic', agent='inspection-agent', status=status,
                message='synthetic memory only', evidence_ids=()))
        except ValueError:
            checks.append({'name': f'{status.value} without evidence rejected', 'passed': True})
        else:
            raise AssertionError('Accepting result without evidence was allowed')
    return {'status': 'passed', 'checks': checks,
            'boundary': 'Synthetic metadata and result-contract checks only; no automatic ECC adapter, model prompt-injection test, persistence, production database or engineering acceptance.'}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
